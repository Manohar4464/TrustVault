
from pathlib import Path

from app.core.database import SessionLocal
from app.core.storage import read_encrypted_file
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

    # Read encrypted document from local storage or R2.
    encrypted_data = read_encrypted_file(document.storage_path)

    decrypted_data = decrypt_file(
        encrypted_data,
        document.nonce
    )

    original_path = Path("test_document.txt")
    original_data = original_path.read_bytes()

    print("Database metadata: PASSED")
    print("Encrypted file retrieved: PASSED")
    print("Decryption: PASSED")
    print(
        "Original file comparison:",
        "PASSED" if decrypted_data == original_data else "FAILED"
    )

finally:
    db.close()
