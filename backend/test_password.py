#!/usr/bin/env python3
"""Test password verification."""
from app.extensions import SessionLocal
from app.models import User

db = SessionLocal()

try:
    user = db.query(User).filter_by(email="patient@example.com").first()
    if not user:
        print("❌ User not found")
        exit(1)

    print(f"User: {user.email}")
    print(f"Password hash: {user.password_hash[:50]}...")

    # Test password verification
    test_pwd = "password123"
    result = user.check_password(test_pwd)

    print(f"✓ Password check result: {result}")

    if not result:
        print("\n❌ Password verification failed. Resetting password...")
        user.set_password(test_pwd)
        db.commit()
        print("✓ Password reset. Try login again.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
