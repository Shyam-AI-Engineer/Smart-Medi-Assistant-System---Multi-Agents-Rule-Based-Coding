"""Admin user management endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import require_role
from app.models import User, UserRole
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


class UpdateUserRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@router.get("/users")
def list_users(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Paginated list of all users, filterable by email/name and role."""
    query = db.query(User)
    if search:
        query = query.filter(
            or_(User.email.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="view_user_list",
        resource_type="admin",
        ip_address=get_client_ip(request),
        details=f"limit={limit} offset={offset} search={search} role={role}",
    )

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "updated_at": u.updated_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_next": (offset + limit) < total,
    }


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get a single user's details."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    request: Request,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update a user's role or is_active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []
    if payload.role is not None:
        new_role = payload.role.value
        if user.role.value != new_role:
            changes.append(f"role: {user.role.value} → {new_role}")
            user.role = payload.role
    if payload.is_active is not None:
        if user.is_active != payload.is_active:
            changes.append(f"is_active: {user.is_active} → {payload.is_active}")
            user.is_active = payload.is_active

    if changes:
        db.commit()
        write_audit(
            db,
            user_id=current_user["user_id"],
            user_email=current_user["email"],
            user_role=current_user["role"],
            action="update_user",
            resource_type="admin",
            resource_id=user_id,
            ip_address=get_client_ip(request),
            details=f"Changes: {'; '.join(changes)}",
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
