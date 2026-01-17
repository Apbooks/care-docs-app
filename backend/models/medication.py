from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(120), nullable=False, index=True)
    default_dose = Column(String(80), nullable=True)
    dose_unit = Column(String(40), nullable=True)
    interval_hours = Column(Integer, nullable=False, default=4)
    early_warning_minutes = Column(Integer, nullable=False, default=15)
    notes = Column(Text, nullable=True)
    is_prn = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    auto_start_reminder = Column(Boolean, default=False, nullable=False)

    recipient_id = Column(UUID(as_uuid=True), ForeignKey("care_recipients.id"), nullable=True, index=True)
    recipient = relationship("CareRecipient")

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Medication {self.name}>"
