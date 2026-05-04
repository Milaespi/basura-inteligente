"""
Tests básicos de la API.
Ejecutar:  pytest tests/ -v
"""

import os
import pytest

# Variables mínimas para que la app arranque sin .env real
os.environ.setdefault("MONGO_URI",   "mongodb://localhost:27017")
os.environ.setdefault("SECRET_KEY",  "clave_de_test_no_usar_en_produccion")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_contiene_proyecto():
    r = client.get("/")
    assert r.status_code == 200
    assert "Basuras" in r.json()["proyecto"]


def test_login_sin_body_retorna_422():
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 422


def test_register_email_invalido():
    r = client.post("/api/auth/register", json={
        "nombre": "Test", "email": "no-es-email", "password": "123456"
    })
    assert r.status_code == 422


def test_rutas_protegidas_requieren_token():
    for path in ["/api/auth/me", "/api/detections/history", "/api/admin/users"]:
        r = client.get(path)
        assert r.status_code == 401, f"Se esperaba 401 en {path}"
