"""Shared pytest fixtures for the Smart Medi Assistant backend test suite."""
import os
import uuid

# Must be set before any app modules are imported.
# auth_middleware.py validates JWT_SECRET_KEY at import time and raises RuntimeError
# if it is missing or matches a known insecure default.
os.environ.setdefault("JWT_SECRET_KEY", "ci-test-secret-32-chars-minimum!!")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app import app as fastapi_app
from app.models import BaseModel, User, UserRole, Patient
from app.extensions import get_db
from app.middleware.auth_middleware import create_access_token


# ---------------------------------------------------------------------------
# Database fixtures (fresh in-memory SQLite per test)
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine():
    """Create a fresh in-memory SQLite engine for one test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    BaseModel.metadata.create_all(engine)
    yield engine
    BaseModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    """Database session bound to the test engine."""
    Session = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    """TestClient with get_db overridden to use the test database."""
    def _override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app, raise_server_exceptions=False) as tc:
        yield tc
    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Rate-limiter reset (SlowAPI stores counters in-process between tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear SlowAPI in-memory rate-limit counters before each test."""
    from app.middleware.rate_limit import limiter
    try:
        limiter._storage.reset()
    except Exception:
        pass
    yield


# ---------------------------------------------------------------------------
# User / token helpers (create directly in DB to avoid API rate limits)
# ---------------------------------------------------------------------------

def make_user(
    db,
    email: str,
    role: str = "patient",
    full_name: str = "Test User",
) -> User:
    """Insert a User (and Patient profile if applicable) directly into the test DB."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        full_name=full_name,
        role=UserRole[role.upper()],
        is_active=True,
    )
    user.set_password("Password1!")
    db.add(user)

    if UserRole[role.upper()] in (UserRole.PATIENT, UserRole.DOCTOR):
        patient = Patient(id=str(uuid.uuid4()), user_id=user.id)
        db.add(patient)

    db.commit()
    db.refresh(user)
    return user


def token_for(user: User) -> str:
    """Generate a signed JWT access token for a user."""
    return create_access_token(user.id, user.email, user.role.value)


def auth_header(user: User) -> dict:
    """Return an Authorization header dict for the given user."""
    return {"Authorization": f"Bearer {token_for(user)}"}


# ---------------------------------------------------------------------------
# Per-test user fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def patient_user(db) -> User:
    return make_user(db, "patient@test.com", "patient", "Alice Patient")


@pytest.fixture()
def second_patient_user(db) -> User:
    return make_user(db, "patient2@test.com", "patient", "Bob Patient")


@pytest.fixture()
def doctor_user(db) -> User:
    return make_user(db, "doctor@test.com", "doctor", "Dr. Smith")


@pytest.fixture()
def admin_user(db) -> User:
    return make_user(db, "admin@test.com", "admin", "Admin User")


@pytest.fixture()
def patient_headers(patient_user) -> dict:
    return auth_header(patient_user)


@pytest.fixture()
def second_patient_headers(second_patient_user) -> dict:
    return auth_header(second_patient_user)


@pytest.fixture()
def doctor_headers(doctor_user) -> dict:
    return auth_header(doctor_user)


@pytest.fixture()
def admin_headers(admin_user) -> dict:
    return auth_header(admin_user)


@pytest.fixture()
def patient_record(db, patient_user) -> Patient:
    """The Patient profile row for patient_user."""
    return db.query(Patient).filter_by(user_id=patient_user.id).first()


@pytest.fixture()
def second_patient_record(db, second_patient_user) -> Patient:
    return db.query(Patient).filter_by(user_id=second_patient_user.id).first()
