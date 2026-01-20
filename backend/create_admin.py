#!/usr/bin/env python3
"""
Script to create the first admin user for the Care Documentation App

Usage:
    python create_admin.py

Or from Docker:
    docker exec -it care-docs-backend python create_admin.py
"""

import sys
from getpass import getpass
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.user import User
from sqlalchemy import func
from services.auth_service import get_password_hash, normalize_username, validate_password_strength


def create_admin_user():
    """Interactive script to create an admin user"""

    print("\n" + "="*60)
    print(" Create Admin User - Care Documentation App")
    print("="*60 + "\n")

    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized\n")

    # Get user input
    print("Enter admin user details:")
    print("-" * 60)

    username_input = input("Username: ").strip()
    normalized_username = normalize_username(username_input)
    if not normalized_username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        sys.exit(1)

    password = getpass("Password (include upper, lower, number): ")
    password_errors = validate_password_strength(password)
    if password_errors:
        print("Error: " + " ".join(password_errors))
        sys.exit(1)

    password_confirm = getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    print()

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if username already exists
        existing_user = db.query(User).filter(func.lower(User.username) == normalized_username).first()
        if existing_user:
            print(f"Error: Username '{normalized_username}' already exists")
            sys.exit(1)

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            print(f"Error: Email '{email}' already exists")
            sys.exit(1)

        # Create admin user
        print(f"Creating admin user '{normalized_username}'...")

        admin_user = User(
            username=normalized_username,
            email=email,
            password_hash=get_password_hash(password),
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
        print(f"\nYou can now log in at: http://localhost:3000/login")
        print()

    except Exception as e:
        db.rollback()
        print(f"\nError creating admin user: {e}")
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
