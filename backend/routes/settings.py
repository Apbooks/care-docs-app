from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json

from database import get_db
from models.app_setting import AppSetting
from models.user import User
from routes.auth import get_current_user, get_current_active_admin

router = APIRouter()

TIMEZONE_KEY = "timezone"
NOTIFICATIONS_KEY = "notifications"


class TimezoneResponse(BaseModel):
    timezone: str


class TimezoneUpdate(BaseModel):
    timezone: str = Field(..., min_length=1, max_length=100)


class NotificationSettings(BaseModel):
    enable_push: bool = False
    enable_in_app: bool = True
    due_soon_minutes: int = 0
    overdue_repeat_minutes: int = 60
    snooze_minutes_default: int = 15


class NotificationSettingsUpdate(BaseModel):
    enable_push: bool
    enable_in_app: bool
    due_soon_minutes: int = Field(..., ge=0, le=1440)
    overdue_repeat_minutes: int = Field(..., ge=0, le=1440)
    snooze_minutes_default: int = Field(..., ge=0, le=1440)


@router.get("/settings/timezone", response_model=TimezoneResponse)
async def get_timezone(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(AppSetting).filter(AppSetting.key == TIMEZONE_KEY).first()
    return TimezoneResponse(timezone=setting.value if setting else "local")


@router.put("/settings/timezone", response_model=TimezoneResponse)
async def update_timezone(
    payload: TimezoneUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    value = payload.timezone.strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timezone is required"
        )

    setting = db.query(AppSetting).filter(AppSetting.key == TIMEZONE_KEY).first()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=TIMEZONE_KEY, value=value)
        db.add(setting)

    db.commit()
    db.refresh(setting)

    return TimezoneResponse(timezone=setting.value)


def _get_notification_settings(setting: AppSetting) -> NotificationSettings:
    defaults = NotificationSettings()
    if not setting:
        return defaults
    try:
        payload = json.loads(setting.value)
        return NotificationSettings(**payload)
    except (json.JSONDecodeError, ValueError, TypeError):
        return defaults


@router.get("/settings/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(AppSetting).filter(AppSetting.key == NOTIFICATIONS_KEY).first()
    return _get_notification_settings(setting)


@router.put("/settings/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    payload: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    serialized = json.dumps(payload.model_dump())
    setting = db.query(AppSetting).filter(AppSetting.key == NOTIFICATIONS_KEY).first()
    if setting:
        setting.value = serialized
    else:
        setting = AppSetting(key=NOTIFICATIONS_KEY, value=serialized)
        db.add(setting)

    db.commit()
    db.refresh(setting)

    return _get_notification_settings(setting)
