from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database import Base


class UserInvite(Base):
    __tablename__ = "user_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    role = Column(String(20), nullable=False, default="caregiver")
    recipient_ids = Column(JSONB, nullable=False, default=list)

    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserInvite {self.email} {self.username}>"
