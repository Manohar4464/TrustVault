
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

# Import all models so SQLAlchemy registers their tables.
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.audit_log import AuditLog


ALLOWED_ACTIONS = {
    "UPLOAD",
    "DOWNLOAD",
    "GRANT",
    "REVOKE",
    "ACCESS_DENIED",
}

ALLOWED_STATUSES = {
    "SUCCESS",
    "DENIED",
}


def record_audit_event(
    db: Session,
    user_id: Optional[UUID],
    document_id: Optional[UUID],
    action: str,
    event_status: str,
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
):
    """Save a security event in the audit_logs table."""

    if action not in ALLOWED_ACTIONS:
        raise ValueError("Invalid audit action")

    if event_status not in ALLOWED_STATUSES:
        raise ValueError("Invalid audit status")

    if details is not None:
        details = details[:500]

    audit_entry = AuditLog(
        user_id=user_id,
        document_id=document_id,
        action=action,
        status=event_status,
        ip_address=ip_address,
        details=details,
    )

    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

    except Exception:
        db.rollback()
        raise

    return audit_entry
