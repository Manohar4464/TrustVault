
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from cryptography.exceptions import InvalidTag
from botocore.exceptions import BotoCoreError, ClientError

from app.core.database import get_db
from app.core.storage import (
    save_encrypted_file,
    read_encrypted_file,
    delete_encrypted_file,
)
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.routers.auth import get_current_user
from app.services.encryption import encrypt_file, decrypt_file


router = APIRouter(prefix="/documents", tags=["Documents"])
@router.get("/")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document)

    if current_user.role == "admin":
        documents = query.order_by(Document.created_at.desc()).all()

    else:
        documents = (
            query.outerjoin(
                DocumentPermission,
                (DocumentPermission.document_id == Document.id)
                & (DocumentPermission.user_id == current_user.id)
                & (DocumentPermission.is_active.is_(True))
                & (DocumentPermission.can_read.is_(True)),
            )
            .filter(
                (Document.owner_id == current_user.id)
                | (DocumentPermission.id.isnot(None))
            )
            .distinct()
            .order_by(Document.created_at.desc())
            .all()
        )

    return [
        {
            "id": str(document.id),
            "filename": document.filename,
            "file_size": document.file_size,
            "encryption_algorithm": document.encryption_algorithm,
            "created_at": document.created_at,
            "owner_id": str(document.owner_id),
        }
        for document in documents
    ]
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
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to upload documents",
        )

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

    # Encrypt before uploading to R2.
    encrypted_data, nonce = encrypt_file(data)

    storage_filename = f"{uuid.uuid4()}.enc"
    storage_saved = False

    try:
        save_encrypted_file(storage_filename, encrypted_data)
        storage_saved = True

        document = Document(
            filename=original_filename,
            storage_path=storage_filename,
            owner_id=current_user.id,
            file_size=len(data),
            nonce=nonce,
            encryption_algorithm="AES-256-GCM",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

    except (SQLAlchemyError, OSError, BotoCoreError, ClientError):
        db.rollback()

        if storage_saved:
            try:
                delete_encrypted_file(storage_filename)
            except Exception:
                pass

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


@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to download this document",
            )

    try:
        encrypted_data = read_encrypted_file(document.storage_path)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file not found",
        )

    except (OSError, BotoCoreError, ClientError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read stored document",
        )

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

    safe_filename = quote(document.filename, safe="")

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
