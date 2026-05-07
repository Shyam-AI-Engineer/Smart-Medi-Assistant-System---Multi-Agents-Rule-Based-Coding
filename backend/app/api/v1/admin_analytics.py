"""Admin analytics endpoints."""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import require_role
from app.models import ChatHistory, Vitals, Patient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


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
        .scalar() or 0
    )
    messages_today = (
        db.query(func.count(ChatHistory.id))
        .filter(func.date(ChatHistory.created_at) == today)
        .scalar() or 0
    )
    avg_confidence = round(float(db.query(func.avg(ChatHistory.confidence_score)).scalar() or 0), 3)
    total_vitals = db.query(func.count(Vitals.id)).scalar() or 0
    anomaly_count = (
        db.query(func.count(Vitals.id)).filter(Vitals.anomaly_detected.is_(True)).scalar() or 0
    )
    anomaly_rate = round(anomaly_count / total_vitals * 100, 1) if total_vitals else 0

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
        db.query(ChatHistory.agent_used, func.count(ChatHistory.id).label("count"))
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
            func.count(case((Vitals.anomaly_detected.is_(True), Vitals.id))).label("anomalies"),
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
            "rate": round((r.anomalies or 0) / r.total_vitals * 100, 1) if r.total_vitals else 0,
        }
        for r in rows
    ]
