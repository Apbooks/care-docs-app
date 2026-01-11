#!/usr/bin/env python3
"""
Simple admin user creation script - directly creates admin user
"""

import sys
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.user import User
import bcrypt


def create_admin_user():
    """Create admin user with hardcoded credentials"""

    print("\n" + "="*60)
    print(" Create Admin User - Simple Version")
    print("="*60 + "\n")

    # Get user input
    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        sys.exit(1)

    password = input("Password: ").strip()
    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        sys.exit(1)

    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized\n")

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Error: Username '{username}' already exists")
            sys.exit(1)

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            print(f"Error: Email '{email}' already exists")
            sys.exit(1)

        # Hash password directly with bcrypt (truncate to 72 bytes)
        print(f"Creating admin user '{username}'...")
        password_bytes = password.encode('utf-8')[:72]
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

        admin_user = User(
            username=username,
            email=email,
            password_hash=hashed.decode('utf-8'),
            role="admin",
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print()
        print("="*60)
        print(" ✓ Admin user created successfully!")
        print("="*60)
        print(f"\nUsername: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Role: {admin_user.role}")
        print(f"User ID: {admin_user.id}")
        print(f"\nYou can now log in at: http://your-raspberry-pi-ip:3000/login")
        print()

    except Exception as e:
        db.rollback()
        print(f"\nError creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
