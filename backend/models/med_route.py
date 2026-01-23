from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


medication_routes = Table(
    "medication_routes",
    Base.metadata,
    Column("medication_id", UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), primary_key=True),
    Column("route_id", UUID(as_uuid=True), ForeignKey("med_routes.id", ondelete="CASCADE"), primary_key=True)
)


class MedRoute(Base):
    __tablename__ = "med_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    recipient_id = Column(UUID(as_uuid=True), ForeignKey("care_recipients.id"), nullable=True, index=True)
    recipient = relationship("CareRecipient")

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    medications = relationship("Medication", secondary=medication_routes, back_populates="routes")

    def __repr__(self):
        return f"<MedRoute {self.name}>"
