"""
Setup endpoints for initial system configuration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from database import get_db
from models.user import User
from services.auth_service import get_password_hash

router = APIRouter()


class InitialAdminCreate(BaseModel):
    """Schema for creating the first admin user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
def initialize_system(
    admin_data: InitialAdminCreate,
    db: Session = Depends(get_db)
):
    """
    Create the first admin user. Only works if no users exist yet.
    This endpoint is ONLY available when the database is empty.
    """

    # Check if any users already exist
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System already initialized. Use the register endpoint with admin credentials."
        )

    # Check if username already exists (shouldn't happen, but just in case)
    existing_user = db.query(User).filter(User.username == admin_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == admin_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create the first admin user
    admin_user = User(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=get_password_hash(admin_data.password),
        role="admin",
        is_active=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "message": "System initialized successfully",
        "admin": {
            "id": str(admin_user.id),
            "username": admin_user.username,
            "email": admin_user.email,
            "role": admin_user.role
        }
    }


@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    """
    Check if the system needs initialization
    """
    user_count = db.query(User).count()

    return {
        "initialized": user_count > 0,
        "user_count": user_count,
        "needs_setup": user_count == 0
    }
