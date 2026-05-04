"""
Rutas de autenticación:
  POST /api/auth/register  → crear cuenta
  POST /api/auth/login     → iniciar sesión → JWT
  GET  /api/auth/me        → perfil del usuario autenticado
"""

from fastapi import APIRouter, Depends

from app.models.user import UserRegister, UserLogin, UserOut, Token, TokenData
from app.services.auth_service import register_user, login_user, get_user_by_id
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=201,
             summary="Registrar nueva cuenta")
def register(data: UserRegister):
    return register_user(data)


@router.post("/login", response_model=Token,
             summary="Iniciar sesión y obtener JWT")
def login(data: UserLogin):
    return login_user(data)


@router.get("/me", response_model=UserOut,
            summary="Ver mi perfil")
def me(current_user: TokenData = Depends(get_current_user)):
    return get_user_by_id(current_user.user_id)
