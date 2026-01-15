from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from models.care_recipient import CareRecipient
from models.user import User
from routes.auth import get_current_user, get_current_active_admin

router = APIRouter()


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class RecipientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class RecipientResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    created_by_user_id: str
    created_by_name: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/recipients", response_model=List[RecipientResponse])
async def list_recipients(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if include_inactive and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view inactive recipients"
        )

    query = db.query(CareRecipient)
    if not include_inactive:
        query = query.filter(CareRecipient.is_active.is_(True))

    recipients = query.order_by(CareRecipient.created_at.asc()).all()

    return [
        RecipientResponse(
            id=str(recipient.id),
            name=recipient.name,
            is_active=recipient.is_active,
            created_by_user_id=str(recipient.created_by_user_id),
            created_by_name=recipient.created_by.username if recipient.created_by else None,
            created_at=recipient.created_at.isoformat(),
            updated_at=recipient.updated_at.isoformat()
        )
        for recipient in recipients
    ]


@router.post("/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def create_recipient(
    data: RecipientCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    new_recipient = CareRecipient(
        name=data.name.strip(),
        is_active=data.is_active,
        created_by_user_id=current_admin.id
    )

    db.add(new_recipient)
    db.commit()
    db.refresh(new_recipient)

    return RecipientResponse(
        id=str(new_recipient.id),
        name=new_recipient.name,
        is_active=new_recipient.is_active,
        created_by_user_id=str(new_recipient.created_by_user_id),
        created_by_name=current_admin.username,
        created_at=new_recipient.created_at.isoformat(),
        updated_at=new_recipient.updated_at.isoformat()
    )


@router.patch("/recipients/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    recipient_id: str,
    updates: RecipientUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    if updates.name is not None:
        recipient.name = updates.name.strip()
    if updates.is_active is not None:
        recipient.is_active = updates.is_active

    recipient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(recipient)

    return RecipientResponse(
        id=str(recipient.id),
        name=recipient.name,
        is_active=recipient.is_active,
        created_by_user_id=str(recipient.created_by_user_id),
        created_by_name=recipient.created_by.username if recipient.created_by else None,
        created_at=recipient.created_at.isoformat(),
        updated_at=recipient.updated_at.isoformat()
    )


@router.delete("/recipients/{recipient_id}")
async def delete_recipient(
    recipient_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    db.delete(recipient)
    db.commit()

    return {"message": "Recipient deleted successfully"}
