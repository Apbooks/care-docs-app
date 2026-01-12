from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Event type: medication, feeding, diaper, demeanor, observation
    type = Column(String(50), nullable=False, index=True)

    # Timestamp when the event occurred
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # User who created the entry
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    # Care recipient this event is for
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("care_recipients.id"), nullable=True, index=True)
    recipient = relationship("CareRecipient")

    # General notes (optional)
    notes = Column(Text, nullable=True)

    # Type-specific data stored as JSON
    # Examples:
    # - Medication: {"med_name": "Aspirin", "dosage": "100mg", "route": "oral"}
    # - Feeding: {"amount_ml": 240, "duration_min": 20, "formula_type": "Standard"}
    # - Diaper: {"condition": "wet", "rash": false, "skin_notes": "Normal"}
    # - Demeanor: {"mood": "happy", "activity_level": "active", "concerns": ""}
    event_data = Column(JSONB, nullable=True, default={})

    # Sync tracking for offline support (Phase 4)
    synced = Column(Boolean, default=True, nullable=False)
    created_offline = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Event {self.type} at {self.timestamp} by {self.user_id}>"
