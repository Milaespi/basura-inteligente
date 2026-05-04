"""
Servicio de inferencia YOLO11s.
El modelo se carga UNA SOLA VEZ en memoria (singleton) al primer uso.

Clases del modelo (raw):
  0 → Aprovechable
  1 → No_aprovechable
  2 → Orgánico
  3 → Organico   ← variante sin tilde del dataset, se normaliza a "Orgánico"

Clases expuestas por la API (3 clases reales):
  Aprovechable · No_aprovechable · Orgánico
"""

import logging
import zipfile
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# Normalización: unifica las 4 etiquetas del dataset en 3 clases reales
_CLASS_NORMALIZE: dict[str, str] = {
    "Organico": "Orgánico",   # variante sin tilde → nombre canónico
}

def normalize_class(name: str) -> str:
    """Retorna el nombre canónico de la clase (corrige variantes del dataset)."""
    return _CLASS_NORMALIZE.get(name, name)


# Rutas
_MODEL_DIR = Path(__file__).parent.parent / "ml_model"
_MODEL_PT  = Path(__file__).parent.parent / "ml_model_cached.pt"

_model: YOLO | None = None


def _build_pt() -> Path:
    """
    El modelo viene en formato torch.save descomprimido (carpeta).
    Lo reempaqueta en un archivo .pt estándar que Ultralytics puede leer.
    Solo se hace una vez; luego reutiliza el .pt en caché.
    """
    if _MODEL_PT.exists():
        return _MODEL_PT

    logger.info("📦 Empaquetando modelo a .pt por primera vez…")
    with zipfile.ZipFile(_MODEL_PT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fp in _MODEL_DIR.rglob("*"):
            if fp.is_file():
                arcname = "ml_model/" + fp.relative_to(_MODEL_DIR).as_posix()
                info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
                zf.writestr(info, fp.read_bytes())

    logger.info(f"✅ Modelo empaquetado en {_MODEL_PT}")
    return _MODEL_PT


def get_model() -> YOLO:
    """Retorna la instancia YOLO cargada (singleton)."""
    global _model
    if _model is None:
        pt = _build_pt()
        _model = YOLO(pt, task="detect")
        logger.info(f"🤖 YOLO11s listo. Clases normalizadas: {['Aprovechable', 'No_aprovechable', 'Orgánico']}")
    return _model


# ── Inferencia ────────────────────────────────────────────────────────────────

def run_inference(image_path: str, conf: float = 0.25) -> dict:
    """
    Ejecuta YOLO sobre una imagen y genera la versión anotada.

    Retorna:
    {
      "detections":     [{"clase": str, "confianza": float, "bbox": [x1,y1,x2,y2]}],
      "resumen":        {"Aprovechable": 2, "Orgánico": 1, ...},
      "annotated_path": "/ruta/a/imagen_anotada.jpg"
    }
    Las clases ya vienen normalizadas (Organico → Orgánico).
    """
    model = get_model()
    results = model.predict(source=image_path, conf=conf, save=False, verbose=False)

    detections: list[dict] = []
    resumen: dict[str, int] = {}
    annotated_path = image_path   # fallback si no hay detecciones

    for result in results:
        for box in result.boxes:
            cls_id    = int(box.cls[0])
            clase     = normalize_class(model.names[cls_id])   # ← normalización aquí
            confianza = round(float(box.conf[0]), 4)
            x1, y1, x2, y2 = [round(v, 6) for v in box.xyxyn[0].tolist()]

            detections.append({"clase": clase, "confianza": confianza,
                                "bbox": [x1, y1, x2, y2]})
            resumen[clase] = resumen.get(clase, 0) + 1

        # Guardar imagen anotada junto a la original
        ann_dir = Path(image_path).parent / "annotated"
        ann_dir.mkdir(parents=True, exist_ok=True)
        annotated_path = str(ann_dir / (Path(image_path).stem + "_ann.jpg"))
        cv2.imwrite(annotated_path, result.plot())

    return {
        "detections": detections,
        "resumen": resumen,
        "annotated_path": annotated_path,
    }
