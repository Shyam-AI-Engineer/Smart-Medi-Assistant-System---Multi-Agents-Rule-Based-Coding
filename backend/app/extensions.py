"""Database, Redis, and external service initialization."""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import redis

# ============================================================================
# DATABASE SETUP (PostgreSQL via SQLAlchemy)
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/smart_medi_dev"
)
# Railway (and some cloud providers) give postgres:// URLs.
# SQLAlchemy 2.0 dropped the postgres:// dialect alias — must be postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ Create engine with connection pooling
# In development: use QueuePool (default, good for testing)
# In production: use QueuePool with pool_size, max_overflow for high concurrency
if os.getenv("ENVIRONMENT") == "production":
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Don't log SQL in production
        pool_size=20,  # Number of persistent connections
        max_overflow=40,  # Additional connections allowed
        pool_pre_ping=True,  # Verify connection before using
        pool_recycle=3600,  # Recycle connections every hour
    )
else:
    # Development: simpler pool configuration
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "False") == "True",  # Log SQL if DEBUG=True
        pool_size=5,
        max_overflow=10,
    )

# Create session factory
# Each request gets a new session via Depends(get_db)
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual flush for better control
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI.

    Provides a database session to each request.
    Auto-commits on success, rolls back on error.

    Usage in routes:
        @router.get("/api/v1/patients/{id}")
        def get_patient(id: str, db: Session = Depends(get_db)):
            patient = db.query(Patient).get(id)
            return patient
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit if no exception
    except Exception:
        db.rollback()  # Rollback on any error
        raise
    finally:
        db.close()  # Always close connection


# ============================================================================
# REDIS SETUP (Caching & Session Storage)
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2,
    )
    redis_client.ping()
except Exception as e:
    print(f"WARNING: Redis not available ({type(e).__name__}) - caching disabled")
    redis_client = None


def get_cache():
    """Get Redis cache client (or None if unavailable)."""
    return redis_client


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Create all tables directly from models — FOR TESTS ONLY.

    Production startup uses Alembic migrations (see app/__init__.py startup_event).
    This function is retained for the pytest fixtures in tests/conftest.py which
    spin up an in-memory SQLite database and bypass the Alembic runner.
    """
    from app.models import BaseModel  # Import here to avoid circular imports
    BaseModel.metadata.create_all(bind=engine)


# ============================================================================
# DATABASE MIGRATIONS (Alembic Alternative)
# ============================================================================

def create_session():
    """Create a standalone session (not for FastAPI routes)."""
    return SessionLocal()


# ============================================================================
# CONNECTION DIAGNOSTICS
# ============================================================================

def check_database_connection() -> bool:
    """Test if database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_redis_connection() -> bool:
    """Test if Redis is reachable."""
    if redis_client is None:
        return False
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connections on script execution
    print("Testing database connection...")
    if check_database_connection():
        print("✅ Database connected")

    print("\nTesting Redis connection...")
    if check_redis_connection():
        print("✅ Redis connected")
    else:
        print("⚠️  Redis not available")
