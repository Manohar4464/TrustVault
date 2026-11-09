from sqlalchemy import or_
import os
import uuid

from pathlib import Path
from urllib.parse import quote

from fastapi.responses import Response
from cryptography.exceptions import InvalidTag
from fastapi import Request
from app.services.audit import record_audit_event

from app.models.document_permission import DocumentPermission
from app.services.encryption import decrypt_file
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.storage import STORAGE_DIR
from app.models.user import User
from app.models.document import Document
from app.routers.auth import get_current_user
from app.services.encryption import encrypt_file


router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".docx",
}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only owners and administrators can upload documents.
    if current_user.role not in ("owner", "admin", "user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to upload documents",
        )

    # Validate the filename and extension.
    original_filename = Path(file.filename or "").name

    if (
        not original_filename
        or len(original_filename) > 255
        or original_filename in (".", "..")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type is not allowed",
        )

    # Read at most 10 MB + 1 byte to detect oversized uploads.
    data = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty files are not allowed",
        )

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum file size is 10 MB",
        )

    # Encrypt the file before saving it.
    encrypted_data, nonce = encrypt_file(data)

    # Generate a random server-controlled storage filename.
    storage_filename = f"{uuid.uuid4()}.enc"
    storage_path = STORAGE_DIR / storage_filename

    try:
        # Exclusive creation prevents accidental overwriting.
        with storage_path.open("xb") as encrypted_file:
            encrypted_file.write(encrypted_data)

        document = Document(
            filename=original_filename,
            storage_path=storage_filename,
            owner_id=current_user.id,
            file_size=len(data),
            nonce=nonce,
            encryption_algorithm="AES-256-GCM",
        )

        db.add(document)
        db.flush()

        # Record successful upload in the audit log.
        record_audit_event(
            db=db,
            user_id=current_user.id,
            document_id=document.id,
            action="UPLOAD",
            event_status="SUCCESS",
            ip_address=request.client.host if request.client else None,
            details="Document uploaded and encrypted successfully",
        )

        db.refresh(document)

    except (OSError, SQLAlchemyError):
        db.rollback()

        # Remove the encrypted file if the database operation fails.
        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed",
        )

    return {
        "message": "Document uploaded and encrypted successfully",
        "document_id": str(document.id),
        "filename": document.filename,
        "file_size": document.file_size,
        "encryption": document.encryption_algorithm,
        "created_at": document.created_at,
    }
@router.get("/")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Administrators can see all documents.
    if current_user.role == "admin":
        documents = (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

        return {
            "total": len(documents),
            "items": [
                {
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "encryption": doc.encryption_algorithm,
                    "created_at": doc.created_at,
                    "access": {
                        "can_read": True,
                        "can_edit": True,
                        "can_download": True,
                        "is_owner": doc.owner_id == current_user.id,
                    },
                }
                for doc in documents
            ],
        }

    # Owners and viewers can see their own documents
    # or documents shared with them with active read permission.
    results = (
        db.query(Document, DocumentPermission)
        .outerjoin(
            DocumentPermission,
            DocumentPermission.document_id == Document.id,
        )
        .filter(
            or_(
                Document.owner_id == current_user.id,
                (
                    (DocumentPermission.user_id == current_user.id)
                    & (DocumentPermission.is_active.is_(True))
                    & (DocumentPermission.can_read.is_(True))
                ),
            )
        )
        .order_by(Document.created_at.desc())
        .all()
    )

    items = []

    for doc, permission in results:
        is_owner = doc.owner_id == current_user.id

        items.append({
            "document_id": str(doc.id),
            "filename": doc.filename,
            "file_size": doc.file_size,
            "encryption": doc.encryption_algorithm,
            "created_at": doc.created_at,
            "access": {
                "can_read": True,
                "can_edit": (
                    True if is_owner
                    else permission.can_edit
                ),
                "can_download": (
                    True if is_owner
                    else permission.can_download
                ),
                "is_owner": is_owner,
            },
        })

    return {
        "total": len(items),
        "items": items,
    }
@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find document
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

    # Check ownership or administrator access
    is_owner = document.owner_id == current_user.id
    is_admin = current_user.role == "admin"

    if not is_owner and not is_admin:
        permission = (
            db.query(DocumentPermission)
            .filter(
                DocumentPermission.document_id == document.id,
                DocumentPermission.user_id == current_user.id,
                DocumentPermission.is_active.is_(True),
            )
            .first()
        )

        if (
            permission is None
            or not permission.can_read
            or not permission.can_download
        ):
            record_audit_event(
                db=db,
                user_id=current_user.id,
                document_id=document.id,
                action="ACCESS_DENIED",
                event_status="DENIED",
                ip_address=request.client.host if request.client else None,
                details="Download denied: insufficient document permissions",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to download this document",
            )

    # Resolve and validate the private storage path
    storage_root = STORAGE_DIR.resolve()
    encrypted_path = (
        storage_root / document.storage_path
    ).resolve()

    if encrypted_path.parent != storage_root:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid document storage path",
        )

    # Read encrypted document
    try:
        encrypted_data = encrypted_path.read_bytes()

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file not found",
        )

    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read stored document",
        )

    # Decrypt and verify authenticity
    try:
        original_data = decrypt_file(
            encrypted_data,
            document.nonce,
        )

    except InvalidTag:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document integrity verification failed",
        )

    # Return original document
    safe_filename = quote(
        document.filename,
        safe="",
    )
    record_audit_event(
    db=db,
    user_id=current_user.id,
    document_id=document.id,
    action="DOWNLOAD",
    event_status="SUCCESS",
    ip_address=request.client.host if request.client else None,
    details="Document downloaded successfully",
)
    return Response(
        content=original_data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f"attachment; filename*=UTF-8''{safe_filename}"
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
