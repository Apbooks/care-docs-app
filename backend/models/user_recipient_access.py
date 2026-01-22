import uuid

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class UserRecipientAccess(Base):
    __tablename__ = "user_recipient_access"
    __table_args__ = (
        UniqueConstraint("user_id", "recipient_id", name="uniq_user_recipient"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("care_recipients.id"), nullable=False, index=True)

    user = relationship("User")
    recipient = relationship("CareRecipient")

    def __repr__(self):
        return f"<UserRecipientAccess {self.user_id} {self.recipient_id}>"
