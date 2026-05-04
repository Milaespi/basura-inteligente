# Guía del Backend para el Frontend
## Identificación de Basuras Inteligentes — Fundación Universitaria Católica Lumen Gentium

---

## ¿Qué hace este backend?

API REST construida con **FastAPI + Python** que recibe imágenes, las analiza con un modelo de inteligencia artificial **YOLO11s** entrenado para clasificar residuos en tres categorías, y guarda los resultados en **MongoDB Atlas**.

### Categorías que detecta el modelo
| Clase | Descripción |
|---|---|
| `Aprovechable` | Reciclables: plástico, papel, cartón, vidrio, metal |
| `No_aprovechable` | No reciclables: icopor, papel higiénico, colillas, envases sucios |
| `Orgánico` | Restos de comida, cáscaras, residuos de jardín |

---

## URL del backend desplegado

```
https://mila10-basura-inteligente.hf.space
```

> **Importante:** El backend está en Hugging Face Spaces tier gratuito. Si lleva un rato sin recibir peticiones, **la primera petición puede tardar ~30 segundos** mientras despierta. Las siguientes son normales.

### Documentación interactiva (Swagger)
```
https://mila10-basura-inteligente.hf.space/docs
```
Desde ahí puedes probar todos los endpoints directamente en el navegador.

---

## Autenticación

El backend usa **JWT (JSON Web Token)**. El flujo es:

1. El usuario hace login → el backend devuelve un `access_token`
2. En cada petición que requiera autenticación, se envía ese token en el header:

```
Authorization: Bearer <access_token>
```

El token expira en **60 minutos**.

---

## Endpoints

### Autenticación — `/api/auth`

---

#### `POST /api/auth/register` — Registrar cuenta
No requiere autenticación.

**Body (JSON):**
```json
{
  "nombre": "Juan Pérez",
  "email": "juan@unicatolicacali.edu.co",
  "password": "mi_contraseña"
}
```

**Respuesta exitosa (201):**
```json
{
  "id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "nombre": "Juan Pérez",
  "email": "juan@unicatolicacali.edu.co",
  "rol": "user",
  "created_at": "2026-05-04T14:00:00Z"
}
```

**Errores posibles:**
- `400` — El email ya está registrado
- `422` — Datos inválidos (email mal formado, contraseña muy corta, etc.)

---

#### `POST /api/auth/login` — Iniciar sesión
No requiere autenticación.

**Body (JSON):**
```json
{
  "email": "juan@unicatolicacali.edu.co",
  "password": "mi_contraseña"
}
```

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errores posibles:**
- `401` — Email o contraseña incorrectos

---

#### `GET /api/auth/me` — Ver perfil del usuario
Requiere token.

**Respuesta exitosa (200):**
```json
{
  "id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "nombre": "Juan Pérez",
  "email": "juan@unicatolicacali.edu.co",
  "rol": "user",
  "created_at": "2026-05-04T14:00:00Z"
}
```

---

### Detecciones — `/api/detections`

---

#### `POST /api/detections/analyze` — Analizar imagen
Requiere token. Usa `multipart/form-data` (no JSON).

**Campos del formulario:**
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo | ✅ | Imagen JPG, PNG o WEBP |
| `zona` | texto | No | Nombre del lugar (ej: "Cafetería central") |
| `zona_detalle` | texto | No | Detalle (ej: "Edificio principal") |

**Ejemplo en JavaScript (fetch):**
```javascript
const formData = new FormData();
formData.append("file", imagenFile);
formData.append("zona", "Cafetería central");
formData.append("zona_detalle", "Edificio principal");

const response = await fetch(
  "https://mila10-basura-inteligente.hf.space/api/detections/analyze",
  {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  }
);
```

**Respuesta exitosa (201):**
```json
{
  "id": "64f1a2b3c4d5e6f7a8b9c0d2",
  "user_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "filename": "imagen.jpg",
  "url": "/uploads/64f.../imagen.jpg",
  "annotated_url": "/uploads/64f.../annotated/imagen_ann.jpg",
  "zona": "Cafetería central",
  "zona_detalle": "Edificio principal",
  "detections": [
    {
      "clase": "Aprovechable",
      "confianza": 0.91,
      "bbox": [0.1, 0.2, 0.5, 0.8]
    }
  ],
  "resumen": {
    "Aprovechable": 2,
    "No_aprovechable": 1
  },
  "created_at": "2026-05-04T14:32:00Z"
}
```

**Notas:**
- `url` y `annotated_url` son rutas relativas. Para mostrar las imágenes en `<img>` úsalas así:
  ```
  https://mila10-basura-inteligente.hf.space/uploads/...
  ```
