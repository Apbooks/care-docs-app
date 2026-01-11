from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.app_setting import AppSetting
from models.user import User
from routes.auth import get_current_user, get_current_active_admin

router = APIRouter()

TIMEZONE_KEY = "timezone"


class TimezoneResponse(BaseModel):
    timezone: str


class TimezoneUpdate(BaseModel):
    timezone: str = Field(..., min_length=1, max_length=100)


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
