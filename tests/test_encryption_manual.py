from cryptography.exceptions import InvalidTag

from app.services.encryption import (
    encrypt_file,
    decrypt_file,
    get_encryption_key
)


# Load the persistent key
key = get_encryption_key()

print("Key configuration: PASSED")

# Sample document
original = b"This is a confidential TrustVault document."

# Encrypt using the persistent key
encrypted, nonce = encrypt_file(original)

print("Encryption: PASSED")

# Decrypt using the same persistent key
decrypted = decrypt_file(encrypted, nonce)

print("Decryption:", "PASSED" if decrypted == original else "FAILED")

# Test tampering
tampered = bytearray(encrypted)
tampered[0] ^= 1

try:
    decrypt_file(bytes(tampered), nonce)
    print("Tampering detection: FAILED")

except InvalidTag:
    print("Tampering detection: PASSED")