"""
Utilidades de seguridad: hash de contraseñas con bcrypt y tokens JWT.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.user import TokenData

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Contraseñas ───────────────────────────────────────────────────────────────

def _prepare(plain: str) -> str:
    # bcrypt tiene límite de 72 bytes; se pre-hashea con SHA-256 para evitarlo
    return hashlib.sha256(plain.encode()).hexdigest()


def hash_password(plain: str) -> str:
    return pwd_context.hash(_prepare(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_prepare(plain), hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> TokenData:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise exc
        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            rol=payload.get("rol"),
        )
    except JWTError:
        raise exc
