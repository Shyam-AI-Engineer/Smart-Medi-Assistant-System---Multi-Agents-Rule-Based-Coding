"""Auth service - register, login, refresh, get current user."""
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User, Patient, UserRole
from app.middleware.auth_middleware import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def register(self, request: RegisterRequest) -> TokenResponse:
        """Register a new account and auto-create patient profile if role is patient/doctor."""
        existing = self.db.query(User).filter_by(email=request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Determine role from request, validate it
        role_str = request.role or "patient"
        try:
            role = UserRole[role_str.upper()]
        except KeyError:
            role = UserRole.PATIENT  # Default to patient on invalid role
            logger.warning(f"Invalid role '{role_str}' provided during registration, defaulting to patient")

        user = User(
            email=request.email,
            full_name=request.full_name,
            role=role,
            is_active=True,
        )
        user.set_password(request.password)
        self.db.add(user)
        self.db.flush()  # Assigns user.id before commit so Patient FK is valid

        # Only create patient profile for patient and doctor roles
        if role in [UserRole.PATIENT, UserRole.DOCTOR]:
            patient = Patient(user_id=user.id)
            self.db.add(patient)

        self.db.commit()

        logger.info(f"New user registered: {user.email} (role: {role.value})")
        return self._build_token_response(user)

    def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate with email + password and return tokens."""
        user = self.db.query(User).filter_by(email=request.email).first()
        if not user or not user.check_password(request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Contact support.",
            )

        logger.info(f"User logged in: {user.email}")
        return self._build_token_response(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        """Issue a new access token from a valid refresh token."""
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = self.db.query(User).filter_by(id=payload["user_id"]).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account disabled",
            )

        return self._build_token_response(user)

    def get_me(self, user_id: str) -> User:
        """Fetch the currently authenticated user by ID."""
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_token_response(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        refresh_tok = create_refresh_token(user_id=user.id, email=user.email)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_tok,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
