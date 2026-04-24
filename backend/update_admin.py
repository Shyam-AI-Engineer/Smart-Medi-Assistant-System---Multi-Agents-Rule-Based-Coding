"""Quick script to make current user an admin."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment
env_file = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_file)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    exit(1)

# Connect to database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    from app.models import User

    email = "admin@example.com"  # Use existing test account
    user = db.query(User).filter_by(email=email).first()

    if not user:
        print(f"❌ User with email '{email}' not found")
        print("\nAvailable users:")
        users = db.query(User).all()
        for u in users:
            print(f"  - {u.email} (role: {u.role})")
    else:
        print(f"✅ Found user: {user.email}")
        print(f"   Current role: {user.role}")

        user.role = "admin"
        db.commit()

        print(f"✅ Updated role to: {user.role}")
        print("\nYou can now use the ingest endpoint!")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()

finally:
    db.close()
