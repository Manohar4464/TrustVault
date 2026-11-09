
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/admin/audit",
    tags=["Admin Audit"],
)


@router.get("/")
def get_audit_logs(
    document_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    event_status: Optional[str] = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only administrators can view audit logs
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access audit logs",
        )

    query = db.query(AuditLog)

    # Apply optional filters
    if document_id is not None:
        query = query.filter(
            AuditLog.document_id == document_id
        )

    if user_id is not None:
        query = query.filter(
            AuditLog.user_id == user_id
        )

    if action is not None:
        query = query.filter(
            AuditLog.action == action.upper()
        )

    if event_status is not None:
        query = query.filter(
            AuditLog.status == event_status.upper()
        )

    # Count matching records before pagination
    total = query.count()

    # Retrieve newest audit events first
    logs = (
        query
        .order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(log.id),
                "user_id": (
                    str(log.user_id)
                    if log.user_id else None
                ),
                "document_id": (
                    str(log.document_id)
                    if log.document_id else None
                ),
                "action": log.action,
                "status": log.status,
                "ip_address": (
                    str(log.ip_address)
                    if log.ip_address else None
                ),
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }
