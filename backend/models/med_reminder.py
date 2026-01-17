from sqlalchemy import Column, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class MedicationReminder(Base):
    __tablename__ = "medication_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    recipient_id = Column(UUID(as_uuid=True), ForeignKey("care_recipients.id"), nullable=False, index=True)
    recipient = relationship("CareRecipient")

    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    medication = relationship("Medication")

    start_time = Column(DateTime, nullable=True)
    interval_hours = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    last_given_at = Column(DateTime, nullable=True)
    last_skipped_at = Column(DateTime, nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MedicationReminder {self.medication_id} for {self.recipient_id}>"
