#!/usr/bin/env python3
"""Create a test user for diagnostics."""
from app.extensions import SessionLocal
from app.models import User, Patient
from datetime import date

db = SessionLocal()

try:
    # Check if test user already exists
    existing = db.query(User).filter_by(email="patient@example.com").first()
    if existing:
        print(f"✓ Test user already exists: {existing.email}")
        print(f"  ID: {existing.id}")
        db.close()
        exit(0)

    # Create new user
    user = User(
        email="patient@example.com",
        full_name="Test Patient",
        role="patient",
        is_active=True
    )
    user.set_password("password123")

    db.add(user)
    db.flush()  # Get the ID

    # Create patient profile
    patient = Patient(
        user_id=user.id,
        date_of_birth=date(1990, 1, 1),
        medical_history="Test patient for diagnostics",
        allergies="None",
        current_medications="None",
        emergency_contact="000-000-0000"
    )

    db.add(patient)
    db.commit()

    print(f"✓ Created test user")
    print(f"  Email: {user.email}")
    print(f"  Password: password123")
    print(f"  User ID: {user.id}")
    print(f"  Patient ID: {patient.id}")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
