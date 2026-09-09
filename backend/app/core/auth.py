import secrets
from fastapi import Header, HTTPException
from app.core.config import settings

async def require_api_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    if not secrets.compare_digest(token, settings.api_token.get_secret_value()):
        raise HTTPException(status_code=401, detail="Authentication required")
