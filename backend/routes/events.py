from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from database import get_db
from models.user import User
from models.event import Event
from routes.auth import get_current_user

router = APIRouter()


def to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


# Pydantic models for request/response
class EventCreate(BaseModel):
    type: str = Field(..., description="Event type: medication, feeding, diaper, demeanor, observation")
    timestamp: Optional[datetime] = None  # Auto-set to now if not provided
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventUpdate(BaseModel):
    type: Optional[str] = None
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    id: str
    type: str
    timestamp: str
    user_id: str
    user_name: str
    notes: Optional[str]
    metadata: Dict[str, Any]
    synced: bool
    created_offline: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


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
    new_event = Event(
        type=event_data.type,
        timestamp=event_data.timestamp or datetime.utcnow(),
        user_id=current_user.id,
        notes=event_data.notes,
        event_data=event_data.metadata or {},
        synced=True,  # Created online, so already synced
        created_offline=False
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return EventResponse(
        id=str(new_event.id),
        type=new_event.type,
        timestamp=to_utc_iso(new_event.timestamp),
        user_id=str(new_event.user_id),
        user_name=current_user.username,
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
    limit: int = Query(50, ge=1, le=200, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of care events

    Returns events ordered by timestamp (most recent first)
    """

    query = db.query(Event)

    # Filter by type if specified
    if type:
        query = query.filter(Event.type == type)

    # Order by timestamp descending (most recent first)
    query = query.order_by(desc(Event.timestamp))

    # Apply pagination
    events = query.offset(offset).limit(limit).all()

    # Build response with user names
    response = []
    for event in events:
        user = db.query(User).filter(User.id == event.user_id).first()
        response.append(EventResponse(
            id=str(event.id),
            type=event.type,
            timestamp=to_utc_iso(event.timestamp),
            user_id=str(event.user_id),
            user_name=user.username if user else "Unknown",
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

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    user = db.query(User).filter(User.id == event.user_id).first()

    return EventResponse(
        id=str(event.id),
        type=event.type,
        timestamp=to_utc_iso(event.timestamp),
        user_id=str(event.user_id),
        user_name=user.username if user else "Unknown",
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

    event = db.query(Event).filter(Event.id == event_id).first()

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

    event.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(event)

    user = db.query(User).filter(User.id == event.user_id).first()

    return EventResponse(
        id=str(event.id),
        type=event.type,
        timestamp=to_utc_iso(event.timestamp),
        user_id=str(event.user_id),
        user_name=user.username if user else "Unknown",
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

    return None


@router.get("/stats/summary")
async def get_event_stats(
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
        count = db.query(Event).filter(Event.type == event_type).count()
        stats[event_type] = count

    stats["total"] = db.query(Event).count()

    return stats
