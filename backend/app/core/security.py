import base64, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings

def _key() -> bytes:
    try:
        raw = base64.urlsafe_b64decode(settings.credential_encryption_key.get_secret_value().encode())
    except Exception as exc:
        raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY is not valid base64") from exc
    if len(raw) != 32:
        raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must decode to 32 bytes")
    return raw

def encrypt_secret(value: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key()).encrypt(nonce, value.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()

def decrypt_secret(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    if len(raw) < 28:
        raise RuntimeError("Encrypted credential is invalid")
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], None).decode()
