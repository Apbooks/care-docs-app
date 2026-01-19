import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import joinedload

from config import get_settings
from database import SessionLocal
from models.app_setting import AppSetting
from models.med_reminder import MedicationReminder
from models.push_subscription import PushSubscription
from models.user import User
from services.med_reminder_service import calculate_next_due
from services.notification_service import send_push_notifications
from services import pubsub

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.SCHEDULER_ENABLED:
        logger.info("Reminder scheduler disabled by configuration")
        return

    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler(timezone=timezone.utc)
    _scheduler.add_job(
        _run_due_scan,
        IntervalTrigger(seconds=settings.REMINDER_SCAN_INTERVAL_SECONDS),
        id="reminder_due_scan",
        max_instances=1,
        coalesce=True
    )
    _scheduler.start()
    logger.info("Reminder scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Reminder scheduler stopped")


async def _run_due_scan() -> None:
    """Scan reminders and broadcast due notifications."""
    try:
        await _scan_due_reminders()
    except Exception as exc:
        logger.exception("Reminder scan failed: %s", exc)


async def _scan_due_reminders() -> None:
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    due_payloads: List[Dict[str, Any]] = []
    notify_config = _get_notification_config(db)
    try:
        reminders = db.query(MedicationReminder).options(
            joinedload(MedicationReminder.medication)
        ).filter(
            MedicationReminder.enabled.is_(True)
        ).all()

        for reminder in reminders:
            next_due = calculate_next_due(reminder, now)
            if not next_due or now < next_due:
                continue
            if _should_skip_due_notification(reminder, next_due, now, notify_config):
                continue

            reminder.last_notified_at = now
            payload = {
                "type": "med_reminder_due",
                "reminder_id": str(reminder.id),
                "recipient_id": str(reminder.recipient_id),
                "medication_id": str(reminder.medication_id),
                "medication_name": reminder.medication.name,
                "next_due": next_due.isoformat(),
                "title": "Medication due",
                "body": f"Time to give {reminder.medication.name}.",
                "url": "/"
            }
            due_payloads.append(payload)

        if due_payloads:
            db.commit()

    finally:
        db.close()

    if not due_payloads:
        return

    if notify_config["enable_in_app"]:
        for payload in due_payloads:
            await pubsub.publish(payload)

    if notify_config["enable_push"]:
        await asyncio.to_thread(_send_push_for_due, due_payloads)


def _send_push_for_due(due_payloads: List[Dict[str, Any]]) -> None:
    db = SessionLocal()
    try:
        subscriptions = db.query(PushSubscription).join(User).filter(
            User.is_active.is_(True)
        ).all()
        if not subscriptions:
            return

        subscription_payloads = [
            {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            for sub in subscriptions
        ]

        for payload in due_payloads:
            send_push_notifications(subscription_payloads, payload)
    finally:
        db.close()


def _get_notification_config(db) -> Dict[str, Any]:
    setting = db.query(AppSetting).filter(AppSetting.key == "notifications").first()
    defaults = {
        "enable_push": False,
        "enable_in_app": True,
        "overdue_repeat_minutes": 60
    }
    if not setting:
        return defaults
    try:
        payload = json.loads(setting.value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return defaults
    return {
        "enable_push": bool(payload.get("enable_push", defaults["enable_push"])),
        "enable_in_app": bool(payload.get("enable_in_app", defaults["enable_in_app"])),
        "overdue_repeat_minutes": int(payload.get("overdue_repeat_minutes", defaults["overdue_repeat_minutes"]))
    }


def _should_skip_due_notification(
    reminder: MedicationReminder,
    next_due: datetime,
    now: datetime,
    notify_config: Dict[str, Any]
) -> bool:
    if reminder.last_notified_at is None:
        return False
    if reminder.last_notified_at < next_due:
        return False
    repeat_minutes = notify_config.get("overdue_repeat_minutes", 60)
    if repeat_minutes <= 0:
        return True
    return now - reminder.last_notified_at < timedelta(minutes=repeat_minutes)
