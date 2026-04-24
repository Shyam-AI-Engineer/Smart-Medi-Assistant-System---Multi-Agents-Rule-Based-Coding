#!/usr/bin/env python3
"""Test database connectivity and initialization."""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("SMART MEDI ASSISTANT - DATABASE DIAGNOSTICS")
print("=" * 60)

# 1. Check environment variables
print("\n1. Checking environment variables...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    print(f"   ✓ DATABASE_URL: {db_url[:50]}..." if db_url else "   ✗ DATABASE_URL not set")
    print(f"   ✓ JWT_SECRET_KEY: {'Set' if jwt_secret else 'Not set'}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 2. Check database connection
print("\n2. Testing database connection...")
try:
    from app.extensions import check_database_connection
    if check_database_connection():
        print("   ✓ Database connection successful")
    else:
        print("   ✗ Database connection failed")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Test model imports
print("\n3. Testing model imports...")
try:
    from app.models import BaseModel, User, Patient, UserRole
    print("   ✓ All models imported successfully")
    print(f"   - BaseModel: {BaseModel}")
    print(f"   - User: {User}")
    print(f"   - Patient: {Patient}")
except Exception as e:
    print(f"   ✗ Error importing models: {e}")
    import traceback
    traceback.print_exc()

# 4. Test database initialization
print("\n4. Testing database initialization...")
try:
    from app.extensions import init_db
    init_db()
    print("   ✓ Database tables created/verified")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 5. Test a simple query
print("\n5. Testing simple query...")
try:
    from app.extensions import SessionLocal
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f"   ✓ Query successful - {user_count} users in database")
    db.close()
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 6. Test schema imports
print("\n6. Testing schema imports...")
try:
    from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
    print("   ✓ All schemas imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 7. Test service imports
print("\n7. Testing service imports...")
try:
    from app.services.auth_service import AuthService
    print("   ✓ AuthService imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTICS COMPLETE")
print("=" * 60)
