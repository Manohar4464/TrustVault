import os
import base64
import binascii

from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


load_dotenv()

KEY_SIZE = 32
NONCE_SIZE = 12


def get_encryption_key() -> bytes:
    """Load and validate the persistent AES-256 key."""

    encoded_key = os.getenv("AES_ENCRYPTION_KEY")

    if not encoded_key:
        raise RuntimeError("AES_ENCRYPTION_KEY is missing")

    try:
        key = base64.b64decode(encoded_key, validate=True)
    except (binascii.Error, ValueError):
        raise RuntimeError("AES_ENCRYPTION_KEY is not valid Base64")

    if len(key) != KEY_SIZE:
        raise RuntimeError("AES-256 requires a 32-byte key")

    return key


def encrypt_file(data: bytes, key: bytes = None) -> tuple[bytes, bytes]:
    """Encrypt document bytes using AES-256-GCM."""

    if key is None:
        key = get_encryption_key()

    if len(key) != KEY_SIZE:
        raise ValueError("AES-256 requires a 32-byte key")

    nonce = os.urandom(NONCE_SIZE)

    aesgcm = AESGCM(key)

    encrypted_data = aesgcm.encrypt(
        nonce,
        data,
        None
    )

    return encrypted_data, nonce


def decrypt_file(
    encrypted_data: bytes,
    nonce: bytes,
    key: bytes = None
) -> bytes:
    """Decrypt document bytes and verify authenticity."""

    if key is None:
        key = get_encryption_key()

    if len(key) != KEY_SIZE:
        raise ValueError("AES-256 requires a 32-byte key")

    if len(nonce) != NONCE_SIZE:
        raise ValueError("Invalid nonce length")

    aesgcm = AESGCM(key)

    return aesgcm.decrypt(
        nonce,
        encrypted_data,
        None
    )