from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.med_reminder import MedicationReminder
from models.medication import Medication
from models.user import User
from routes.auth import get_current_user, get_current_active_admin
from services.med_reminder_service import calculate_next_due, check_early_status, get_medication_by_name
from services.access_control import ensure_recipient_access, require_write_access

router = APIRouter()


class MedReminderCreate(BaseModel):
    recipient_id: str
    medication_id: str
    start_time: Optional[datetime] = None
    interval_hours: Optional[int] = None
    enabled: bool = True


class MedReminderUpdate(BaseModel):
    start_time: Optional[datetime] = None
    interval_hours: Optional[int] = None
    enabled: Optional[bool] = None


class MedReminderResponse(BaseModel):
    id: str
    recipient_id: str
    medication_id: str
    medication_name: str
    interval_hours: int
    early_warning_minutes: int
    start_time: Optional[str]
    last_given_at: Optional[str]
    last_skipped_at: Optional[str]
    enabled: bool
    next_due: Optional[str]

    class Config:
        from_attributes = True


class MedReminderNextResponse(BaseModel):
    id: str
    medication_id: str
    medication_name: str
    default_dose: Optional[str] = None
    dose_unit: Optional[str] = None
    recipient_id: str
    next_due: Optional[str]
    status: str
    minutes_until_due: Optional[int]
    enabled: bool


class MedEarlyCheckRequest(BaseModel):
    recipient_id: str
    med_name: str
    timestamp: Optional[datetime] = None


class MedEarlyCheckResponse(BaseModel):
    status: str
    next_due: Optional[str] = None
    minutes_until_due: Optional[int] = None
    warning_level: Optional[str] = None


def _to_response(reminder: MedicationReminder) -> MedReminderResponse:
    next_due = calculate_next_due(reminder)
    return MedReminderResponse(
        id=str(reminder.id),
        recipient_id=str(reminder.recipient_id),
        medication_id=str(reminder.medication_id),
        medication_name=reminder.medication.name,
        interval_hours=reminder.interval_hours or reminder.medication.interval_hours,
        early_warning_minutes=reminder.medication.early_warning_minutes,
        start_time=reminder.start_time.isoformat() if reminder.start_time else None,
        last_given_at=reminder.last_given_at.isoformat() if reminder.last_given_at else None,
        last_skipped_at=reminder.last_skipped_at.isoformat() if reminder.last_skipped_at else None,
        enabled=reminder.enabled,
        next_due=next_due.isoformat() if next_due else None
    )


def _ensure_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/", response_model=List[MedReminderResponse])
async def list_reminders(
    recipient_id: str = Query(...),
    include_disabled: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_recipient_access(db, current_user, recipient_id)
    query = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication))
    query = query.filter(MedicationReminder.recipient_id == recipient_id)
    if not include_disabled:
        query = query.filter(MedicationReminder.enabled.is_(True))
    reminders = query.order_by(MedicationReminder.created_at.desc()).all()
    return [_to_response(reminder) for reminder in reminders]


@router.post("/", response_model=MedReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    payload: MedReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    ensure_recipient_access(db, current_user, payload.recipient_id)
    existing = db.query(MedicationReminder).filter(
        MedicationReminder.recipient_id == payload.recipient_id,
        MedicationReminder.medication_id == payload.medication_id
    ).first()
    if existing:
        existing.start_time = _ensure_utc(payload.start_time) or existing.start_time
        if payload.interval_hours is not None:
            existing.interval_hours = payload.interval_hours
        existing.enabled = payload.enabled
        db.add(existing)
        db.commit()
        existing = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).get(existing.id)
        return _to_response(existing)

    med = db.query(Medication).filter(Medication.id == payload.medication_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    reminder = MedicationReminder(
        recipient_id=payload.recipient_id,
        medication_id=payload.medication_id,
        start_time=_ensure_utc(payload.start_time) or datetime.now(timezone.utc),
        interval_hours=payload.interval_hours,
        enabled=payload.enabled,
        created_by_user_id=current_user.id
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    reminder = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).get(reminder.id)
    return _to_response(reminder)


@router.patch("/{reminder_id}", response_model=MedReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    updates: MedReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    reminder = db.query(MedicationReminder).filter(MedicationReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    ensure_recipient_access(db, current_user, str(reminder.recipient_id))

    data = updates.model_dump(exclude_unset=True)
    if "start_time" in data:
        data["start_time"] = _ensure_utc(data["start_time"])
    for key, value in data.items():
        setattr(reminder, key, value)

    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    reminder = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).get(reminder.id)
    return _to_response(reminder)


@router.post("/{reminder_id}/skip", response_model=MedReminderResponse)
async def skip_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_write_access(current_user)
    reminder = db.query(MedicationReminder).filter(MedicationReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    ensure_recipient_access(db, current_user, str(reminder.recipient_id))
    reminder.enabled = False
    reminder.last_skipped_at = datetime.now(timezone.utc)
    db.add(reminder)
    db.commit()
    reminder = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).get(reminder.id)
    return _to_response(reminder)


@router.post("/{reminder_id}/log", response_model=MedReminderResponse)
async def log_dose(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_write_access(current_user)
    reminder = db.query(MedicationReminder).filter(MedicationReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    ensure_recipient_access(db, current_user, str(reminder.recipient_id))
    reminder.last_given_at = datetime.now(timezone.utc)
    reminder.enabled = True
    db.add(reminder)
    db.commit()
    reminder = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).get(reminder.id)
    return _to_response(reminder)


@router.get("/next", response_model=List[MedReminderNextResponse])
async def next_reminders(
    recipient_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_recipient_access(db, current_user, recipient_id)
    reminders = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).filter(
        MedicationReminder.recipient_id == recipient_id,
        MedicationReminder.enabled.is_(True)
    ).all()

    results: List[MedReminderNextResponse] = []
    now = datetime.now(timezone.utc)
    for reminder in reminders:
        next_due = calculate_next_due(reminder, now)
        if not next_due:
            continue
        minutes_until_due = int((next_due - now).total_seconds() // 60)
        status = "due" if minutes_until_due <= 0 else "upcoming"
        results.append(MedReminderNextResponse(
            id=str(reminder.id),
            medication_id=str(reminder.medication_id),
            medication_name=reminder.medication.name,
            default_dose=reminder.medication.default_dose,
            dose_unit=reminder.medication.dose_unit,
            recipient_id=str(reminder.recipient_id),
            next_due=next_due.isoformat(),
            status=status,
            minutes_until_due=minutes_until_due,
            enabled=reminder.enabled
        ))

    results.sort(key=lambda item: item.next_due or "")
    return results[:limit]


@router.post("/check-early", response_model=MedEarlyCheckResponse)
async def check_early(
    payload: MedEarlyCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ensure_recipient_access(db, current_user, payload.recipient_id)
    medication = get_medication_by_name(db, payload.med_name, payload.recipient_id)
    if not medication:
        return MedEarlyCheckResponse(status="unknown")

    reminder = db.query(MedicationReminder).options(joinedload(MedicationReminder.medication)).filter(
        MedicationReminder.recipient_id == payload.recipient_id,
        MedicationReminder.medication_id == medication.id
    ).first()
    if not reminder or not reminder.enabled or not reminder.last_given_at:
        return MedEarlyCheckResponse(status="unknown")

    status = check_early_status(reminder, _ensure_utc(payload.timestamp))
    return MedEarlyCheckResponse(
        status=status.get("status"),
        next_due=status.get("next_due").isoformat() if status.get("next_due") else None,
        minutes_until_due=status.get("minutes_until_due"),
        warning_level=status.get("warning_level")
    )
