# services/crypto_utils.py
import os
from cryptography.fernet import Fernet, InvalidToken

_MASTER_KEY = os.getenv("FERNET_MASTER_KEY")
if not _MASTER_KEY:
    raise RuntimeError("FERNET_MASTER_KEY not set in environment")

# Ensure bytes
fernet = Fernet(_MASTER_KEY.encode() if isinstance(_MASTER_KEY, str) else _MASTER_KEY)

def encrypt_text(plaintext: str) -> str:
    """Return base64-encoded token string safe for storing in TEXT."""
    if plaintext is None:
        return None
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_text(token: str) -> str:
    """Decrypt token and return plaintext string. Raises InvalidToken on failure."""
    if token is None:
        return None
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        # Don't leak sensitive info in logs
        raise
