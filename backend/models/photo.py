from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Link to the event this photo belongs to
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    event = relationship("Event", backref="photos")

    # File information
    filename = Column(String(255), nullable=False, unique=True)  # Generated unique filename
    original_filename = Column(String(255), nullable=True)  # User's original filename
    thumbnail_filename = Column(String(255), nullable=True)  # Thumbnail version

    # File metadata
    size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Additional metadata (dimensions, device info, etc.)
    # GPS data should be stripped for privacy
    # Use a non-reserved attribute name; keep DB column name as "metadata".
    photo_metadata = Column("metadata", JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Photo {self.filename} for event {self.event_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "filename": self.filename,
            "original_filename": self.original_filename,
            "thumbnail_filename": self.thumbnail_filename,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "metadata": self.photo_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
