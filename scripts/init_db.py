"""
Inicializa los índices necesarios en MongoDB.
Ejecutar UNA VEZ después de configurar el .env:

    python scripts/init_db.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from pymongo import ASCENDING, DESCENDING, TEXT
from app.database import get_db


def main():
    db = get_db()

    # users: email único
    db["users"].create_index([("email", ASCENDING)], unique=True)
    print("✅ Índice único en users.email")

    # images: consultas por usuario ordenadas por fecha
    db["images"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    print("✅ Índice compuesto en images.(user_id, created_at)")

    # images: filtro por zona (búsqueda de texto)
    db["images"].create_index([("zona", TEXT)])
    print("✅ Índice de texto en images.zona")

    # images: filtro por categoría (campo dinámico del resumen)
    for clase in ["Aprovechable", "No_aprovechable", "Orgánico"]:
        db["images"].create_index([(f"resumen.{clase}", ASCENDING)])
    print("✅ Índices de resumen por clase")

    print("\n🎉 Base de datos lista")


if __name__ == "__main__":
    main()
