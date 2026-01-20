from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from models.quick_medication import QuickMedication
from models.quick_feed import QuickFeed
from models.care_recipient import CareRecipient
from models.user import User
from routes.auth import get_current_user, get_current_active_admin
from services.access_control import get_allowed_recipient_ids

router = APIRouter()
VALID_FEED_MODES = ["continuous", "bolus", "oral"]


# ============================================================================
# QUICK MEDICATIONS
# ============================================================================

class QuickMedicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=100)
    route: str = Field(default="oral", max_length=50)
    is_active: bool = True
    recipient_id: str = Field(..., min_length=1)


class QuickMedicationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    dosage: Optional[str] = Field(default=None, max_length=100)
    route: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    recipient_id: Optional[str] = None


class QuickMedicationResponse(BaseModel):
    id: str
    name: str
    dosage: str
    route: str
    is_active: bool
    recipient_id: Optional[str]
    created_by_user_id: str
    created_by_name: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/quick-meds", response_model=List[QuickMedicationResponse])
async def list_quick_medications(
    include_inactive: bool = Query(False),
    recipient_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if include_inactive and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view inactive templates"
        )

    allowed = get_allowed_recipient_ids(db, current_user)
    if allowed is not None:
        if recipient_id and recipient_id not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this recipient"
            )
        if not allowed:
            return []

    query = db.query(QuickMedication)
    if not include_inactive:
        query = query.filter(QuickMedication.is_active.is_(True))
    if recipient_id:
        query = query.filter(QuickMedication.recipient_id == recipient_id)
    elif allowed is not None:
        query = query.filter(QuickMedication.recipient_id.in_(allowed))

    meds = query.order_by(QuickMedication.created_at.desc()).all()

    return [
        QuickMedicationResponse(
            id=str(med.id),
            name=med.name,
            dosage=med.dosage,
            route=med.route,
            is_active=med.is_active,
            recipient_id=str(med.recipient_id) if med.recipient_id else None,
            created_by_user_id=str(med.created_by_user_id),
            created_by_name=med.created_by.username if med.created_by else None,
            created_at=med.created_at.isoformat(),
            updated_at=med.updated_at.isoformat()
        )
        for med in meds
    ]


