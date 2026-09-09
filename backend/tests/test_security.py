import base64
from app.core import security

def test_roundtrip(monkeypatch):
    key=base64.urlsafe_b64encode(b'k'*32).decode()
    class Secret:
        def get_secret_value(self): return key
    monkeypatch.setattr(security.settings,'credential_encryption_key',Secret(),raising=False)
    assert security.decrypt_secret(security.encrypt_secret('secret'))=='secret'
