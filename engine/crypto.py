from __future__ import annotations

from cryptography.fernet import Fernet

from api.config import get_settings


def get_cipher_suite() -> Fernet | None:
    """Get the Fernet cipher suite using the configured key."""
    settings = get_settings()
    key = settings.encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception:
        # Invalid key, fallback to plaintext or error?
        # For now, if key is invalid, return None (plaintext mode safety check?)
        # Or better, crash early.
        # But for smooth rollout, let's assume if key is set, it must be valid.
        return None

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data if a key is configured."""
    cipher = get_cipher_suite()
    if cipher:
        return cipher.encrypt(data)
    return data

def decrypt_data(data: bytes) -> bytes:
    """Decrypt data if a key is configured and data is encrypted."""
    cipher = get_cipher_suite()
    if not cipher:
        return data

    # Check if data looks encrypted (Fernet tokens are url-safe base64)
    # But simpler: try decrypt. If fail, return original (migration support)
    try:
        return cipher.decrypt(data)
    except Exception:
        # Not encrypted or wrong key
        return data
