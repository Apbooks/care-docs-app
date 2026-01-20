from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from models.user_recipient_access import UserRecipientAccess


def get_allowed_recipient_ids(db: Session, user: User) -> Optional[List[str]]:
    if user.role == "admin":
        return None
    rows = db.query(UserRecipientAccess).filter(
        UserRecipientAccess.user_id == user.id
    ).all()
    return [str(row.recipient_id) for row in rows]


def ensure_recipient_access(db: Session, user: User, recipient_id: str) -> None:
    if user.role == "admin":
        return
    allowed = get_allowed_recipient_ids(db, user)
    if not allowed or recipient_id not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this recipient"
        )


def require_write_access(user: User) -> None:
    if user.role == "read_only":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read-only users cannot modify data"
        )
