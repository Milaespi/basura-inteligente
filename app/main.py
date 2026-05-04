"""
Punto de entrada de la API.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Identificación de Basuras Inteligentes
 Fundacion Universitaria Católica Lumen Gentium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import get_client, close_connection
from app.routes import auth, detections, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s → %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Ciclo de vida ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando servidor…")
    get_client()                                        # Conectar MongoDB
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True) # Carpeta de uploads
    yield
    close_connection()
    logger.info("👋 Servidor detenido")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Identificación de Basuras Inteligentes",
    description=(
        "API REST para clasificación de residuos con **YOLO11s**.\n\n"
        "Proyecto de la **Fundacion Universitaria Católica Lumen Gentium**.\n\n"
        "### Clases detectadas\n"
        "- `Aprovechable` — residuos reciclables\n"
        "- `No_aprovechable` — residuos no reciclables\n"
        "- `Orgánico` — residuos orgánicos (`Organico` del dataset se normaliza automáticamente)\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Archivos estáticos (imágenes subidas) ─────────────────────────────────────

os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_FOLDER),
    name="uploads",
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(detections.router)
app.include_router(admin.router)


# ── Endpoints de salud ────────────────────────────────────────────────────────

@app.get("/", tags=["Estado"], summary="Información del proyecto")
def root():
    return {
        "proyecto":    "Identificación de Basuras Inteligentes",
        "universidad": "Fundacion Universitaria Católica Lumen Gentium",
        "version":     "1.0.0",
        "estado":      "activo",
        "docs":        "/docs",
    }


@app.get("/health", tags=["Estado"], summary="Health check")
def health():
    return {"status": "ok"}
