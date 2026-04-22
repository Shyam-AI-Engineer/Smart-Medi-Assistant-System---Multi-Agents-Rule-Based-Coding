"""JWT authentication middleware for FastAPI."""
import os
import jwt
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> Dict[str, any]:
    """
    Validate JWT token and extract user info.

    Used in routes:
    @router.post("/api/v1/chat")
    def send_message(current_user: dict = Depends(get_current_user)):
        return current_user

    Returns dict with: user_id, email, role, exp

    Raises HTTPException 401 if token invalid/expired.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role", "patient")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user_id": user_id,
            "email": email,
            "role": role,
        }

    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles: str):
    """
    Dependency to enforce role-based access control.

    Usage:
    @router.get("/api/v1/admin/users")
    def list_users(_: dict = Depends(require_role("admin"))):
        return users
    """
    def check_role(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: requires one of {allowed_roles}"
            )
        return current_user

    return check_role


def create_access_token(
    user_id: str,
    email: str,
    role: str = "patient",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    return encoded_jwt
