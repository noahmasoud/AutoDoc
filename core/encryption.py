"""Encryption utilities for sensitive data storage.

Implements NFR-9: Never store tokens unencrypted.
Uses Fernet symmetric encryption with the application secret key.
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.config import settings


def _derive_key(secret_key: str, salt: bytes) -> bytes:
    """Derive encryption key from secret key using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key_material = kdf.derive(secret_key.encode())
    # Fernet requires URL-safe base64-encoded key
    return base64.urlsafe_b64encode(key_material)


# Use a fixed salt for consistent encryption (in production, consider using a salt per connection)
_SALT = b"autodoc_connection_token_salt"  # Fixed salt for this use case


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for storage.

    Args:
        token: Plain text token to encrypt

    Returns:
        Encrypted token as base64 string

    Raises:
        ValueError: If token is empty or secret key is invalid
    """
    if not token:
        raise ValueError("Token cannot be empty")

    key = _derive_key(settings.SECRET_KEY, _SALT)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(token.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored token.

    Args:
        encrypted_token: Base64 encoded encrypted token

    Returns:
        Decrypted plain text token

    Raises:
        ValueError: If decryption fails (invalid token or key)
    """
    if not encrypted_token:
        raise ValueError("Encrypted token cannot be empty")

    try:
        # The encrypted_token is already base64-encoded from encrypt_token
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
        key = _derive_key(settings.SECRET_KEY, _SALT)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt token: {e!s}") from e