- `annotated_url` es la imagen con los recuadros dibujados por el modelo
- `bbox` son coordenadas normalizadas `[x1, y1, x2, y2]` entre 0 y 1
- `resumen` es un conteo de cuántos objetos de cada clase se detectaron

---

#### `GET /api/detections/history` — Historial con paginación
Requiere token. Devuelve solo las detecciones del usuario autenticado.

**Query params (todos opcionales):**
| Param | Valores | Default | Descripción |
|---|---|---|---|
| `limit` | 1–100 | 20 | Registros por página |
| `skip` | ≥0 | 0 | Registros a omitir (para paginación) |
| `categoria` | `Aprovechable` \| `No_aprovechable` \| `Orgánico` | — | Filtrar por clase |
| `zona` | texto | — | Buscar por zona (coincidencia parcial) |
| `fecha` | `hoy` \| `semana` \| `mes` | — | Filtrar por período |

**Ejemplo:**
```
GET /api/detections/history?limit=10&skip=0&fecha=semana
```

**Respuesta (200):**
```json
{
  "total": 45,
  "skip": 0,
  "limit": 10,
  "items": [
    {
      "id": "...",
      "filename": "imagen.jpg",
      "url": "/uploads/.../imagen.jpg",
      "annotated_url": "/uploads/.../annotated/imagen_ann.jpg",
      "zona": "Cafetería central",
      "zona_detalle": "Edificio principal",
      "resumen": { "Aprovechable": 2 },
      "confianza_max": 0.91,
      "created_at": "2026-05-04T14:32:00Z"
    }
  ]
}
```

> Usa `total`, `skip` y `limit` para construir la paginación en el frontend.

---

#### `GET /api/detections/history/export` — Exportar CSV
Requiere token. Acepta los mismos filtros que `/history`.

Descarga un archivo `historial_basuras.csv` con columnas:
`ID, Zona, Detalle zona, Aprovechable, No_aprovechable, Orgánico, Confianza máx., Fecha`

---

#### `GET /api/detections/stats/global` — Estadísticas globales
Requiere token.

**Respuesta (200):**
```json
{
  "total_imagenes_analizadas": 360,
  "total_detecciones": 360,
  "distribucion_por_clase": {
    "Aprovechable":    { "total": 187, "porcentaje": 52.0 },
    "No_aprovechable": { "total": 112, "porcentaje": 31.0 },
    "Orgánico":        { "total": 61,  "porcentaje": 17.0 }
  },
  "detecciones_por_dia": [
    { "fecha": "2026-05-01", "total": 45 },
    { "fecha": "2026-05-02", "total": 32 }
  ],
  "metricas_por_clase": {
    "Aprovechable":    { "precision": 0.963, "recall": 0.941, "f1": 0.952, "map50": 0.968, "muestras": 187 },
    "No_aprovechable": { "precision": 0.921, "recall": 0.887, "f1": 0.904, "map50": 0.932, "muestras": 112 },
    "Orgánico":        { "precision": 0.945, "recall": 0.912, "f1": 0.928, "map50": 0.951, "muestras": 61 },
    "Promedio":        { "precision": 0.943, "recall": 0.913, "f1": 0.928, "map50": 0.950, "muestras": 360 }
  }
}
```

---

#### `GET /api/detections/{id}` — Detalle de una detección
Requiere token.

**Respuesta (200):** Igual que la respuesta de `/analyze`.

**Errores:**
- `404` — Detección no encontrada o no pertenece al usuario

---

### Administración — `/api/admin`

#### `GET /api/admin/users` — Listar usuarios
Requiere token con `rol: "admin"`.

---

## Roles de usuario

| Rol | Descripción |
|---|---|
| `user` | Usuario normal, acceso a sus propias detecciones |
| `admin` | Acceso a endpoints de administración |

---

## Manejo de errores

Todos los errores siguen este formato:
```json
{
  "detail": "Mensaje descriptivo del error"
}
```

Códigos más comunes:
| Código | Significado |
|---|---|
| `400` | Datos incorrectos (ej: email ya registrado) |
| `401` | No autenticado o token inválido/expirado |
| `403` | Sin permisos (ej: no es admin) |
| `404` | Recurso no encontrado |
| `422` | Error de validación (campos faltantes o mal formados) |

---

## CORS

El backend acepta peticiones desde cualquier origen (`*`). No hay restricciones de dominio para el frontend.

---

## Resumen del flujo completo

```
1. POST /api/auth/register  → crear cuenta
2. POST /api/auth/login     → obtener token JWT
3. POST /api/detections/analyze  → subir imagen → recibir detecciones
4. GET  /api/detections/history  → ver historial
5. GET  /api/detections/stats/global → ver estadísticas
```

Guarda el `access_token` del login en `localStorage` o el estado de tu app y envíalo en cada petición como:
```
Authorization: Bearer <access_token>
```
