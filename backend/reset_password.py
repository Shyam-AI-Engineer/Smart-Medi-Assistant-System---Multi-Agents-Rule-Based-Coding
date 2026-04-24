"""Reset password for test user."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

env_file = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_file)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    from app.models import User

    email = "admin@example.com"
    user = db.query(User).filter_by(email=email).first()

    if not user:
        print(f"❌ User '{email}' not found")
    else:
        print(f"✅ Found user: {user.email}")

        # Set password to 'password123'
        user.set_password("password123")
        db.commit()

        print(f"✅ Password reset to: password123")
        print(f"✅ Use this to login in Swagger")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()

finally:
    db.close()
