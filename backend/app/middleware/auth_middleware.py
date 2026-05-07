"""JWT authentication middleware for FastAPI."""
import os
import jwt
import logging
import uuid
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.utils.cache import cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

_JWT_SECRET_RAW = os.getenv("JWT_SECRET_KEY", "")
_INSECURE_DEFAULTS = {"", "dev-secret-change-in-production", "your-super-secret-key-change-this-in-production-min-32-chars"}

if _JWT_SECRET_RAW in _INSECURE_DEFAULTS:
    raise RuntimeError(
        "STARTUP BLOCKED: JWT_SECRET_KEY is missing or set to a known insecure default.\n"
        "Set a strong random value in your .env file:\n"
        "  JWT_SECRET_KEY=<run: python -c \"import secrets; print(secrets.token_hex(32))\">"
    )

JWT_SECRET = _JWT_SECRET_RAW
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


security = HTTPBearer()


def is_token_revoked(jti: str) -> bool:
    """Check if token JTI is in revocation list."""
    revoked = cache_get(f"revoked_token:{jti}")
    return revoked is True


def revoke_token(jti: str, ttl_seconds: int) -> None:
    """Add token JTI to revocation list with TTL."""
    cache_set(f"revoked_token:{jti}", True, ttl=ttl_seconds)
    logger.info(f"Token revoked: {jti}")


def get_current_user(
    credentials = Depends(security),
) -> Dict[str, any]:
    """
    Validate JWT token and extract user info.

    Used in routes:
    @router.post("/api/v1/chat")
    def send_message(current_user: dict = Depends(get_current_user)):
        return current_user

    Returns dict with: user_id, email, role, jti

    Raises HTTPException 401 if token invalid/expired/revoked.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role", "patient")
        jti: str = payload.get("jti")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token has been revoked (logged out)
        if jti and is_token_revoked(jti):
            logger.warning(f"Token revoked: {jti}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"user_id": user_id, "email": email, "role": role, "jti": jti}

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
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
    """Create JWT access token with unique JTI for revocation support."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: str, email: str) -> str:
    """Create long-lived JWT refresh token (default 7 days) with JTI for revocation."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "email": email,
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_refresh_token(token: str) -> Optional[Dict]:
    """Verify a refresh token and return its payload, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("token_type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None
