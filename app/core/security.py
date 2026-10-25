from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from app.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
password_hash = PasswordHash.recommended()

def hash_password(value: str) -> str: return password_hash.hash(value)
def verify_password(value: str, hashed: str) -> bool: return password_hash.verify(value, hashed)

def create_access_token(subject: str, role: str) -> str:
    s = get_settings()
    payload = {"sub": subject, "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=s.access_token_expire_minutes)}
    return jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm)

def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
    s = get_settings()
    try: return jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
    except jwt.PyJWTError as exc: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

def require_roles(*roles: str):
    def guard(payload: Annotated[dict[str, str], Depends(decode_token)]) -> dict[str, str]:
        if payload.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return payload
    return guard
