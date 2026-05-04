"""
Dependencias de FastAPI para proteger rutas con JWT.

Uso en cualquier ruta:
    current_user: TokenData = Depends(get_current_user)
    admin_user:   TokenData = Depends(require_admin)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.utils.security import decode_access_token
from app.models.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Valida el JWT y retorna los datos del usuario autenticado."""
    return decode_access_token(token)


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Solo permite acceso a usuarios con rol 'admin'."""
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user
