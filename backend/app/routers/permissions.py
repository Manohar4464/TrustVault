from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.routers.auth import get_current_user
from app.services.audit import record_audit_event

from app.schemas.permission import (
    PermissionGrantRequest,
    PermissionResponse,
    PermissionCheckResponse,
)
router = APIRouter(prefix="/permissions", tags=["Document Permissions"])


@router.post(
    "/grant",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def grant_permission(
    data: PermissionGrantRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the document
    document = (
        db.query(Document)
        .filter(Document.id == data.document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Only the owner or admin can grant permissions
    if (
        str(document.owner_id) != str(current_user.id)
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to share this document",
        )

    # Prevent sharing with yourself
    if str(data.user_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot grant document access to yourself",
        )

    # Find the receiving user
    receiver = (
        db.query(User)
        .filter(
            User.id == data.user_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if receiver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active receiving user not found",
        )

    # Find an existing permission
    permission = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == receiver.id,
        )
        .first()
    )

    if permission is None:
        # Create a new permission
        permission = DocumentPermission(
            document_id=document.id,
            user_id=receiver.id,
            can_read=data.can_read,
            can_edit=data.can_edit,
            can_download=data.can_download,
            is_active=True,
        )
        db.add(permission)
        response_status = status.HTTP_201_CREATED

    else:
        # Update or reactivate existing permission
        permission.can_read = data.can_read
        permission.can_edit = data.can_edit
        permission.can_download = data.can_download
        permission.is_active = True
        response_status = status.HTTP_200_OK

    try:
        db.commit()
        db.refresh(permission)

        record_audit_event(
            db=db,
            user_id=current_user.id,
            document_id=document.id,
            action="GRANT",
            event_status="SUCCESS",
            details=f"Permission granted to user {receiver.id}",
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission could not be saved",
        )
    response.status_code = response_status
    return PermissionResponse(
        id=str(permission.id),
        document_id=str(permission.document_id),
        user_id=str(permission.user_id),
        can_read=permission.can_read,
        can_edit=permission.can_edit,
        can_download=permission.can_download,
        is_active=permission.is_active,
    )

@router.get(
    "/{document_id}",
    response_model=list[PermissionResponse],
)
def list_document_permissions(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the document
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Only owner or admin can view permission records
    if (
        str(document.owner_id) != str(current_user.id)
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view these permissions",
        )

    # Retrieve all permission records, including revoked ones
    permissions = (
        db.query(DocumentPermission)
        .filter(DocumentPermission.document_id == document_id)
        .order_by(DocumentPermission.created_at.desc())
        .all()
    )

    return [
        PermissionResponse(
            id=str(permission.id),
            document_id=str(permission.document_id),
            user_id=str(permission.user_id),
            can_read=permission.can_read,
            can_edit=permission.can_edit,
            can_download=permission.can_download,
            is_active=permission.is_active,
        )
        for permission in permissions
    ]

@router.get(
    "/check/{document_id}",
    response_model=PermissionCheckResponse,
)
def check_document_permission(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the document
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check whether the user is the owner or admin
    is_owner = document.owner_id == current_user.id
    is_admin = current_user.role == "admin"

    # Owners and admins have full access
    if is_owner or is_admin:
        return PermissionCheckResponse(
            document_id=str(document.id),
            user_id=str(current_user.id),
            is_owner=is_owner,
            is_admin=is_admin,
            can_read=True,
            can_edit=True,
            can_download=True,
            is_active=True,
        )

    # Find the current user's permission
    permission = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == current_user.id,
            DocumentPermission.is_active.is_(True),
        )
        .first()
    )

    # No active permission means no access
    if permission is None:
        return PermissionCheckResponse(
            document_id=str(document.id),
            user_id=str(current_user.id),
            is_owner=False,
            is_admin=False,
            can_read=False,
            can_edit=False,
            can_download=False,
            is_active=False,
        )

    return PermissionCheckResponse(
        document_id=str(document.id),
        user_id=str(current_user.id),
        is_owner=False,
        is_admin=False,
        can_read=permission.can_read,
        can_edit=permission.can_edit,
        can_download=permission.can_download,
        is_active=True,
    )

@router.delete(
    "/revoke/{document_id}/{user_id}"
)
def revoke_permission(
    document_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the document
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Only owner or admin can revoke access
    if (
        document.owner_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to revoke access",
        )

    # Find the permission record
    permission = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id,
        )
        .first()
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission record not found",
        )

    if not permission.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission is already revoked",
        )

    # Revoke access without deleting the record
    permission.is_active = False

    db.commit()
    db.refresh(permission)

    record_audit_event(
        db=db,
        user_id=current_user.id,
        document_id=document.id,
        action="REVOKE",
        event_status="SUCCESS",
        details=f"Permission revoked from user {user_id}",
    )

    return {
        "message": "Document access revoked successfully",
        "document_id": str(document_id),
        "user_id": str(user_id),
        "is_active": permission.is_active,
    }
