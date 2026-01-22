from datetime import datetime, timedelta, timezone
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.care_recipient import CareRecipient
from models.user import User
from models.user_invite import UserInvite
from models.user_recipient_access import UserRecipientAccess
from routes.auth import get_current_active_admin
from services.auth_service import get_password_hash, normalize_username, validate_password_strength

router = APIRouter()


class InviteCreate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=2, max_length=50)
    invitee_name: Optional[str] = Field(default=None, max_length=120)
    role: str = "caregiver"
    recipient_ids: List[str] = Field(default_factory=list)
    expires_in_hours: int = Field(48, ge=1, le=720)


class InviteResponse(BaseModel):
    token: str
    email: Optional[str]
    username: Optional[str]
    invitee_name: Optional[str]
    role: str
    recipient_ids: List[str]
    expires_at: str
    invite_url: str


class InviteInfoResponse(BaseModel):
    email: Optional[str]
    username: Optional[str]
    invitee_name: Optional[str]
    role: str
    recipient_ids: List[str]
    recipient_names: List[str]
    expires_at: str
    created_at: str


class InviteAcceptRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    display_name: Optional[str] = Field(default=None, max_length=100)
    password: str


class InviteSummaryResponse(BaseModel):
    token: str
    invitee_name: Optional[str]
    role: str
    recipient_ids: List[str]
    recipient_names: List[str]
    expires_at: str
    created_at: str
    invite_url: str


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_role(role: str) -> None:
    if role not in ["admin", "caregiver", "read_only"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin', 'caregiver', or 'read_only'"
        )


def _load_recipients(db: Session, recipient_ids: List[str]) -> List[CareRecipient]:
    if not recipient_ids:
        return []
    recipients = db.query(CareRecipient).filter(CareRecipient.id.in_(recipient_ids)).all()
    if len(recipients) != len(set(recipient_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more recipients are invalid"
        )
    return recipients


@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    normalized_username = normalize_username(payload.username) if payload.username else None
    _validate_role(payload.role)
    recipients = _load_recipients(db, payload.recipient_ids)

    if normalized_username:
        existing_user = db.query(User).filter(
            func.lower(User.username) == normalized_username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        existing_invite = db.query(UserInvite).filter(
            func.lower(UserInvite.username) == normalized_username,
            UserInvite.used_at.is_(None)
        ).first()
        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active invite already exists for this username"
            )

    if payload.email:
        existing_email = db.query(User).filter(
            func.lower(User.email) == payload.email.lower()
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

    invite = UserInvite(
        token=token,
        email=payload.email,
        username=normalized_username,
        invitee_name=(payload.invitee_name or "").strip() or None,
        role=payload.role,
        recipient_ids=[str(rec.id) for rec in recipients],
        expires_at=expires_at,
        created_by_user_id=current_admin.id
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    origin = request.headers.get("origin")
    base_url = origin.rstrip("/") if origin else str(request.base_url).rstrip("/")
    invite_url = f"{base_url}/invite/{invite.token}"

    return InviteResponse(
        token=invite.token,
        email=invite.email,
        username=invite.username,
        invitee_name=invite.invitee_name,
        role=invite.role,
        recipient_ids=invite.recipient_ids or [],
        expires_at=invite.expires_at.isoformat(),
        invite_url=invite_url
    )


@router.get("/{token}", response_model=InviteInfoResponse)
async def get_invite(token: str, db: Session = Depends(get_db)):
    invite = db.query(UserInvite).filter(UserInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    expires_at = _ensure_utc(invite.expires_at)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")

    recipients = _load_recipients(db, invite.recipient_ids or [])
    recipient_names = [recipient.name for recipient in recipients]

    return InviteInfoResponse(
        email=invite.email,
        username=invite.username,
        invitee_name=invite.invitee_name,
        role=invite.role,
        recipient_ids=invite.recipient_ids or [],
        recipient_names=recipient_names,
        expires_at=expires_at.isoformat(),
        created_at=invite.created_at.isoformat()
    )


@router.post("/{token}/accept", status_code=status.HTTP_201_CREATED)
async def accept_invite(
    token: str,
    payload: InviteAcceptRequest,
    db: Session = Depends(get_db)
):
    invite = db.query(UserInvite).filter(UserInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    expires_at = _ensure_utc(invite.expires_at)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")

    password_errors = validate_password_strength(payload.password)
    if password_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=" ".join(password_errors)
        )

    normalized_username = normalize_username(payload.username)
    if not normalized_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )
    if invite.username and invite.username != normalized_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username does not match invite"
        )
    if invite.email and invite.email.lower() != payload.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match invite"
        )

    existing_user = db.query(User).filter(
        func.lower(User.username) == normalized_username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = db.query(User).filter(
        func.lower(User.email) == payload.email.lower()
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        username=normalized_username,
        email=payload.email,
        display_name=(payload.display_name or "").strip() or None,
        password_hash=get_password_hash(payload.password),
        role=invite.role,
        is_active=True
    )
    db.add(user)
    db.flush()

    recipient_ids = invite.recipient_ids or []
    for recipient_id in recipient_ids:
        db.add(UserRecipientAccess(user_id=user.id, recipient_id=recipient_id))

    invite.used_at = datetime.now(timezone.utc)
    db.add(invite)
    db.commit()

    return {"status": "accepted"}


@router.get("/", response_model=List[InviteSummaryResponse])
async def list_invites(
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    now = datetime.now(timezone.utc)
    invites = db.query(UserInvite).filter(
        UserInvite.used_at.is_(None),
        UserInvite.expires_at > now
    ).order_by(UserInvite.created_at.desc()).all()

    results = []
    for invite in invites:
        recipients = _load_recipients(db, invite.recipient_ids or [])
        recipient_names = [recipient.name for recipient in recipients]
        expires_at = _ensure_utc(invite.expires_at)
        origin = request.headers.get("origin")
        base_url = origin.rstrip("/") if origin else str(request.base_url).rstrip("/")
        invite_url = f"{base_url}/invite/{invite.token}"
        results.append(InviteSummaryResponse(
            token=invite.token,
            invitee_name=invite.invitee_name,
            role=invite.role,
            recipient_ids=invite.recipient_ids or [],
            recipient_names=recipient_names,
            expires_at=expires_at.isoformat(),
            created_at=invite.created_at.isoformat(),
            invite_url=invite_url
        ))
    return results


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    token: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    invite = db.query(UserInvite).filter(UserInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    db.delete(invite)
    db.commit()
    return None
