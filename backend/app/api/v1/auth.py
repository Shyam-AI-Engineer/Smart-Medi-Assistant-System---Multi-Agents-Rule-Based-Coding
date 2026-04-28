"""Auth routes: register, login, token refresh, current user."""
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.services.auth_service import AuthService
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_security = HTTPBearer()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new patient account",
)
@limiter.limit("3/minute")
def register(
    _request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Create a patient account. Also auto-creates an empty patient profile.

    Returns access + refresh JWT tokens on success.
    """
    return AuthService(db).register(body)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
@limiter.limit("5/minute")
def login(
    _request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password.

    Returns access + refresh JWT tokens.
    """
    return AuthService(db).login(body)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh_token(
    credentials = Depends(_security),
    db: Session = Depends(get_db),
):
    """
    Exchange a valid refresh token (sent in Authorization header) for a new
    access token + refresh token pair.
    """
    return AuthService(db).refresh(credentials.credentials)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user info",
)
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return profile for the currently authenticated user.

    Requires a valid access token in the Authorization header.
    """
    user = AuthService(db).get_me(current_user["user_id"])
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )
