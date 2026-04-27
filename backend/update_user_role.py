#!/usr/bin/env python3
"""Update user role in database."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models import User, UserRole
from app.extensions import SessionLocal

def update_user_role(email: str, role: str):
    """Update a user's role by email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False

        # Convert role string to enum
        try:
            user.role = UserRole[role.upper()]
        except KeyError:
            valid_roles = ", ".join([r.value for r in UserRole])
            print(f"❌ Invalid role '{role}'. Valid roles: {valid_roles}")
            return False

        db.commit()
        print(f"✅ Updated {user.email} to role: {user.role.value}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_user_role.py <email> <role>")
        print("Example: python update_user_role.py doctor@example.com doctor")
        print("Valid roles: patient, doctor, nurse, admin")
        sys.exit(1)

    email = sys.argv[1]
    role = sys.argv[2]

    success = update_user_role(email, role)
    sys.exit(0 if success else 1)
