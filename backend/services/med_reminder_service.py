from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from models.event import Event
from models.medication import Medication
from models.med_reminder import MedicationReminder


def _ensure_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def calculate_next_due(reminder: MedicationReminder, now: Optional[datetime] = None) -> Optional[datetime]:
    base = reminder.last_given_at or reminder.start_time
    if base is None:
        return None
    base = _ensure_utc(base)
    interval_hours = reminder.interval_hours or reminder.medication.interval_hours
    return base + timedelta(hours=interval_hours)


def get_medication_by_name(
    db: Session,
    med_name: str,
    recipient_id: Optional[str]
) -> Optional[Medication]:
    if not med_name:
        return None
    query = db.query(Medication).filter(Medication.name.ilike(med_name))
    if recipient_id:
        query = query.filter(
            (Medication.recipient_id == recipient_id) | (Medication.recipient_id.is_(None))
        )
    return query.order_by(Medication.recipient_id.desc()).first()


def record_medication_dose(
    db: Session,
    recipient_id: str,
    med_name: Optional[str],
    timestamp: Optional[datetime] = None,
    user_id: Optional[str] = None
) -> Optional[MedicationReminder]:
    if not med_name:
        return None
    medication = get_medication_by_name(db, med_name, recipient_id)
    if not medication:
        return None

    reminder = db.query(MedicationReminder).filter(
        MedicationReminder.recipient_id == recipient_id,
        MedicationReminder.medication_id == medication.id
    ).first()
    if not reminder:
        if not medication.auto_start_reminder or not user_id:
            return None
        reminder = MedicationReminder(
            recipient_id=recipient_id,
            medication_id=medication.id,
            start_time=timestamp or datetime.now(timezone.utc),
            interval_hours=None,
            enabled=True,
            created_by_user_id=user_id
        )
        db.add(reminder)

    reminder.last_given_at = timestamp or datetime.now(timezone.utc)
    reminder.enabled = True
    db.add(reminder)
    return reminder


def check_early_status(
    reminder: MedicationReminder,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    now = _ensure_utc(now or datetime.now(timezone.utc))
    next_due = calculate_next_due(reminder, now)
    if not next_due:
        return {"status": "unknown"}

    warning_minutes = reminder.medication.early_warning_minutes or 15
    warning_start = next_due - timedelta(minutes=warning_minutes)
    minutes_until_due = int((next_due - now).total_seconds() // 60)

    if now >= next_due:
        return {
            "status": "ok",
            "next_due": next_due,
            "minutes_until_due": minutes_until_due
        }

    if now >= warning_start:
        return {
            "status": "early",
            "next_due": next_due,
            "minutes_until_due": minutes_until_due,
            "warning_level": "within_window"
        }

    return {
        "status": "early",
        "next_due": next_due,
        "minutes_until_due": minutes_until_due,
        "warning_level": "too_early"
    }


def update_reminder_after_event_delete(
    db: Session,
    recipient_id: str,
    med_name: Optional[str],
    deleted_event_id: Optional[str] = None
) -> Optional[MedicationReminder]:
    if not med_name:
        return None

    medication = get_medication_by_name(db, med_name, recipient_id)
    if not medication:
        return None

    reminder = db.query(MedicationReminder).filter(
        MedicationReminder.recipient_id == recipient_id,
        MedicationReminder.medication_id == medication.id
    ).first()
    if not reminder:
        return None

    latest_event_query = db.query(Event).filter(
        Event.type == "medication",
        Event.recipient_id == recipient_id,
        Event.event_data["med_name"].astext == med_name
    )
    if deleted_event_id:
        latest_event_query = latest_event_query.filter(Event.id != deleted_event_id)

    latest_event = latest_event_query.order_by(Event.timestamp.desc()).first()

    if latest_event:
        reminder.last_given_at = latest_event.timestamp
        reminder.enabled = True
    else:
        reminder.last_given_at = None
        reminder.enabled = False

    db.add(reminder)
    return reminder
