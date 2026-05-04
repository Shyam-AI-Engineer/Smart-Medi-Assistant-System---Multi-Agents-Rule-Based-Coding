"""Admin analytics API endpoints.

Routes:
  GET /api/v1/admin/analytics/overview   – KPI summary
  GET /api/v1/admin/analytics/daily      – per-day metrics (messages, DAU, confidence)
  GET /api/v1/admin/analytics/agents     – agent routing distribution
  GET /api/v1/admin/analytics/anomalies  – anomaly detection trend
  GET /api/v1/admin/audit-logs           – paginated PHI access trail (compliance)
  GET /api/v1/admin/audit-logs/summary   – counts by action + outcome (last 30 days)
  GET /api/v1/admin/users                – paginated user list (filterable)
  GET /api/v1/admin/users/{user_id}      – single user detail
  PUT /api/v1/admin/users/{user_id}      – update user (role, is_active)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import func, case, or_
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import require_role
from app.models import ChatHistory, Vitals, Patient, User
from app.models.audit_log import AuditLog
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics/overview")
def get_analytics_overview(
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Summary KPIs for the investor dashboard."""
    today = datetime.utcnow().date()

    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_messages = db.query(func.count(ChatHistory.id)).scalar() or 0

    dau = (
        db.query(func.count(func.distinct(ChatHistory.patient_id)))
        .filter(func.date(ChatHistory.created_at) == today)
        .scalar()
        or 0
    )
    messages_today = (
        db.query(func.count(ChatHistory.id))
        .filter(func.date(ChatHistory.created_at) == today)
        .scalar()
        or 0
    )

    avg_confidence_raw = db.query(func.avg(ChatHistory.confidence_score)).scalar()
    avg_confidence = round(float(avg_confidence_raw or 0), 3)

    total_vitals = db.query(func.count(Vitals.id)).scalar() or 0
    anomaly_count = (
        db.query(func.count(Vitals.id))
        .filter(Vitals.anomaly_detected.is_(True))
        .scalar()
        or 0
    )
    anomaly_rate = round(anomaly_count / total_vitals * 100, 1) if total_vitals else 0

    # Feedback satisfaction (thumbs_up / total with feedback)
    feedback_rows = (
        db.query(ChatHistory.feedback, func.count(ChatHistory.id))
        .filter(ChatHistory.feedback.isnot(None))
        .group_by(ChatHistory.feedback)
        .all()
    )
    feedback_map = {r[0]: r[1] for r in feedback_rows}
    up = feedback_map.get("thumbs_up", 0)
    down = feedback_map.get("thumbs_down", 0)
    satisfaction = round(up / (up + down) * 100, 1) if (up + down) > 0 else None

    return {
        "total_patients": total_patients,
        "total_messages": total_messages,
        "dau": dau,
        "messages_today": messages_today,
        "avg_confidence": avg_confidence,
        "anomaly_rate": anomaly_rate,
        "total_vitals": total_vitals,
        "satisfaction_rate": satisfaction,
    }


@router.get("/analytics/daily")
def get_daily_metrics(
    days: int = Query(default=30, ge=7, le=90),
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Per-day messages, DAU, and avg confidence for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(ChatHistory.created_at).label("day"),
            func.count(ChatHistory.id).label("messages"),
            func.count(func.distinct(ChatHistory.patient_id)).label("active_patients"),
            func.avg(ChatHistory.confidence_score).label("avg_confidence"),
        )
        .filter(ChatHistory.created_at >= cutoff)
        .group_by(func.date(ChatHistory.created_at))
        .order_by(func.date(ChatHistory.created_at))
        .all()
    )

    return [
        {
            "day": str(r.day),
            "messages": r.messages,
            "active_patients": r.active_patients,
            "avg_confidence": round(float(r.avg_confidence or 0), 3),
        }
        for r in rows
    ]


@router.get("/analytics/agents")
def get_agent_distribution(
    days: int = Query(default=30, ge=7, le=90),
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Agent routing distribution for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            ChatHistory.agent_used,
            func.count(ChatHistory.id).label("count"),
        )
        .filter(ChatHistory.created_at >= cutoff)
        .group_by(ChatHistory.agent_used)
        .order_by(func.count(ChatHistory.id).desc())
        .all()
    )

    return [{"agent": r.agent_used or "unknown", "count": r.count} for r in rows]


@router.get("/analytics/anomalies")
def get_anomaly_trend(
    days: int = Query(default=30, ge=7, le=90),
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Daily vitals recorded and anomalies detected for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Vitals.created_at).label("day"),
            func.count(Vitals.id).label("total_vitals"),
            func.count(
                case((Vitals.anomaly_detected.is_(True), Vitals.id))
            ).label("anomalies"),
        )
        .filter(Vitals.created_at >= cutoff)
        .group_by(func.date(Vitals.created_at))
        .order_by(func.date(Vitals.created_at))
        .all()
    )

    return [
        {
            "day": str(r.day),
            "total_vitals": r.total_vitals,
            "anomalies": r.anomalies or 0,
            "rate": (
                round((r.anomalies or 0) / r.total_vitals * 100, 1)
                if r.total_vitals
                else 0
            ),
        }
        for r in rows
    ]


# ── Audit log endpoints ───────────────────────────────────────────────────────

@router.get("/audit-logs")
def list_audit_logs(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None, description="ISO date, e.g. 2026-01-01"),
    date_to: Optional[str] = Query(default=None, description="ISO date, e.g. 2026-12-31"),
    search: Optional[str] = Query(default=None, description="Filter by email substring"),
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Paginated, filterable audit trail for compliance officers.

    Supports filtering by action, resource_type, outcome, user_id,
    date range, and email substring search.
    """
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
        query
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    # Log that the admin viewed the audit trail
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
    """
    Aggregate counts grouped by action and outcome for the last N days.
    Used to populate the summary cards at the top of the audit log page.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            AuditLog.action,
            AuditLog.outcome,
            func.count(AuditLog.id).label("count"),
        )
        .filter(AuditLog.created_at >= cutoff)
        .group_by(AuditLog.action, AuditLog.outcome)
        .all()
    )

    total_events = sum(r.count for r in rows)
    failures = sum(r.count for r in rows if r.outcome == "failure")
    unique_users = (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(AuditLog.created_at >= cutoff)
        .scalar()
        or 0
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


# ── User management endpoints ─────────────────────────────────────────────────

@router.get("/users")
def list_users(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, description="Filter by email or name substring"),
    role: Optional[str] = Query(default=None, description="Filter by role: patient, doctor, admin"),
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Paginated list of all users (patients, doctors, admins).

    Supports filtering by:
    - search: email or full_name substring match
    - role: PATIENT, DOCTOR, or ADMIN
    """
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = (
        query
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Log the admin viewed user list
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
    payload: dict,
    request: Request,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Update a user's role or is_active status.

    Body: {role?: "patient"|"doctor"|"admin", is_active?: bool}
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []

    # Update role if provided
    if "role" in payload and payload["role"]:
        new_role = payload["role"].lower()
        if new_role not in ["patient", "doctor", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        if user.role.value != new_role:
            changes.append(f"role: {user.role.value} → {new_role}")
            user.role = new_role

    # Update is_active if provided
    if "is_active" in payload and payload["is_active"] is not None:
        new_active = bool(payload["is_active"])
        if user.is_active != new_active:
            changes.append(f"is_active: {user.is_active} → {new_active}")
            user.is_active = new_active

    if not changes:
        # No changes made, return current state
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    db.commit()

    # Log the update
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
