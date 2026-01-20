#!/usr/bin/env python3
"""
Simple script to create admin user by connecting directly to PostgreSQL
Run this OUTSIDE Docker on the Raspberry Pi

Usage:
    python3 create_admin_simple.py

Requirements:
    pip install psycopg2-binary bcrypt
"""

import sys
import psycopg2
from getpass import getpass
import bcrypt
import hashlib
import uuid

# Database connection details
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "caredb"
DB_USER = "careapp"
DB_PASSWORD = "1d2361418342716c0649a2294e8b02441c86951db7311990f9c3aa60767a352c"

def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def validate_password_strength(password: str) -> list:
    errors = []
    if not any(ch.islower() for ch in password):
        errors.append("Password must include a lowercase letter.")
    if not any(ch.isupper() for ch in password):
        errors.append("Password must include an uppercase letter.")
    if not any(ch.isdigit() for ch in password):
        errors.append("Password must include a number.")
    return errors


def hash_password(password: str) -> str:
    """Hash a password using bcrypt over sha256 for compatibility."""
    sha = hashlib.sha256(password.encode('utf-8')).digest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(sha, salt)
    return hashed.decode('utf-8')

def create_admin():
    print("\n" + "="*60)
    print(" Create Admin User - Care Documentation App")
    print("="*60 + "\n")

    # Get user input
    username_input = input("Username: ").strip()
    username = normalize_username(username_input)
    if not username:
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

    print("\nConnecting to database...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
        if cursor.fetchone():
            print(f"\nError: Username '{username}' already exists")
            conn.close()
            sys.exit(1)

        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"\nError: Email '{email}' already exists")
            conn.close()
            sys.exit(1)

        # Create admin user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)

        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (user_id, username, email, password_hash, 'admin', True))

        conn.commit()

        print("\n" + "="*60)
        print(" ✓ Admin user created successfully!")
        print("="*60)
        print(f"\nUsername: {username}")
        print(f"Email: {email}")
        print(f"Role: admin")
        print(f"User ID: {user_id}")
        print(f"\nYou can now log in at: http://192.168.1.101:3000/login")
        print()

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        sys.exit(1)
