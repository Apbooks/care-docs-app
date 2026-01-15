from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
from uuid import UUID

from database import get_db
from models.user import User
from models.app_setting import AppSetting
from models.event import Event
from models.care_recipient import CareRecipient
from routes.auth import get_current_user
from routes.stream import broadcast_event
from services.utils import to_utc_iso

router = APIRouter()
ACTIVE_FEED_KEY_PREFIX = "active_continuous_feed"


def feed_setting_key(recipient_id: str) -> str:
    return f"{ACTIVE_FEED_KEY_PREFIX}:{recipient_id}"


def update_active_feed_started_at(db: Session, recipient_id: str, started_at: datetime) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == feed_setting_key(recipient_id)).first()
    if not setting:
        return
    try:
        payload = setting.value
        data = payload if isinstance(payload, dict) else json.loads(payload)
    except Exception:
        return
    data["started_at"] = to_utc_iso(started_at)
    setting.value = json.dumps(data)
    db.commit()


# Pydantic models for request/response
class EventCreate(BaseModel):
    type: str = Field(..., description="Event type: medication, feeding, diaper, demeanor, observation")
    timestamp: Optional[datetime] = None  # Auto-set to now if not provided
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    recipient_id: Optional[str] = None


class EventUpdate(BaseModel):
    type: Optional[str] = None
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    recipient_id: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    type: str
    timestamp: str
    user_id: str
    user_name: str
    recipient_id: Optional[str]
    recipient_name: Optional[str]
    notes: Optional[str]
    metadata: Dict[str, Any]
    synced: bool
    created_offline: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def resolve_recipient(db: Session, recipient_id: Optional[str]) -> CareRecipient:
    if recipient_id:
        recipient = db.query(CareRecipient).filter(CareRecipient.id == recipient_id).first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        if not recipient.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient is inactive"
            )
        return recipient

    active_recipients = db.query(CareRecipient).filter(CareRecipient.is_active.is_(True)).all()
    if len(active_recipients) == 1:
        return active_recipients[0]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="recipient_id is required"
    )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new care event

    Supported event types:
    - medication: Track medication administration
    - feeding: Log feeding sessions
    - diaper: Record diaper changes
    - demeanor: Document mood and behavior
    - observation: General notes and observations
    """

    # Validate event type
    valid_types = ["medication", "feeding", "diaper", "demeanor", "observation"]
    if event_data.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type. Must be one of: {', '.join(valid_types)}"
        )

    # Create event
    recipient = resolve_recipient(db, event_data.recipient_id)

    new_event = Event(
        type=event_data.type,
        timestamp=event_data.timestamp or datetime.now(timezone.utc),
        user_id=current_user.id,
        recipient_id=recipient.id,
        notes=event_data.notes,
        event_data=event_data.metadata or {},
        synced=True,  # Created online, so already synced
        created_offline=False
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    await broadcast_event({"type": "event.created", "id": str(new_event.id), "recipient_id": str(recipient.id)})

    return EventResponse(
        id=str(new_event.id),
        type=new_event.type,
        timestamp=to_utc_iso(new_event.timestamp),
        user_id=str(new_event.user_id),
        user_name=current_user.username,
        recipient_id=str(recipient.id),
        recipient_name=recipient.name,
        notes=new_event.notes,
        metadata=new_event.event_data,
        synced=new_event.synced,
        created_offline=new_event.created_offline,
        created_at=to_utc_iso(new_event.created_at),
        updated_at=to_utc_iso(new_event.updated_at)
    )


@router.get("/", response_model=List[EventResponse])
async def get_events(
    type: Optional[str] = Query(None, description="Filter by event type"),
    start: Optional[datetime] = Query(None, description="Start datetime (inclusive)"),
    end: Optional[datetime] = Query(None, description="End datetime (inclusive)"),
    q: Optional[str] = Query(None, description="Search term"),
    recipient_id: Optional[str] = Query(None, description="Filter by care recipient"),
    limit: int = Query(50, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of care events

    Returns events ordered by timestamp (most recent first)
    """

    # Use joinedload to eagerly fetch related User and CareRecipient (fixes N+1 query)
    query = db.query(Event).options(
        joinedload(Event.user),
        joinedload(Event.recipient)
    )

    # Filter by type if specified
    if type:
        query = query.filter(Event.type == type)

    if start:
        query = query.filter(Event.timestamp >= start)
    if end:
        query = query.filter(Event.timestamp <= end)
    if recipient_id:
        query = query.filter(Event.recipient_id == recipient_id)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Event.notes.ilike(search),
                Event.event_data["med_name"].astext.ilike(search),
                Event.event_data["formula_type"].astext.ilike(search),
                Event.event_data["oral_notes"].astext.ilike(search),
            )
        )
    # Order by timestamp descending (most recent first)
    query = query.order_by(desc(Event.timestamp))

    # Apply pagination
    events = query.offset(offset).limit(limit).all()

    # Build response using eager-loaded relationships
    response = []
    for event in events:
        response.append(EventResponse(
            id=str(event.id),
            type=event.type,
            timestamp=to_utc_iso(event.timestamp),
            user_id=str(event.user_id),
            user_name=event.user.username if event.user else "Unknown",
            recipient_id=str(event.recipient.id) if event.recipient else None,
            recipient_name=event.recipient.name if event.recipient else None,
            notes=event.notes,
            metadata=event.event_data,
            synced=event.synced,
            created_offline=event.created_offline,
            created_at=to_utc_iso(event.created_at),
            updated_at=to_utc_iso(event.updated_at)
        ))

    return response


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific event by ID"""

    event = db.query(Event).options(
        joinedload(Event.user),
        joinedload(Event.recipient)
    ).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return EventResponse(
        id=str(event.id),
        type=event.type,
        timestamp=to_utc_iso(event.timestamp),
        user_id=str(event.user_id),
        user_name=event.user.username if event.user else "Unknown",
        recipient_id=str(event.recipient.id) if event.recipient else None,
        recipient_name=event.recipient.name if event.recipient else None,
        notes=event.notes,
        metadata=event.event_data,
        synced=event.synced,
        created_offline=event.created_offline,
        created_at=to_utc_iso(event.created_at),
        updated_at=to_utc_iso(event.updated_at)
    )


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an event (notes and metadata only)"""

    event = db.query(Event).options(
        joinedload(Event.user),
        joinedload(Event.recipient)
    ).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Update fields if provided
    if event_update.type is not None:
        valid_types = ["medication", "feeding", "diaper", "demeanor", "observation"]
        if event_update.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type. Must be one of: {', '.join(valid_types)}"
            )
        event.type = event_update.type

    if event_update.timestamp is not None:
        event.timestamp = event_update.timestamp

    if event_update.notes is not None:
        event.notes = event_update.notes

    if event_update.metadata is not None:
        event.event_data = event_update.metadata
    if event_update.recipient_id is not None:
        recipient = resolve_recipient(db, event_update.recipient_id)
        event.recipient_id = recipient.id

    event.updated_at = datetime.now(timezone.utc)

    if event.type == "feeding":
        metadata = event.event_data or {}
        if metadata.get("mode") == "continuous" and metadata.get("status") == "started" and event.recipient_id:
            update_active_feed_started_at(db, str(event.recipient_id), event.timestamp)

    db.commit()
    db.refresh(event)
    await broadcast_event({"type": "event.updated", "id": str(event.id), "recipient_id": str(event.recipient_id) if event.recipient_id else None})

    return EventResponse(
        id=str(event.id),
        type=event.type,
        timestamp=to_utc_iso(event.timestamp),
        user_id=str(event.user_id),
        user_name=event.user.username if event.user else "Unknown",
        recipient_id=str(event.recipient.id) if event.recipient else None,
        recipient_name=event.recipient.name if event.recipient else None,
        notes=event.notes,
        metadata=event.event_data,
        synced=event.synced,
        created_offline=event.created_offline,
        created_at=to_utc_iso(event.created_at),
        updated_at=to_utc_iso(event.updated_at)
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an event"""

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    db.delete(event)
    db.commit()
    await broadcast_event({"type": "event.deleted", "id": str(event.id), "recipient_id": str(event.recipient_id) if event.recipient_id else None})

    return None


@router.get("/stats/summary")
async def get_event_stats(
    recipient_id: Optional[str] = Query(None, description="Filter by care recipient"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics of events

    Returns count of each event type
    """

    stats = {}
    event_types = ["medication", "feeding", "diaper", "demeanor", "observation"]

    for event_type in event_types:
        count_query = db.query(Event).filter(Event.type == event_type)
        if recipient_id:
            count_query = count_query.filter(Event.recipient_id == recipient_id)
        count = count_query.count()
        stats[event_type] = count

    total_query = db.query(Event)
    if recipient_id:
        total_query = total_query.filter(Event.recipient_id == recipient_id)
    stats["total"] = total_query.count()

    return stats
