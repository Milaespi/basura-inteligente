"""
Rutas de detección de basuras:
  POST /api/detections/analyze            → subir imagen y detectar
  GET  /api/detections/history            → historial con filtros y paginación
  GET  /api/detections/history/export     → exportar historial como CSV
  GET  /api/detections/stats/global       → estadísticas completas
  GET  /api/detections/{id}               → detalle de una imagen
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from app.models.image import ImageOut, ImageListItem
from app.models.user import TokenData
from app.services.image_service import (
    analyze_image,
    get_user_history,
    count_user_history,
    export_history_csv,
    get_image_detail,
    get_global_stats,
)
from app.middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/detections", tags=["Detecciones"])


@router.post("/analyze", response_model=ImageOut, status_code=201,
             summary="Analizar imagen con YOLO11s")
async def analyze(
    file: UploadFile = File(..., description="Imagen JPG/PNG/WEBP"),
    zona: Optional[str] = Form(None, description="Nombre de la zona (ej: Cafetería central)"),
    zona_detalle: Optional[str] = Form(None, description="Detalle de la zona (ej: Edificio principal)"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Recibe una imagen y campos opcionales de zona.
    Ejecuta YOLO11s y retorna detecciones + imagen anotada.
    """
    return await analyze_image(file, current_user.user_id, zona, zona_detalle)


@router.get("/history", response_model=dict, summary="Historial con filtros y paginación")
def history(
    limit:     int            = Query(20,   ge=1, le=100),
    skip:      int            = Query(0,    ge=0),
    categoria: Optional[str]  = Query(None, description="Aprovechable | No_aprovechable | Orgánico"),
    zona:      Optional[str]  = Query(None, description="Buscar por zona (parcial)"),
    fecha:     Optional[str]  = Query(None, description="hoy | semana | mes"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Retorna el historial paginado con el total de registros para que
    el frontend pueda construir la paginación.
    """
    items = get_user_history(
        current_user.user_id, limit=limit, skip=skip,
        categoria=categoria, zona=zona, fecha=fecha,
    )
    total = count_user_history(
        current_user.user_id,
        categoria=categoria, zona=zona, fecha=fecha,
    )
    return {
        "total":  total,
        "skip":   skip,
        "limit":  limit,
        "items":  [i.model_dump() for i in items],
    }


@router.get("/history/export", summary="Exportar historial como CSV")
def export_csv(
    categoria: Optional[str] = Query(None),
    zona:      Optional[str] = Query(None),
    fecha:     Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
):
    """Descarga el historial filtrado en formato CSV."""
    csv_content = export_history_csv(
        current_user.user_id,
        categoria=categoria, zona=zona, fecha=fecha,
    )
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=historial_basuras.csv"},
    )


@router.get("/stats/global", summary="Estadísticas completas del modelo")
def stats(current_user: TokenData = Depends(get_current_user)):
    """
    Retorna:
    - Total de imágenes analizadas y detecciones
    - Distribución y porcentaje por clase
    - Detecciones por día (últimos 7 días)
    - Métricas del modelo por clase (Precisión, Recall, F1, mAP@0.5)
    """
    return get_global_stats()


@router.get("/{image_id}", response_model=ImageOut,
            summary="Detalle completo de una detección")
def detail(
    image_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    return get_image_detail(image_id, current_user.user_id)
