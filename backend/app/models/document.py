
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):

    __tablename__ = "documents"

    # Unique document ID
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Original document filename
    filename = Column(
        String(255),
        nullable=False
    )

    # Path of encrypted file
    storage_path = Column(
        String(500),
        nullable=False,
        unique=True
    )

    # Document owner
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Original file size
    file_size = Column(
        BigInteger,
        nullable=False
    )

    # AES-GCM nonce (12 bytes)
    nonce = Column(
        LargeBinary(12),
        nullable=False
    )

    # Encryption algorithm
    encryption_algorithm = Column(
        String(50),
        nullable=False,
        default="AES-256-GCM"
    )

    # Date and time of upload
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
