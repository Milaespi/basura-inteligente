"""
Lógica de negocio para subida de imágenes, inferencia YOLO,
historial con filtros y exportación CSV.
"""

import uuid
import csv
import io
import aiofiles
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.database import get_db
from app.models.image import ImageOut, ImageListItem
from app.services.yolo_service import run_inference
from app.utils.mongo_helpers import doc_to_dict, to_object_id
from app.config import get_settings

settings = get_settings()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _col():
    return get_db()["images"]


def _upload_dir(user_id: str) -> Path:
    p = Path(settings.UPLOAD_FOLDER) / user_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── Subir imagen y analizar ───────────────────────────────────────────────────

async def analyze_image(
    file: UploadFile,
    user_id: str,
    zona: Optional[str] = None,
    zona_detalle: Optional[str] = None,
) -> ImageOut:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se aceptan imágenes JPG, PNG o WEBP",
        )

    content = await file.read()
    if len(content) > settings.max_file_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La imagen supera el límite de {settings.MAX_FILE_SIZE_MB} MB",
        )

    ext      = Path(file.filename or "imagen.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = _upload_dir(user_id) / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    inference = run_inference(str(filepath))

    url           = f"/uploads/{user_id}/{filename}"
    ann_name      = Path(inference["annotated_path"]).name
    annotated_url = f"/uploads/{user_id}/annotated/{ann_name}"

    # Confianza máxima de todas las detecciones
    confs = [d["confianza"] for d in inference["detections"]]
    confianza_max = round(max(confs), 4) if confs else None

    doc = {
        "user_id":       user_id,
        "filename":      filename,
        "url":           url,
        "annotated_url": annotated_url,
        "zona":          zona,
        "zona_detalle":  zona_detalle,
        "detections":    inference["detections"],
        "resumen":       inference["resumen"],
        "confianza_max": confianza_max,
        "created_at":    datetime.now(timezone.utc),
    }
    result = _col().insert_one(doc)
    doc["_id"] = result.inserted_id
    return ImageOut(**doc_to_dict(doc))


# ── Historial con filtros ─────────────────────────────────────────────────────

def _build_date_filter(fecha: Optional[str]) -> Optional[dict]:
    """Convierte el parámetro 'fecha' en un filtro MongoDB."""
    now = datetime.now(timezone.utc)
    if fecha == "hoy":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif fecha == "semana":
        start = now - timedelta(days=7)
    elif fecha == "mes":
        start = now - timedelta(days=30)
    else:
        return None
    return {"$gte": start}


def get_user_history(
    user_id: str,
    limit: int = 20,
    skip: int = 0,
    categoria: Optional[str] = None,
    zona: Optional[str] = None,
    fecha: Optional[str] = None,
) -> list[ImageListItem]:
    query: dict = {"user_id": user_id}

    if categoria:
        query["resumen." + categoria] = {"$exists": True, "$gt": 0}

    if zona:
        query["zona"] = {"$regex": zona, "$options": "i"}

    date_filter = _build_date_filter(fecha)
    if date_filter:
        query["created_at"] = date_filter

    cursor = (
        _col()
        .find(query, {"detections": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [ImageListItem(**doc_to_dict(d)) for d in cursor]


def count_user_history(
    user_id: str,
    categoria: Optional[str] = None,
    zona: Optional[str] = None,
    fecha: Optional[str] = None,
) -> int:
    """Total de registros para la paginación del frontend."""
    query: dict = {"user_id": user_id}
    if categoria:
        query["resumen." + categoria] = {"$exists": True, "$gt": 0}
    if zona:
        query["zona"] = {"$regex": zona, "$options": "i"}
    date_filter = _build_date_filter(fecha)
    if date_filter:
        query["created_at"] = date_filter
    return _col().count_documents(query)


# ── Exportar historial como CSV ───────────────────────────────────────────────

def export_history_csv(
    user_id: str,
    categoria: Optional[str] = None,
    zona: Optional[str] = None,
    fecha: Optional[str] = None,
) -> str:
    """Retorna el historial como string CSV listo para descargar."""
    items = get_user_history(
        user_id, limit=10_000, skip=0,
        categoria=categoria, zona=zona, fecha=fecha,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Zona", "Detalle zona", "Aprovechable",
                     "No_aprovechable", "Orgánico", "Confianza máx.", "Fecha"])

    for item in items:
        writer.writerow([
            item.id,
            item.zona or "",
            item.zona_detalle or "",
            item.resumen.get("Aprovechable", 0),
            item.resumen.get("No_aprovechable", 0),
            item.resumen.get("Orgánico", 0),
            f"{item.confianza_max:.0%}" if item.confianza_max else "",
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return output.getvalue()


# ── Detalle de una imagen ─────────────────────────────────────────────────────

def get_image_detail(image_id: str, user_id: str) -> ImageOut:
    doc = _col().find_one({"_id": to_object_id(image_id), "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return ImageOut(**doc_to_dict(doc))


# ── Estadísticas globales ─────────────────────────────────────────────────────

def get_global_stats() -> dict:
    col = _col()

    # Totales por clase
    pipeline_clases = [
        {"$unwind": "$detections"},
        {"$group": {"_id": "$detections.clase", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    clase_counts = {r["_id"]: r["total"] for r in col.aggregate(pipeline_clases)}
    total_detecciones = sum(clase_counts.values())

    # Distribución porcentual
    distribucion = {
        clase: {
            "total": total,
            "porcentaje": round(total / total_detecciones * 100, 1) if total_detecciones else 0,
        }
        for clase, total in clase_counts.items()
    }

    # Detecciones por día — últimos 7 días
    hace_7_dias = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline_dias = [
        {"$match": {"created_at": {"$gte": hace_7_dias}}},
        {"$unwind": "$detections"},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at",
                        "timezone": "America/Bogota",
                    }
                },
                "total": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    detecciones_por_dia = [
        {"fecha": r["_id"], "total": r["total"]}
        for r in col.aggregate(pipeline_dias)
    ]

    # Métricas por clase (fijas del entrenamiento con YOLO11s)
    metricas_por_clase = {
        "Aprovechable":    {"precision": 0.963, "recall": 0.941, "f1": 0.952, "map50": 0.968, "muestras": 187},
        "No_aprovechable": {"precision": 0.921, "recall": 0.887, "f1": 0.904, "map50": 0.932, "muestras": 112},
        "Orgánico":        {"precision": 0.945, "recall": 0.912, "f1": 0.928, "map50": 0.951, "muestras": 61},
        "Promedio":        {"precision": 0.943, "recall": 0.913, "f1": 0.928, "map50": 0.950, "muestras": 360},
    }

    return {
        "total_imagenes_analizadas": col.count_documents({}),
        "total_detecciones":         total_detecciones,
        "distribucion_por_clase":    distribucion,
        "detecciones_por_dia":       detecciones_por_dia,
        "metricas_por_clase":        metricas_por_clase,
    }
