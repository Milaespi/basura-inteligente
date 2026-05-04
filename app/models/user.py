"""
Esquemas Pydantic para usuarios.

Colección MongoDB 'users':
  _id, nombre, email (único), password (hash), rol, created_at
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ── Entrada ───────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Juan Pérez"])
    email: EmailStr = Field(..., examples=["juan@unicatolicacali.edu.co"])
    password: str = Field(..., min_length=6, examples=["mi_contraseña"])


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── Salida  (nunca exponer la contraseña) ─────────────────────────────────────

class UserOut(BaseModel):
    id: str
    nombre: str
    email: str
    rol: str
    created_at: datetime


# ── JWT ───────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None
