"""Helpers para trabajar con documentos MongoDB."""

from bson import ObjectId
from fastapi import HTTPException


def doc_to_dict(doc: dict) -> dict:
    """Convierte _id (ObjectId) → id (str) para serializar con Pydantic."""
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail=f"ID inválido: {id_str}")