@router.post("/quick-meds", response_model=QuickMedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_medication(
    data: QuickMedicationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == data.recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient not found or inactive"
        )

    new_med = QuickMedication(
        name=data.name.strip(),
        dosage=data.dosage.strip(),
        route=data.route.strip().lower(),
        is_active=data.is_active,
        recipient_id=recipient.id,
        created_by_user_id=current_admin.id
    )

    db.add(new_med)
    db.commit()
    db.refresh(new_med)

    return QuickMedicationResponse(
        id=str(new_med.id),
        name=new_med.name,
        dosage=new_med.dosage,
        route=new_med.route,
        is_active=new_med.is_active,
        recipient_id=str(new_med.recipient_id) if new_med.recipient_id else None,
        created_by_user_id=str(new_med.created_by_user_id),
        created_by_name=current_admin.username,
        created_at=new_med.created_at.isoformat(),
        updated_at=new_med.updated_at.isoformat()
    )


@router.patch("/quick-meds/{med_id}", response_model=QuickMedicationResponse)
async def update_quick_medication(
    med_id: str,
    updates: QuickMedicationUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    med = db.query(QuickMedication).filter(QuickMedication.id == med_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick medication not found"
        )

    if updates.name is not None:
        med.name = updates.name.strip()
    if updates.dosage is not None:
        med.dosage = updates.dosage.strip()
    if updates.route is not None:
        med.route = updates.route.strip().lower()
    if updates.is_active is not None:
        med.is_active = updates.is_active
    if updates.recipient_id is not None:
        recipient = db.query(CareRecipient).filter(CareRecipient.id == updates.recipient_id).first()
        if not recipient or not recipient.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient not found or inactive"
            )
        med.recipient_id = recipient.id

    med.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(med)

    return QuickMedicationResponse(
        id=str(med.id),
        name=med.name,
        dosage=med.dosage,
        route=med.route,
        is_active=med.is_active,
        recipient_id=str(med.recipient_id) if med.recipient_id else None,
        created_by_user_id=str(med.created_by_user_id),
        created_by_name=med.created_by.username if med.created_by else None,
        created_at=med.created_at.isoformat(),
        updated_at=med.updated_at.isoformat()
    )


@router.delete("/quick-meds/{med_id}")
async def delete_quick_medication(
    med_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    med = db.query(QuickMedication).filter(QuickMedication.id == med_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick medication not found"
        )

    db.delete(med)
    db.commit()

    return {"message": "Quick medication deleted successfully"}


# ============================================================================
# QUICK FEEDS
# ============================================================================

class QuickFeedCreate(BaseModel):
    mode: str = Field(default="bolus", max_length=20)
    amount_ml: Optional[int] = Field(default=None, ge=0)
    duration_min: Optional[int] = Field(default=None, ge=0)
    formula_type: Optional[str] = Field(default=None, max_length=100)
    rate_ml_hr: Optional[float] = Field(default=None, ge=0)
    dose_ml: Optional[float] = Field(default=None, ge=0)
    interval_hr: Optional[float] = Field(default=None, ge=0)
    oral_notes: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = True
    recipient_id: str = Field(..., min_length=1)


class QuickFeedUpdate(BaseModel):
    mode: Optional[str] = Field(default=None, max_length=20)
    amount_ml: Optional[int] = Field(default=None, ge=0)
    duration_min: Optional[int] = Field(default=None, ge=0)
    formula_type: Optional[str] = Field(default=None, max_length=100)
    rate_ml_hr: Optional[float] = Field(default=None, ge=0)
    dose_ml: Optional[float] = Field(default=None, ge=0)
    interval_hr: Optional[float] = Field(default=None, ge=0)
    oral_notes: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = None
    recipient_id: Optional[str] = None


class QuickFeedResponse(BaseModel):
    id: str
    mode: str
    amount_ml: Optional[int]
    duration_min: Optional[int]
    formula_type: Optional[str]
    rate_ml_hr: Optional[float]
    dose_ml: Optional[float]
    interval_hr: Optional[float]
    oral_notes: Optional[str]
    is_active: bool
    recipient_id: Optional[str]
    created_by_user_id: str
    created_by_name: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/quick-feeds", response_model=List[QuickFeedResponse])
async def list_quick_feeds(
    include_inactive: bool = Query(False),
    recipient_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if include_inactive and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view inactive templates"
        )

    allowed = get_allowed_recipient_ids(db, current_user)
    if allowed is not None:
        if recipient_id and recipient_id not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this recipient"
            )
        if not allowed:
            return []

    query = db.query(QuickFeed)
    if not include_inactive:
        query = query.filter(QuickFeed.is_active.is_(True))
    if recipient_id:
        query = query.filter(QuickFeed.recipient_id == recipient_id)
    elif allowed is not None:
        query = query.filter(QuickFeed.recipient_id.in_(allowed))

    feeds = query.order_by(QuickFeed.created_at.desc()).all()

    return [
        QuickFeedResponse(
            id=str(feed.id),
            mode=feed.mode,
            amount_ml=feed.amount_ml,
            duration_min=feed.duration_min,
            formula_type=feed.formula_type,
            rate_ml_hr=feed.rate_ml_hr,
            dose_ml=feed.dose_ml,
            interval_hr=feed.interval_hr,
            oral_notes=feed.oral_notes,
            is_active=feed.is_active,
            recipient_id=str(feed.recipient_id) if feed.recipient_id else None,
            created_by_user_id=str(feed.created_by_user_id),
            created_by_name=feed.created_by.username if feed.created_by else None,
            created_at=feed.created_at.isoformat(),
            updated_at=feed.updated_at.isoformat()
        )
        for feed in feeds
    ]


@router.post("/quick-feeds", response_model=QuickFeedResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_feed(
    data: QuickFeedCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    if data.mode.strip().lower() not in VALID_FEED_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feed mode. Must be one of: {', '.join(VALID_FEED_MODES)}"
        )
    recipient = db.query(CareRecipient).filter(CareRecipient.id == data.recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient not found or inactive"
        )
    new_feed = QuickFeed(
        mode=data.mode.strip().lower(),
        amount_ml=data.amount_ml,
        duration_min=data.duration_min,
        formula_type=data.formula_type.strip() if data.formula_type else None,
        rate_ml_hr=data.rate_ml_hr,
        dose_ml=data.dose_ml,
        interval_hr=data.interval_hr,
        oral_notes=data.oral_notes.strip() if data.oral_notes else None,
        is_active=data.is_active,
        recipient_id=recipient.id,
        created_by_user_id=current_admin.id
    )

    db.add(new_feed)
    db.commit()
    db.refresh(new_feed)

    return QuickFeedResponse(
        id=str(new_feed.id),
        mode=new_feed.mode,
        amount_ml=new_feed.amount_ml,
        duration_min=new_feed.duration_min,
        formula_type=new_feed.formula_type,
        rate_ml_hr=new_feed.rate_ml_hr,
        dose_ml=new_feed.dose_ml,
        interval_hr=new_feed.interval_hr,
        oral_notes=new_feed.oral_notes,
        is_active=new_feed.is_active,
        recipient_id=str(new_feed.recipient_id) if new_feed.recipient_id else None,
        created_by_user_id=str(new_feed.created_by_user_id),
        created_by_name=current_admin.username,
        created_at=new_feed.created_at.isoformat(),
        updated_at=new_feed.updated_at.isoformat()
    )


@router.patch("/quick-feeds/{feed_id}", response_model=QuickFeedResponse)
async def update_quick_feed(
    feed_id: str,
    updates: QuickFeedUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    feed = db.query(QuickFeed).filter(QuickFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick feed not found"
        )

    if updates.amount_ml is not None:
        feed.amount_ml = updates.amount_ml
    if updates.duration_min is not None:
        feed.duration_min = updates.duration_min
    if updates.formula_type is not None:
        feed.formula_type = updates.formula_type.strip() if updates.formula_type else None
    if updates.mode is not None:
        mode_value = updates.mode.strip().lower()
        if mode_value not in VALID_FEED_MODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feed mode. Must be one of: {', '.join(VALID_FEED_MODES)}"
            )
        feed.mode = mode_value
    if updates.rate_ml_hr is not None:
        feed.rate_ml_hr = updates.rate_ml_hr
    if updates.dose_ml is not None:
        feed.dose_ml = updates.dose_ml
    if updates.interval_hr is not None:
        feed.interval_hr = updates.interval_hr
    if updates.oral_notes is not None:
        feed.oral_notes = updates.oral_notes.strip() if updates.oral_notes else None
    if updates.is_active is not None:
        feed.is_active = updates.is_active
    if updates.recipient_id is not None:
        recipient = db.query(CareRecipient).filter(CareRecipient.id == updates.recipient_id).first()
        if not recipient or not recipient.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient not found or inactive"
            )
        feed.recipient_id = recipient.id

    feed.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(feed)

    return QuickFeedResponse(
        id=str(feed.id),
        mode=feed.mode,
        amount_ml=feed.amount_ml,
        duration_min=feed.duration_min,
        formula_type=feed.formula_type,
        rate_ml_hr=feed.rate_ml_hr,
        dose_ml=feed.dose_ml,
        interval_hr=feed.interval_hr,
        oral_notes=feed.oral_notes,
        is_active=feed.is_active,
        recipient_id=str(feed.recipient_id) if feed.recipient_id else None,
        created_by_user_id=str(feed.created_by_user_id),
        created_by_name=feed.created_by.username if feed.created_by else None,
        created_at=feed.created_at.isoformat(),
        updated_at=feed.updated_at.isoformat()
    )


@router.delete("/quick-feeds/{feed_id}")
async def delete_quick_feed(
    feed_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    feed = db.query(QuickFeed).filter(QuickFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick feed not found"
        )

    db.delete(feed)
    db.commit()

    return {"message": "Quick feed deleted successfully"}
