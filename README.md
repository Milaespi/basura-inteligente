---
title: Identificacion de Basuras Inteligentes
emoji: 🗑️
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# 🗑️ Identificación de Basuras Inteligentes — Backend

**Fundacion Universitaria Católica Lumen Gentium**

API REST construida con **FastAPI** · **YOLO11s** · **MongoDB Atlas**

---

## 📁 Estructura del proyecto

```
basuras-backend/
├── app/
│   ├── main.py                  ← Punto de entrada FastAPI
│   ├── config.py                ← Configuración desde .env
│   ├── database.py              ← Conexión MongoDB (singleton)
│   ├── ml_model/                ← Modelo YOLO11s entrenado
│   ├── routes/
│   │   ├── auth.py              ← /api/auth/*
│   │   ├── detections.py        ← /api/detections/*
│   │   └── admin.py             ← /api/admin/*
│   ├── services/
│   │   ├── auth_service.py      ← Registro, login, perfil
│   │   ├── image_service.py     ← Subida, inferencia, historial, CSV, estadísticas
│   │   └── yolo_service.py      ← Carga del modelo e inferencia
│   ├── models/
│   │   ├── user.py              ← Esquemas Pydantic de usuario
│   │   └── image.py             ← Esquemas Pydantic de imágenes
│   ├── middleware/
│   │   └── auth.py              ← Dependencias JWT para rutas
│   └── utils/
│       ├── security.py          ← bcrypt + JWT
│       └── mongo_helpers.py     ← Helpers para ObjectId
├── scripts/
│   ├── init_db.py               ← Crea índices en MongoDB
│   └── create_admin.py          ← Crea el primer administrador
├── tests/
│   └── test_api.py              ← Tests con pytest
├── uploads/                     ← Imágenes subidas (creada automáticamente)
├── .env                         ← Variables de entorno (NO subir a git)
├── .env.example                 ← Plantilla de variables
├── .gitignore
└── requirements.txt
```

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd basuras-backend
```

### 2. Crear y activar entorno virtual
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
```
Editar `.env`:
```env
MONGO_URI=mongodb+srv://admin:TU_PASSWORD@cluster0.h8elraf.mongodb.net/?appName=Cluster0
SECRET_KEY=genera_con: python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Inicializar índices en MongoDB
```bash
python scripts/init_db.py
```

### 6. Crear usuario administrador
```bash
python scripts/create_admin.py
```

### 7. Arrancar el servidor
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📖 Documentación interactiva

| URL | Descripción |
|-----|-------------|
| http://localhost:8000/docs | **Swagger UI** — probar todos los endpoints |
| http://localhost:8000/redoc | ReDoc |

---

## 🔌 Endpoints

### Autenticación — `/api/auth`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|:----:|
| `POST` | `/register` | Crear cuenta | — |
| `POST` | `/login` | Iniciar sesión → JWT | — |
| `GET` | `/me` | Ver mi perfil | ✅ |

---

### Detecciones — `/api/detections`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|:----:|
| `POST` | `/analyze` | Subir imagen y detectar | ✅ |
| `GET` | `/history` | Historial con filtros y paginación | ✅ |
| `GET` | `/history/export` | Exportar historial como CSV | ✅ |
| `GET` | `/stats/global` | Estadísticas completas del modelo | ✅ |
| `GET` | `/{id}` | Detalle de una detección | ✅ |

#### POST `/analyze` — subir imagen
Usa `multipart/form-data`:

| Campo | Tipo | Requerido | Descripción |
|-------|------|:---------:|-------------|
| `file` | archivo | ✅ | Imagen JPG/PNG/WEBP |
| `zona` | texto | — | Nombre del lugar (ej: "Cafetería central") |
| `zona_detalle` | texto | — | Detalle (ej: "Edificio principal") |

**Respuesta:**
```json
{
  "id": "...",
  "url": "/uploads/{user_id}/imagen.jpg",
  "annotated_url": "/uploads/{user_id}/annotated/imagen_ann.jpg",
  "zona": "Cafetería central",
  "zona_detalle": "Edificio principal",
  "detections": [
    {"clase": "Aprovechable", "confianza": 0.91, "bbox": [0.1, 0.2, 0.5, 0.8]}
  ],
  "resumen": {"Aprovechable": 1},
  "created_at": "2025-01-01T14:32:00Z"
}
```

#### GET `/history` — historial con filtros
Query params opcionales:

| Param | Valores | Descripción |
|-------|---------|-------------|
| `limit` | 1–100 (default 20) | Registros por página |
| `skip` | ≥0 | Registros a omitir |
| `categoria` | `Aprovechable` \| `No_aprovechable` \| `Orgánico` | Filtrar por clase |
| `zona` | texto libre | Buscar por zona (parcial) |
| `fecha` | `hoy` \| `semana` \| `mes` | Filtrar por período |

**Respuesta:**
```json
{
  "total": 360,
  "skip": 0,
  "limit": 20,
  "items": [...]
}
```

#### GET `/history/export` — CSV
Acepta los mismos filtros que `/history`.
Descarga un archivo `historial_basuras.csv` con columnas:
`ID, Zona, Detalle zona, Aprovechable, No_aprovechable, Orgánico, Confianza máx., Fecha`

#### GET `/stats/global` — estadísticas
```json
{
  "total_imagenes_analizadas": 360,
  "total_detecciones": 360,
  "distribucion_por_clase": {
    "Aprovechable":    {"total": 187, "porcentaje": 52.0},
    "No_aprovechable": {"total": 112, "porcentaje": 31.0},
    "Orgánico":        {"total": 61,  "porcentaje": 17.0}
  },
  "detecciones_por_dia": [
    {"fecha": "2025-01-01", "total": 45},
    ...
  ],
  "metricas_por_clase": {
    "Aprovechable":    {"precision": 0.963, "recall": 0.941, "f1": 0.952, "map50": 0.968, "muestras": 187},
    "No_aprovechable": {"precision": 0.921, "recall": 0.887, "f1": 0.904, "map50": 0.932, "muestras": 112},
    "Orgánico":        {"precision": 0.945, "recall": 0.912, "f1": 0.928, "map50": 0.951, "muestras": 61},
    "Promedio":        {"precision": 0.943, "recall": 0.913, "f1": 0.928, "map50": 0.950, "muestras": 360}
  }
}
```

---

### Administración — `/api/admin`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|:----:|
| `GET` | `/users` | Listar todos los usuarios | ✅ Admin |

---

## 🏷️ Clases del modelo YOLO11s

| Clase | Color sugerido | Descripción |
|-------|:--------------:|-------------|
| `Aprovechable` | 🟢 verde | Plástico, papel, cartón, vidrio, metal, textiles |
| `No_aprovechable` | 🔴 rojo | Papel higiénico, colillas, icopor, envases sucios |
| `Orgánico` | 🟡 amarillo | Restos de comida, cáscaras, residuos de jardín |

> El modelo internamente tiene la etiqueta `Organico` (sin tilde). El backend la normaliza automáticamente a `Orgánico`.

---

## 🧪 Tests
```bash
pytest tests/ -v
```

---

## 🔐 Seguridad
- Contraseñas hasheadas con **bcrypt**
- Autenticación con **JWT** (expira en 60 min)
- Credenciales en `.env` — nunca en el código
- `.env` está en `.gitignore`

---

## 🤝 Para el Frontend

### Flujo de autenticación
1. `POST /api/auth/login` → guardar `access_token`
2. Cada petición: header `Authorization: Bearer <token>`

### Flujo de análisis
1. `POST /api/detections/analyze` con `multipart/form-data`
2. Campos: `file` (obligatorio) + `zona` + `zona_detalle` (opcionales)
3. Respuesta incluye `url` y `annotated_url` listas para mostrar en `<img>`

### CORS configurado para
```
http://localhost:3000   (React CRA)
http://localhost:5173   (React + Vite)
```
Para producción agregar en `.env`:
```env
ALLOWED_ORIGINS=http://localhost:5173,https://identificador-basuras.lumengetium.edu.co
```
