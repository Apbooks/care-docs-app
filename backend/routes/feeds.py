from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

from database import get_db
from models.app_setting import AppSetting
from models.event import Event
from models.user import User
from routes.auth import get_current_user
from routes.stream import broadcast_event

router = APIRouter()

ACTIVE_FEED_KEY = "active_continuous_feed"


class ContinuousFeedStart(BaseModel):
    rate_ml_hr: Optional[float] = Field(default=None, ge=0)
    dose_ml: Optional[float] = Field(default=None, ge=0)
    interval_hr: Optional[float] = Field(default=None, ge=0)
    formula_type: Optional[str] = Field(default=None, max_length=100)
    pump_model: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class ContinuousFeedStatus(BaseModel):
    active_feed: Optional[Dict[str, Any]]
    event: Optional[Dict[str, Any]]


def to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def event_to_response(event: Event, user_name: str) -> Dict[str, Any]:
    return {
        "id": str(event.id),
        "type": event.type,
        "timestamp": to_utc_iso(event.timestamp),
        "user_id": str(event.user_id),
        "user_name": user_name,
        "notes": event.notes,
        "metadata": event.event_data,
        "synced": event.synced,
        "created_offline": event.created_offline,
        "created_at": to_utc_iso(event.created_at),
        "updated_at": to_utc_iso(event.updated_at),
    }


def get_active_feed_setting(db: Session) -> Optional[Dict[str, Any]]:
    setting = db.query(AppSetting).filter(AppSetting.key == ACTIVE_FEED_KEY).first()
    if not setting:
        return None
    try:
        return json.loads(setting.value)
    except json.JSONDecodeError:
        return None


def set_active_feed_setting(db: Session, value: Optional[Dict[str, Any]]) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == ACTIVE_FEED_KEY).first()
    if value is None:
        if setting:
            db.delete(setting)
            db.commit()
        return
    payload = json.dumps(value)
    if setting:
        setting.value = payload
    else:
        setting = AppSetting(key=ACTIVE_FEED_KEY, value=payload)
        db.add(setting)
    db.commit()


@router.get("/feeds/continuous/active", response_model=ContinuousFeedStatus)
async def get_active_continuous_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ContinuousFeedStatus(active_feed=get_active_feed_setting(db), event=None)


@router.post("/feeds/continuous/start", response_model=ContinuousFeedStatus, status_code=status.HTTP_201_CREATED)
async def start_continuous_feed(
    payload: ContinuousFeedStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if get_active_feed_setting(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A continuous feed is already running"
        )

    start_time = datetime.utcnow()
    feed_data = {
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

    set_active_feed_setting(db, feed_data)

    await broadcast_event({"type": "feed.started"})
    return ContinuousFeedStatus(
        active_feed=feed_data,
        event=event_to_response(new_event, current_user.username)
    )


@router.post("/feeds/continuous/stop", response_model=ContinuousFeedStatus)
async def stop_continuous_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    active_feed = get_active_feed_setting(db)
    if not active_feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active continuous feed found"
        )

    stop_time = datetime.utcnow()
    started_at = datetime.fromisoformat(active_feed["started_at"].replace("Z", "+00:00"))
    duration_ms = max(0, (stop_time - started_at.replace(tzinfo=None)).total_seconds() * 1000)
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
            "amount_ml": round(amount)
        },
        synced=True,
        created_offline=False
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    set_active_feed_setting(db, None)

    await broadcast_event({"type": "feed.stopped"})
    return ContinuousFeedStatus(
        active_feed=None,
        event=event_to_response(new_event, current_user.username)
    )
