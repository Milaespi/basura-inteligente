"""
Crea el usuario administrador inicial.
Ejecutar:  python scripts/create_admin.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone
from app.database import get_db
from app.utils.security import hash_password


def main():
    db = get_db()
    col = db["users"]

    print("=== Crear usuario administrador ===")
    email    = input("Email:       ").strip()
    nombre   = input("Nombre:      ").strip()
    password = input("Contraseña:  ").strip()

    if col.find_one({"email": email}):
        print(f"⚠️  Ya existe un usuario con el email '{email}'")
        return

    col.insert_one({
        "nombre":     nombre,
        "email":      email,
        "password":   hash_password(password),
        "rol":        "admin",
        "created_at": datetime.now(timezone.utc),
    })
    print(f"\n✅ Admin '{email}' creado correctamente")


if __name__ == "__main__":
    main()
