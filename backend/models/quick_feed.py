from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class QuickFeed(Base):
    __tablename__ = "quick_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    amount_ml = Column(Integer, nullable=True)
    duration_min = Column(Integer, nullable=True)
    formula_type = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<QuickFeed {self.amount_ml}ml {self.duration_min}min {self.formula_type}>"
