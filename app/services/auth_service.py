"""
Lógica de negocio para autenticación y gestión de usuarios.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.database import get_db
from app.models.user import UserRegister, UserLogin, UserOut, Token
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.mongo_helpers import doc_to_dict, to_object_id


def _col():
    return get_db()["users"]


# ── Registro ──────────────────────────────────────────────────────────────────

def register_user(data: UserRegister) -> UserOut:
    col = _col()

    if col.find_one({"email": data.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese correo electrónico",
        )

    doc = {
        "nombre": data.nombre,
        "email": data.email,
        "password": hash_password(data.password),
        "rol": "user",
        "created_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return UserOut(**doc_to_dict(doc))


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(data: UserLogin) -> Token:
    col = _col()
    user = col.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"],
        "rol": user["rol"],
    })
    return Token(access_token=token)


# ── Perfil ────────────────────────────────────────────────────────────────────

def get_user_by_id(user_id: str) -> UserOut:
    doc = _col().find_one({"_id": to_object_id(user_id)}, {"password": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserOut(**doc_to_dict(doc))


# ── Listar (admin) ────────────────────────────────────────────────────────────

def list_users() -> list[UserOut]:
    return [UserOut(**doc_to_dict(d)) for d in _col().find({}, {"password": 0})]
