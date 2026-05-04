"""Audit logging helper — write PHI access events to audit_logs table.

Call write_audit() from any route after the main operation succeeds.
It silently swallows its own exceptions so a logging failure never
takes down the real request.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def write_audit(
    db: Session,
    *,
    user_id: str,
    user_email: str,
    user_role: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    outcome: str = "success",
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """Append one row to audit_logs.

    Must be called *before* the route returns so that get_db()'s
    auto-commit picks it up in the same transaction.

    Args:
        db:            The active SQLAlchemy session (from get_db()).
        user_id:       UUID of the acting user.
        user_email:    Denormalised email (stays readable if user deleted).
        user_role:     Denormalised role string.
        action:        Snake-case verb: login | register | view_patient |
                       view_vitals | record_vitals | send_chat |
                       view_chat_history | export_pdf | view_audit_logs.
        resource_type: Domain noun: auth | patient | vitals | chat | admin.
        resource_id:   Optional UUID of the specific record accessed.
        outcome:       "success" or "failure".
        ip_address:    Client IP from the request (optional).
        details:       Free-text note (failure reason, record count, etc.).
    """
    from app.models.audit_log import AuditLog
    try:
        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            ip_address=ip_address,
            details=details,
        )
        db.add(log)
        # No explicit commit — get_db() commits on request success.
    except Exception as exc:
        logger.warning("audit write failed (non-fatal): %s", exc)


def get_client_ip(request) -> Optional[str]:
    """Extract real client IP, respecting X-Forwarded-For from proxies."""
    forwarded = getattr(request.headers, "get", lambda k, d=None: d)("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    return client.host if client else None
