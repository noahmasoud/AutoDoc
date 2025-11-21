"""Token encryption utilities for secure storage (NFR-9)."""

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
    return base64.urlsafe_b64encode(key_material)


_SALT = b"autodoc_connection_token_salt"


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for secure storage.
    
    Args:
        token: Plaintext token to encrypt
        
    Returns:
        Base64-encoded encrypted token
    """
    key = _derive_key(settings.SECRET_KEY, _SALT)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(token.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored token.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
        
    Returns:
        Decrypted plaintext token
    """
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
    key = _derive_key(settings.SECRET_KEY, _SALT)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()

