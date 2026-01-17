from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.medication import Medication
from models.user import User
from routes.auth import get_current_user, get_current_active_admin

router = APIRouter()


class MedicationCreate(BaseModel):
    name: str
    default_dose: Optional[str] = None
    dose_unit: Optional[str] = None
    interval_hours: int = 4
    early_warning_minutes: int = 15
    notes: Optional[str] = None
    is_prn: bool = False
    is_active: bool = True
    recipient_id: Optional[str] = None


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    default_dose: Optional[str] = None
    dose_unit: Optional[str] = None
    interval_hours: Optional[int] = None
    early_warning_minutes: Optional[int] = None
    notes: Optional[str] = None
    is_prn: Optional[bool] = None
    is_active: Optional[bool] = None
    recipient_id: Optional[str] = None


class MedicationResponse(BaseModel):
    id: str
    name: str
    default_dose: Optional[str]
    dose_unit: Optional[str]
    interval_hours: int
    early_warning_minutes: int
    notes: Optional[str]
    is_prn: bool
    is_active: bool
    recipient_id: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def _to_response(med: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=str(med.id),
        name=med.name,
        default_dose=med.default_dose,
        dose_unit=med.dose_unit,
        interval_hours=med.interval_hours,
        early_warning_minutes=med.early_warning_minutes,
        notes=med.notes,
        is_prn=med.is_prn,
        is_active=med.is_active,
        recipient_id=str(med.recipient_id) if med.recipient_id else None,
        created_at=med.created_at.isoformat(),
        updated_at=med.updated_at.isoformat()
    )


@router.get("/", response_model=List[MedicationResponse])
async def list_medications(
    recipient_id: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Medication)
    if not include_inactive:
        query = query.filter(Medication.is_active.is_(True))
    if recipient_id:
        query = query.filter(
            (Medication.recipient_id == recipient_id) | (Medication.recipient_id.is_(None))
        )
    meds = query.order_by(Medication.name.asc()).all()
    return [_to_response(med) for med in meds]


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    med = Medication(
        name=payload.name.strip(),
        default_dose=payload.default_dose,
        dose_unit=payload.dose_unit,
        interval_hours=payload.interval_hours,
        early_warning_minutes=payload.early_warning_minutes,
        notes=payload.notes,
        is_prn=payload.is_prn,
        is_active=payload.is_active,
        recipient_id=payload.recipient_id,
        created_by_user_id=current_user.id
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return _to_response(med)


@router.patch("/{med_id}", response_model=MedicationResponse)
async def update_medication(
    med_id: UUID,
    updates: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    med = db.query(Medication).filter(Medication.id == med_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(med, key, value)

    db.add(med)
    db.commit()
    db.refresh(med)
    return _to_response(med)


@router.delete("/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    med_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    med = db.query(Medication).filter(Medication.id == med_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    db.delete(med)
    db.commit()
    return None
