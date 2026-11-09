
from pathlib import Path

from app.core.database import SessionLocal
from app.core.storage import STORAGE_DIR
from app.models.document import Document
from app.services.encryption import decrypt_file

db = SessionLocal()

try:
    document = (
        db.query(Document)
        .filter(Document.filename == "test_document.txt")
        .order_by(Document.created_at.desc())
        .first()
    )

    if document is None:
        raise RuntimeError("Uploaded document not found in database")

    encrypted_path = (STORAGE_DIR / document.storage_path).resolve()

    if encrypted_path.parent != STORAGE_DIR.resolve():
        raise RuntimeError("Invalid storage path")

    encrypted_data = encrypted_path.read_bytes()

    decrypted_data = decrypt_file(
        encrypted_data,
        document.nonce
    )

    original_path = Path("test_document.txt")
    original_data = original_path.read_bytes()

    print("Database metadata: PASSED")
    print("Encrypted file found: PASSED")
    print("Decryption: PASSED")
    print(
        "Original file comparison:",
        "PASSED" if decrypted_data == original_data else "FAILED"
    )

finally:
    db.close()
