import os,base64
os.environ.setdefault('API_TOKEN','test-token')
os.environ.setdefault('CREDENTIAL_ENCRYPTION_KEY',base64.urlsafe_b64encode(b'0'*32).decode())
