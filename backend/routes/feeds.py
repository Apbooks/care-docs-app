import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

from database import get_db
from models.app_setting import AppSetting
from models.event import Event
from models.user import User
from models.care_recipient import CareRecipient
from routes.auth import get_current_user
from routes.stream import broadcast_event
from services.utils import to_utc_iso

router = APIRouter()

ACTIVE_FEED_KEY_PREFIX = "active_continuous_feed"


class ContinuousFeedStart(BaseModel):
    recipient_id: str = Field(..., min_length=1)
    rate_ml_hr: Optional[float] = Field(default=None, ge=0)
    dose_ml: Optional[float] = Field(default=None, ge=0)
    interval_hr: Optional[float] = Field(default=None, ge=0)
    formula_type: Optional[str] = Field(default=None, max_length=100)
    pump_model: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class ContinuousFeedStatus(BaseModel):
    active_feed: Optional[Dict[str, Any]]
    event: Optional[Dict[str, Any]]


class ContinuousFeedStop(BaseModel):
    recipient_id: str = Field(..., min_length=1)
    pump_total_ml: Optional[float] = Field(default=None, ge=0)


def event_to_response(event: Event, user_name: str, recipient_name: Optional[str]) -> Dict[str, Any]:
    return {
        "id": str(event.id),
        "type": event.type,
        "timestamp": to_utc_iso(event.timestamp),
        "user_id": str(event.user_id),
        "user_name": user_name,
        "recipient_id": str(event.recipient_id) if event.recipient_id else None,
        "recipient_name": recipient_name,
        "notes": event.notes,
        "metadata": event.event_data,
        "synced": event.synced,
        "created_offline": event.created_offline,
        "created_at": to_utc_iso(event.created_at),
        "updated_at": to_utc_iso(event.updated_at),
    }


def feed_setting_key(recipient_id: str) -> str:
    return f"{ACTIVE_FEED_KEY_PREFIX}:{recipient_id}"


def get_active_feed_setting(db: Session, recipient_id: str) -> Optional[Dict[str, Any]]:
    setting = db.query(AppSetting).filter(AppSetting.key == feed_setting_key(recipient_id)).first()
    if not setting:
        return None
    try:
        return json.loads(setting.value)
    except json.JSONDecodeError:
        return None


def set_active_feed_setting(db: Session, recipient_id: str, value: Optional[Dict[str, Any]]) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == feed_setting_key(recipient_id)).first()
    if value is None:
        if setting:
            db.delete(setting)
            db.commit()
        return
    payload = json.dumps(value)
    if setting:
        setting.value = payload
    else:
        setting = AppSetting(key=feed_setting_key(recipient_id), value=payload)
        db.add(setting)
    db.commit()


@router.get("/feeds/continuous/active", response_model=ContinuousFeedStatus)
async def get_active_continuous_feed(
    recipient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient not found or inactive"
        )

    return ContinuousFeedStatus(active_feed=get_active_feed_setting(db, recipient_id), event=None)


@router.post("/feeds/continuous/start", response_model=ContinuousFeedStatus, status_code=status.HTTP_201_CREATED)
async def start_continuous_feed(
    payload: ContinuousFeedStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == payload.recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient not found or inactive"
        )

    if get_active_feed_setting(db, payload.recipient_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A continuous feed is already running"
        )

    start_time = datetime.now(timezone.utc)
    feed_data = {
        "recipient_id": str(recipient.id),
        "started_at": to_utc_iso(start_time),
        "rate_ml_hr": payload.rate_ml_hr,
        "dose_ml": payload.dose_ml,
        "interval_hr": payload.interval_hr,
        "formula_type": payload.formula_type.strip() if payload.formula_type else None,
        "pump_model": payload.pump_model.strip() if payload.pump_model else None,
        "started_by_user_id": str(current_user.id),
        "started_by_name": current_user.username
    }

    new_event = Event(
        type="feeding",
        timestamp=start_time,
        user_id=current_user.id,
        recipient_id=recipient.id,
        notes=payload.notes,
        event_data={
            "mode": "continuous",
            "status": "started",
            **feed_data
        },
        synced=True,
        created_offline=False
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    set_active_feed_setting(db, payload.recipient_id, feed_data)

    await broadcast_event({"type": "feed.started", "recipient_id": str(recipient.id)})
    return ContinuousFeedStatus(
        active_feed=feed_data,
        event=event_to_response(new_event, current_user.username, recipient.name)
    )


@router.post("/feeds/continuous/stop", response_model=ContinuousFeedStatus)
async def stop_continuous_feed(
    payload: ContinuousFeedStop,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == payload.recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient not found or inactive"
        )

    active_feed = get_active_feed_setting(db, payload.recipient_id)
    if not active_feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active continuous feed found"
        )

    stop_time = datetime.now(timezone.utc)

    # Parse started_at with error handling for malformed dates
    try:
        started_at = datetime.fromisoformat(active_feed["started_at"].replace("Z", "+00:00"))
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid feed start time in active_feed: {e}")
        started_at = stop_time  # Fallback to 0 duration

    # Ensure both datetimes are UTC-aware for proper comparison
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    duration_ms = max(0, (stop_time - started_at).total_seconds() * 1000)
    duration_min_value = max(0, round(duration_ms / 60000))
    duration_hr = duration_ms / 3600000

    rate = active_feed.get("rate_ml_hr") or 0
    dose = active_feed.get("dose_ml")
    interval_hr = active_feed.get("interval_hr")
    amount = rate * duration_hr

    if interval_hr and dose and rate:
        active_time_hr = dose / rate
        cycles = int(duration_hr // interval_hr)
        remainder_hr = max(0, duration_hr - cycles * interval_hr)
        remainder_active_hr = min(remainder_hr, active_time_hr)
        remainder_amount = min(dose, rate * remainder_active_hr)
        amount = cycles * dose + remainder_amount
    elif dose:
        amount = min(amount, dose)

    new_event = Event(
        type="feeding",
        timestamp=stop_time,
        user_id=current_user.id,
        recipient_id=recipient.id,
        notes=None,
        event_data={
            "mode": "continuous",
            "status": "stopped",
            "rate_ml_hr": active_feed.get("rate_ml_hr"),
            "dose_ml": active_feed.get("dose_ml"),
            "interval_hr": active_feed.get("interval_hr"),
            "formula_type": active_feed.get("formula_type"),
            "pump_model": active_feed.get("pump_model"),
            "duration_min": duration_min_value,
            "amount_ml": round(amount),
            "pump_total_ml": payload.pump_total_ml
        },
        synced=True,
        created_offline=False
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    set_active_feed_setting(db, payload.recipient_id, None)

    await broadcast_event({"type": "feed.stopped", "recipient_id": str(recipient.id)})
    return ContinuousFeedStatus(
        active_feed=None,
        event=event_to_response(new_event, current_user.username, recipient.name)
    )
