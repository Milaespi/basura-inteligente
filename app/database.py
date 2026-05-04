"""
Conexión única a MongoDB (patrón singleton).
Usar get_db() para obtener la base de datos en cualquier parte del proyecto.
"""

from pymongo import MongoClient
from pymongo.database import Database
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.MONGO_URI)
        logger.info("✅ Conexión a MongoDB establecida")
    return _client


def get_db() -> Database:
    settings = get_settings()
    return get_client()[settings.MONGO_DB_NAME]


def close_connection():
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("🔌 Conexión a MongoDB cerrada")
