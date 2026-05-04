"""
Esquemas Pydantic para imágenes analizadas.

Colección MongoDB 'images':
  _id, user_id, filename, url, annotated_url,
  zona, zona_detalle, detections, resumen, created_at
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DetectionItem(BaseModel):
    """Un objeto detectado por YOLO."""
    clase: str
    confianza: float = Field(..., ge=0.0, le=1.0)
    bbox: list[float]           # [x1, y1, x2, y2] normalizados [0, 1]


class ImageOut(BaseModel):
    id: str
    user_id: str
    filename: str
    url: str
    annotated_url: Optional[str] = None
    zona: Optional[str] = None          # ej: "Cafetería central"
    zona_detalle: Optional[str] = None  # ej: "Edificio principal"
    detections: list[DetectionItem]
    resumen: dict[str, int]
    created_at: datetime


class ImageListItem(BaseModel):
    """Versión resumida para el historial."""
    id: str
    filename: str
    url: str
    annotated_url: Optional[str] = None
    zona: Optional[str] = None
    zona_detalle: Optional[str] = None
    resumen: dict[str, int]
    confianza_max: Optional[float] = None   # confianza más alta de la imagen
    created_at: datetime


class HistorialFilters(BaseModel):
    """Filtros opcionales para el historial."""
    categoria: Optional[str] = None   # Aprovechable | No_aprovechable | Orgánico
    zona: Optional[str] = None
    fecha: Optional[str] = None       # "hoy" | "semana" | "mes"
