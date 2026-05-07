"""Admin audit log endpoints."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import require_role
from app.models.audit_log import AuditLog
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.get("/audit-logs")
def list_audit_logs(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Paginated, filterable audit trail for compliance officers."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if outcome:
        query = query.filter(AuditLog.outcome == outcome)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if search:
        query = query.filter(AuditLog.user_email.ilike(f"%{search}%"))
    if date_from:
        try:
            query = query.filter(AuditLog.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    total = query.count()
    rows = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="view_audit_logs",
        resource_type="admin",
        ip_address=get_client_ip(request),
        details=f"page={page} limit={limit}",
    )

    return {
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_email": r.user_email,
                "user_role": r.user_role,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "outcome": r.outcome,
                "ip_address": r.ip_address,
                "details": r.details,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "has_next": (page * limit) < total,
    }


@router.get("/audit-logs/summary")
def audit_logs_summary(
    days: int = Query(default=30, ge=1, le=90),
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Aggregate counts by action and outcome for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(AuditLog.action, AuditLog.outcome, func.count(AuditLog.id).label("count"))
        .filter(AuditLog.created_at >= cutoff)
        .group_by(AuditLog.action, AuditLog.outcome)
        .all()
    )

    total_events = sum(r.count for r in rows)
    failures = sum(r.count for r in rows if r.outcome == "failure")
    unique_users = (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(AuditLog.created_at >= cutoff)
        .scalar() or 0
    )

    breakdown = {}
    for r in rows:
        key = r.action
        if key not in breakdown:
            breakdown[key] = {"action": key, "success": 0, "failure": 0, "total": 0}
        breakdown[key][r.outcome] = r.count
        breakdown[key]["total"] += r.count

    return {
        "total_events": total_events,
        "failures": failures,
        "unique_users": unique_users,
        "breakdown": sorted(breakdown.values(), key=lambda x: -x["total"]),
        "days": days,
    }
