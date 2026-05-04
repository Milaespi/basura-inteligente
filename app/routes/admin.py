"""
Rutas de administración (solo rol 'admin'):
  GET /api/admin/users  → listar todos los usuarios
"""

from fastapi import APIRouter, Depends

from app.models.user import UserOut, TokenData
from app.services.auth_service import list_users
from app.middleware.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["Administración"])


@router.get("/users", response_model=list[UserOut],
            summary="Listar todos los usuarios")
def get_all_users(_: TokenData = Depends(require_admin)):
    return list_users()
