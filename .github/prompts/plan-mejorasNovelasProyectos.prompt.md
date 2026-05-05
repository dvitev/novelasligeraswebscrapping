## Plan: Mejoras Completas — Django Backend + Next.js Frontend

**Resumen**: Plan de implementación en 5 fases para ambos proyectos. Fase 1 corrige bugs existentes, Fase 2 asegura el backend, Fase 3 mejora rendimiento, Fase 4 mejora arquitectura, Fase 5 mejora el frontend. Todas las fases mantienen compatibilidad entre ambos proyectos — las rutas del API Django nunca cambian de URL ni de estructura JSON.

---

### Fase 1 — Corrección de Bugs (ambos proyectos)

**1.1** Corregir typo `resources.MdelResources` → `resources.ModelResource` en `app/admin.py` (se repite en los 5 admin registrations).

**1.2** Corregir `Capitulo_id` → `capitulo_id` (mayúscula a minúscula) en `app/forms.py` — campo del formulario de `ContenidoCapitulo` que no coincide con el modelo.

**1.3** Corregir `NovelaCapitulosConteoViewSet.retrieve()` en `app/viewsets.py` — actualmente solo pasa `_id`, `cantidad_capitulos`, `cantidad_contenido_capitulos` al serializer pero el serializer define campos `nombre`, `sinopsis`, `autor`, etc. que quedan vacíos. Agregar los campos de la novela al dict `data`.

**1.4** Corregir doble appbar en Next.js — `app/layout.js` renderiza un `<header className="appbar">` y tanto `app/sitios/[_id]/page.jsx` como `app/novelas/[_id]/NovelDetail.jsx` rinden otro. Solución: eliminar el appbar del layout y dejar que cada página maneje el suyo, O crear un layout sin appbar y mover la navegación a las páginas.

**1.5** Agregar fallback de imagen en `NovelCard.jsx` y `NovelDetail.jsx` — si `imagen_url` es `null`/`undefined`, `next/image` lanza error. Agregar una imagen placeholder `/imagenes/no-cover.png`.

**1.6** Corregir `getSitio()` y `getNovela()` en `lib/api.js` — actualmente hacen `data[0]` asumiendo que la respuesta es un array. Esto es correcto dado que los ViewSets de Django usan `many=True` en `retrieve()`, pero es frágil. Agregar manejo para cuando la respuesta sea un objeto directo.

---

### Fase 2 — Seguridad del Backend

**2.1** Mover configuración sensible a variables de entorno en `settings.py`:
- `SECRET_KEY` → `os.environ.get("DJANGO_SECRET_KEY", "dev-key-insegura")`
- `DEBUG` → `os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1")`
- `ALLOWED_HOSTS` → `os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,192.168.1.11").split(",")`
- `DATABASES` HOST → `os.environ.get("MONGODB_HOST", "192.168.1.11")`
- `CORS_ALLOWED_ORIGINS` → `os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")`

**2.2** Crear archivo `.env.example` con todas las variables documentadas.

**2.3** Agregar rate limiting al REST Framework en `settings.py`:
- `DEFAULT_THROTTLE_CLASSES`: `AnonRateThrottle`
- `DEFAULT_THROTTLE_RATES`: `anon: 100/minute`

**2.4** Restringir `CORS_ALLOW_METHODS` a solo `["GET", "OPTIONS"]` para los ViewSets de lectura (el frontend solo hace GET). Mantener todos los métodos para `ContenidoCapituloViewSet` que sí necesita POST/PUT/DELETE.

**2.5** Agregar `django.middleware.gzip.GZipMiddleware` al middleware stack en `settings.py` — comprimir respuestas JSON grandes (listados de novelas/capítulos).

**2.6** En el proyecto Next.js: cambiar `NEXT_PUBLIC_API_URL` a `API_URL` (sin prefijo `NEXT_PUBLIC_`) en `.env.local` y `lib/api.js`. Todas las llamadas API se hacen desde server components, así que no necesita exponerse al browser. Crear una función aparte `getPublicApiUrl()` para los links de descarga EPUB/PDF que sí son client-side.

---

### Fase 3 — Rendimiento del Backend

**3.1** Optimizar filtrado de géneros en `NovelaSitioViewSet` de `app/viewsets.py` — actualmente carga TODAS las novelas en memoria Python y filtra una por una en un loop. Cambiar a filtrado en la query MongoDB usando `__regex` o `exclude()`:
```python
queryset = Novela.objects.filter(sitio_id=pk).exclude(
    genero__regex=r'Yaoi|Lgbt\+|Yuri|Shounen ai|Shoujo ai'
)
```

**3.2** Optimizar `GeneroViewSet` en `app/viewsets.py` — misma lógica de carga completa. Usar `values_list('genero', flat=True)` y procesar solo los strings de géneros, no objetos Novela completos.

**3.3** Habilitar paginación (descomentar `pagination_class = NovelaPagination` en `NovelaSitioViewSet`) pero con lógica de retrocompatibilidad: si el request no incluye `?page=`, devolver todos los resultados como array directo (formato actual que Next.js espera). Si incluye `?page=`, devolver formato paginado.

**3.4** Crear índices MongoDB manualmente ejecutando en MongoDB shell:
- `db.app_novela.createIndex({"sitio_id": 1})` — listar novelas por sitio
- `db.app_novela.createIndex({"nombre": "text"}, {default_language: "spanish"})` — búsqueda por texto
- `db.app_capitulo.createIndex({"novela_id": 1})` — listar capítulos por novela
- `db.app_contenidocapitulo.createIndex({"novela_id": 1})` — contar contenido por novela
- `db.app_contenidocapitulo.createIndex({"capitulo_id": 1})` — buscar contenido de un capítulo

**3.5** Agregar caché por vista para endpoints de solo lectura. Opción 1 (sin Redis): `django.views.decorators.cache.cache_page(300)` en los ViewSets más pesados (`NovelaSitioViewSet`, `GeneroViewSet`). Opción 2 (con Redis): configurar `CACHES` en settings con `django.core.cache.backends.redis.RedisCache`.

**3.6** En Next.js: cambiar `cache: "no-store"` a `next: { revalidate: 60 }` en `lib/api.js` para las funciones `getSitios()` y `getGeneros()` que cambian raramente. Mantener `cache: "no-store"` para novelas y capítulos que cambian con scraping.

---

### Fase 4 — Arquitectura y Calidad del Backend

**4.1** Limpiar `requirements.txt`:
- Eliminar duplicado `django-filter` (aparece dos veces)
- Eliminar paquetes no usados en Django: `flet`, `pyinstaller`, `undetected-chromedriver`, `undetected-edgedriver`, `zenrows`, `cloudscraper`, `selenium`, `webdriver_manager`, `Proxy-List-Scrapper`, `googletrans`, `icrawler`, `pandas`
- Fijar versiones con `>=X,<Y` para reproducibilidad
- Eliminar `mongoengine` (instalado pero nunca usado)

**4.2** Eliminar código muerto en `app/utils.py` — 240 líneas de funciones (`btn_guardar_pdf_click`, `btn_guardar_epub_click`, clase `PDF` duplicada) que son remanentes del proyecto Flet y no se usan en Django.

**4.3** Agregar manejo global de errores: crear `app/exception_handler.py` con un handler custom que convierta `bson.errors.InvalidId` en `400 Bad Request`, `ConnectionError` en `503`, y errores no manejados en `500` con JSON consistente. Registrar en `REST_FRAMEWORK['EXCEPTION_HANDLER']` en settings.

**4.4** Mejorar logging en `settings.py`:
- Agregar `RotatingFileHandler` para logs de archivo (max 10MB, 5 backups)
- Separar logger `scraping` del logger `app`
- Formato más descriptivo: `[{asctime}] {levelname} {module}.{funcName}:{lineno} — {message}`

**4.5** Agregar endpoint de health check: crear `app/views_health.py` con una vista que haga `db.command("ping")` a MongoDB y responda JSON `{"status": "healthy"}` o `503`. Registrar en `path('api/health/', health_check)` en `recopilarnovelasdjango/urls.py`.

**4.6** Mejorar generación EPUB/PDF en `app/views.py`:
- Mover a un módulo dedicado `app/services/export_service.py`
- Cerrar file handles correctamente (actualmente `open(ruta_imagen, 'rb').read()` no se cierra)
- Generar en memoria con `io.BytesIO` en vez de escribir a disco y releer
- Manejar errores si la novela no tiene capítulos o contenido
- Manejar timeout en la traducción (actualmente loops infinitos con `while True`)

**4.7** Escribir tests unitarios en `app/tests.py`:
- Test para cada endpoint GET (sitios, novelas, capítulos, géneros, conteo)
- Test para ID inválido → 400
- Test para recurso no encontrado → 404
- Test para health check
- Usar `unittest.mock.patch` para mockear los queries MongoDB

**4.8** Mejorar Dockerfile en `Dockerfile`:
- Actualizar de `python:3.10.2` a `python:3.12-slim` (más pequeña y segura)
- Separar en etapas `deps` → `dev` → `production`
- Agregar `HEALTHCHECK` usando el endpoint health
- Usar `gunicorn` en producción en vez de `runserver`

**4.9** Mejorar `docker-compose.yml`:
- Agregar servicio MongoDB 7 con volumen persistente y healthcheck
- Agregar servicio Redis para caché (si se implementa 3.5 opción 2)
- Usar `env_file: .env` en vez de variables hardcodeadas
- Agregar `depends_on` con condition `service_healthy`

---

### Fase 5 — Mejoras del Frontend Next.js

**5.1** Crear `.dockerignore` con: `node_modules`, `.next`, `.git`, `.env.local`, `README.md`.

**5.2** Mejorar manejo de errores en `lib/api.js`:
- Devolver objetos tipados `{ data, error, status }` en vez de `null` para que las páginas puedan distinguir "red caída" de "no encontrado" de "OK vacío"
- O crear un `error.jsx` boundary en las rutas

**5.3** Agregar CSS para estado `downloaded` en capítulos de `NovelDetail.jsx` — actualmente el CSS define `.chapter-item.downloaded` pero nunca se aplica la clase. Depende del bug 1.3 de Django (endpoint `conteocapitulosnovela`): cuando ese endpoint devuelva datos correctos, se puede usar para marcar capítulos individuales.

**5.4** Agregar `output: "standalone"` en `next.config.mjs` y actualizar el stage `production` del `Dockerfile` para usar la build standalone (reduce imagen de ~800MB a ~150MB).

**5.5** Restringir `images.remotePatterns` en `next.config.mjs` — actualmente `hostname: "**"` permite cualquier origen. Listar solo los hostnames reales de imágenes de novelas (ej: `cdn.novelbin.com`, `www.mtlnovel.com`, etc.) o al menos limitar a HTTP/HTTPS sin wildcard.

**5.6** Agregar `error.jsx` boundaries para:
- `app/error.jsx` — error global
- `app/sitios/[_id]/error.jsx` — error al cargar sitio
- `app/novelas/[_id]/error.jsx` — error al cargar novela

**5.7** Agregar `not-found.jsx` para:
- `app/not-found.jsx` — 404 global con estilo consistente

**5.8** Mejorar SEO: agregar `generateMetadata()` dinámico en `app/sitios/[_id]/page.jsx` y `app/novelas/[_id]/page.jsx` usando el nombre del sitio/novela como título de página.

---

### Fase 6 — Migración MongoDB: Djongo → PyMongo

> **Contexto**: Djongo (v1.3.6) está prácticamente abandonado, traduce SQL a queries MongoDB de forma ineficiente, no soporta aggregation pipelines, y tiene problemas conocidos con ObjectId y transacciones. Esta fase reemplaza Djongo por PyMongo directo con un patrón Repository para desacoplar el acceso a datos.

**6.1** Instalar `pymongo>=4.6,<5.0` y eliminar `djongo` de `requirements.txt`. Mantener Django y DRF — solo cambia la capa de acceso a datos, no los ViewSets ni serializers.

**6.2** Crear módulo `app/db.py` — singleton de conexión PyMongo:
```python
from pymongo import MongoClient
import os

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(
            host=os.environ.get("MONGODB_HOST", "192.168.1.11"),
            port=int(os.environ.get("MONGODB_PORT", 27017)),
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _client[os.environ.get("MONGODB_DATABASE", "recopilarnovelas")]
```

**6.3** Crear patrón Repository en `app/repositories/`:
- `base_repository.py` — clase base con `find_all()`, `find_by_id()`, `find_by_filter()`, `insert()`, `update()`, `delete()`, `aggregate()`, `count()`
- `sitio_repository.py` — `SitioRepository` con queries específicas de sitios
- `novela_repository.py` — `NovelaRepository` con filtrado de géneros excluidos, búsqueda por texto, paginación cursor-based
- `capitulo_repository.py` — `CapituloRepository` con ordenamiento y conteo
- `contenido_repository.py` — `ContenidoRepository` con búsqueda por `capitulo_id` y `novela_id`

**6.4** Migrar cada ViewSet para usar el Repository correspondiente en lugar de `Modelo.objects.filter()`. Los ViewSets llaman al repository → reciben dicts → pasan a serializer. La respuesta JSON no cambia.

**6.5** Reemplazar queries ineficientes con aggregation pipelines de MongoDB:
- **Conteo de capítulos por novela** — pipeline `$lookup` + `$count` en vez de 2 queries separadas:
  ```javascript
  db.app_novela.aggregate([
    { $match: { _id: ObjectId(novelaId) } },
    { $lookup: { from: "app_capitulo", localField: "_id", foreignField: "novela_id", as: "capitulos" } },
    { $lookup: { from: "app_contenidocapitulo", localField: "_id", foreignField: "novela_id", as: "contenidos" } },
    { $project: { nombre: 1, cantidad_capitulos: { $size: "$capitulos" }, cantidad_contenido: { $size: "$contenidos" } } }
  ])
  ```
- **Géneros únicos por sitio** — pipeline `$match` + `$unwind` + `$group` en vez de cargar todas las novelas en Python
- **Novelas con conteo** — pipeline que devuelve novelas con cantidad de capítulos en una sola query

**6.6** Mejorar diseño de documentos MongoDB (considerar para datos nuevos):
- **Embedding**: Mover `EstructuraSitio` como subdocumento dentro de `Sitio` (relación 1:1, siempre se consultan juntos)
- **Denormalización**: Agregar campo `cantidad_capitulos` pre-calculado en documento `Novela` (actualizar con `$inc` al insertar capítulo)
- **Genero como array**: Cambiar `genero` de string HTML separado por comas a array nativo `["Action", "Adventure", "Fantasy"]` — permite `$in` queries y `$unwind` directo

**6.7** Configuración MongoDB optimizada (aplicar en `mongod.conf` del contenedor Docker):
- `storage.wiredTiger.engineConfig.cacheSizeGB: 1` — limitar uso de RAM
- `storage.wiredTiger.collectionConfig.blockCompressor: snappy` — compresión
- Habilitar profiler nivel 1 (`slowOpThresholdMs: 100`) para detectar queries lentas
- Considerar replica set para alta disponibilidad (mínimo: 1 primary + 1 secondary + 1 arbiter)

**6.8** Ejecutar script de migración de datos `scripts/export_mongodb_for_migration.py` (ya creado):
- Fase export: respaldar todas las colecciones a JSON
- Fase verify: validar integridad referencial y formatos
- Fase import: importar a nueva estructura con índices
- Generar script de rollback automático

**6.9** Crear índices compuestos adicionales tras la migración:
- `db.app_novela.createIndex({"sitio_id": 1, "genero": 1})` — filtrado por sitio + género
- `db.app_novela.createIndex({"sitio_id": 1, "updated_at": -1})` — novelas recientes por sitio
- `db.app_capitulo.createIndex({"novela_id": 1, "created_at": -1})` — capítulos ordenados por fecha
- `db.app_novela.createIndex({"nombre": 1}, {unique: false, collation: {locale: "es", strength: 2}})` — búsqueda case-insensitive en español

---

### Fase 7 — Scraping con Selenium + undetected-chromedriver

> **Contexto**: Los sitios de novelas (NovelBin, FanMTL, MTLNovel, etc.) usan Cloudflare para protección anti-bot. Playwright y Selenium estándar son detectados. `undetected-chromedriver` parchea el binario de Chrome para evadir la detección de Cloudflare, y ejecutar en modo no-headless (con Xvfb como display virtual) es la estrategia más efectiva.

**7.1** Crear `Dockerfile.selenium-worker` — contenedor Docker dedicado al scraping:
- Base `python:3.12-slim` + Google Chrome real (no Chromium) vía repositorio de Google
- Instalar `xvfb`, `xauth`, `dbus-x11` para display virtual
- Script `entrypoint-worker.sh` que inicia `Xvfb :99 -screen 0 1920x1080x24` antes del worker
- Variable `DISPLAY=:99` para que Chrome use el display virtual
- Archivo `requirements.selenium.txt` separado: `undetected-chromedriver>=3.5`, `selenium>=4.15`, `celery>=5.3`, `redis>=5.0`, `pymongo>=4.6`, `beautifulsoup4>=4.12`, `lxml>=5.1`

**7.2** Crear servicio de scraping `app/services/scraper_service.py` con clase `ChapterScraper`:
- **`create_driver()`** — factory que crea instancia `uc.Chrome` con opciones anti-detección:
  - `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-blink-features=AutomationControlled`
  - `--window-size=1920,1080`, `--disable-gpu`
  - NO usar `--headless` (Cloudflare lo detecta) — Xvfb simula pantalla real
  - User-Agent rotativo desde lista predefinida
- **`wait_for_cloudflare(driver, timeout=30)`** — detecta challenge de Cloudflare buscando:
  - Título de página `"Just a moment..."` o `"Attention Required"`
  - iframe con id `cf-challenge`
  - Elemento `#challenge-running`
  - Espera hasta que desaparezca o timeout
- **`scrape_chapter(url, site_config)`** — scraping de un capítulo:
  - Navegar con `driver.get(url)`
  - Esperar bypass de Cloudflare
  - Scroll progresivo para cargar lazy content (`window.scrollBy(0, 300)`)
  - Extraer contenido con BeautifulSoup usando selectores CSS del `site_config`
  - Limpiar HTML: eliminar ads, scripts, estilos inline, divs vacíos
  - Retornar texto limpio y metadata
- **`warm_up(base_url)`** — visitar homepage primero para establecer cookies de Cloudflare antes de scraping masivo
- **Retry logic**: 3 intentos con backoff exponencial (5s, 15s, 45s), recrear driver tras 2 fallos consecutivos
- **Rate limiting**: `time.sleep(random.uniform(2, 5))` entre requests para no activar rate limiter del sitio

**7.3** Crear configuración de sitios `app/services/site_configs.py` — diccionario `SITE_CONFIGS` con selectores CSS por sitio:
```python
SITE_CONFIGS = {
    "novelbin": {
        "base_url": "https://novelbin.com",
        "chapter_content_selector": "#chr-content",
        "chapter_title_selector": ".chr-title h2",
        "next_chapter_selector": "#next_chap",
        "remove_selectors": [".ads-holder", "script", ".hidden"],
        "encoding": "utf-8",
    },
    "fanmtl": {
        "base_url": "https://www.fanmtl.com",
        "chapter_content_selector": ".chapter-content",
        "chapter_title_selector": ".chapter-title",
        "next_chapter_selector": "a.next-chapter",
        "remove_selectors": [".ad-container", "script", "ins"],
        "encoding": "utf-8",
    },
    "mtlnovel": {
        "base_url": "https://www.mtlnovel.com",
        "chapter_content_selector": ".chapter-content",
        "chapter_title_selector": ".current-crumb span",
        "next_chapter_selector": "a.next",
        "remove_selectors": [".donate-section", "script", ".ad-zone"],
        "encoding": "utf-8",
    },
}
```

**7.4** Crear sistema de gestión de drivers con pool:
- Máximo 3 instancias de Chrome simultáneas (configurable vía `MAX_CHROME_INSTANCES`)
- Reutilizar driver entre capítulos del mismo sitio (mantener session/cookies de Cloudflare)
- Cerrar driver tras inactividad de 5 minutos o tras procesar 50 capítulos (evitar memory leaks)
- Cleanup automático de procesos Chrome huérfanos: `pkill -f chrome` en caso de crash

**7.5** Consideraciones anti-detección adicionales:
- Rotar User-Agent cada 20 requests desde pool de 10+ UAs reales de Chrome en Windows/Mac/Linux
- Randomizar viewport size ligeramente (±50px)
- Simular movimientos de mouse con `ActionChains` antes del primer scroll
- Respetar `robots.txt` delays cuando estén definidos
- Cap de 500 capítulos por sesión de scraping para evitar bans de IP
- Soporte para proxies rotativos (configurable, no obligatorio): pasar `proxy` a `uc.Chrome()`

---

### Fase 8 — Celery + Redis: Tareas Asíncronas

> **Contexto**: El scraping de novelas completas puede tomar horas (miles de capítulos). Ejecutar esto de forma síncrona en el request HTTP de Django bloquea el servidor. Celery con Redis permite ejecutar el scraping en workers dedicados con seguimiento de progreso.

**8.1** Instalar y configurar Celery:
- Agregar `celery>=5.3,<6.0`, `redis>=5.0,<6.0` a `requirements.txt`
- Crear `recopilarnovelasdjango/celery.py`:
  ```python
  import os
  from celery import Celery

  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recopilarnovelasdjango.settings")
  app = Celery("recopilarnovelas")
  app.config_from_object("django.conf:settings", namespace="CELERY")
  app.autodiscover_tasks()
  ```
- Agregar a `recopilarnovelasdjango/__init__.py`:
  ```python
  from .celery import app as celery_app
  __all__ = ("celery_app",)
  ```
- Configuración en `settings.py`:
  ```python
  CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://192.168.1.11:6379/0")
  CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://192.168.1.11:6379/1")
  CELERY_ACCEPT_CONTENT = ["json"]
  CELERY_TASK_SERIALIZER = "json"
  CELERY_RESULT_SERIALIZER = "json"
  CELERY_TASK_TRACK_STARTED = True
  CELERY_TASK_TIME_LIMIT = 7200  # 2 horas max por tarea
  CELERY_TASK_SOFT_TIME_LIMIT = 6600  # aviso a 1h50
  CELERY_WORKER_MAX_TASKS_PER_CHILD = 10  # reiniciar worker tras 10 tareas (liberar memoria Chrome)
  ```

**8.2** Crear tareas Celery en `app/tasks.py`:
- **`scrape_novel_chapters`** — tarea principal:
  - Recibe `novela_id`, `site_key`, `start_url`, `max_chapters` (opcional)
  - Crea `ChapterScraper`, warm-up, itera capítulos
  - Actualiza progreso en Redis: `task.update_state(state="PROGRESS", meta={"current": n, "total": total, "chapter": nombre})`
  - Guarda cada capítulo en MongoDB via Repository
  - Manejo de `SoftTimeLimitExceeded`: guardar progreso, cerrar driver, reportar parcial
  - Manejo de cancelación: verificar `task.is_aborted()` en cada iteración
- **`scrape_novel_list`** — scraping de lista de novelas de un sitio:
  - Recibe `sitio_id`, `site_key`
  - Extrae URLs de novelas de la página del sitio
  - Crea subtareas `scrape_novel_chapters` por cada novela nueva (no existente en DB)
  - Usa `celery.group()` para paralelizar (máximo 3 simultáneas)
- **`cleanup_stale_tasks`** — tarea periódica (cada 30 min):
  - Buscar tareas en estado PROGRESS que no han actualizado en >30min → marcar como FAILURE
  - Limpiar drivers Chrome huérfanos
  - Reportar estadísticas de scraping al log

**8.3** Crear endpoints API de scraping en `app/views_scraping.py`:
- **`POST /api/scraping/iniciar/`** — iniciar scraping de una novela:
  - Body: `{"novela_id": "...", "site_key": "novelbin", "start_url": "https://..."}`
  - Valida que no exista tarea activa para esa novela
  - Lanza `scrape_novel_chapters.delay()`
  - Responde `{"task_id": "uuid", "status": "PENDING"}`
- **`GET /api/scraping/progreso/{task_id}/`** — consultar progreso:
  - Responde `{"task_id": "uuid", "status": "PROGRESS", "current": 45, "total": 200, "chapter": "Chapter 45: ..."}`
  - Estados posibles: `PENDING`, `STARTED`, `PROGRESS`, `SUCCESS`, `FAILURE`, `REVOKED`
- **`POST /api/scraping/cancelar/{task_id}/`** — cancelar tarea:
  - Llama `celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")`
  - Responde `{"task_id": "uuid", "status": "REVOKED"}`
- **`GET /api/scraping/tareas-activas/`** — listar tareas en ejecución:
  - Responde array de tareas con su progreso actual

**8.4** Registrar URLs de scraping en `app/urls_scraping.py` e incluir en `recopilarnovelasdjango/urls.py`:
```python
urlpatterns += [
    path('api/scraping/', include('app.urls_scraping')),
]
```

**8.5** Configurar Redis como caché de Django (doble función: broker Celery + caché):
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://192.168.1.11:6379/2"),
        "OPTIONS": {
            "db": 2,
        },
        "KEY_PREFIX": "novelas",
        "TIMEOUT": 300,
    }
}
```

**8.6** Celery Beat para tareas programadas (opcional):
- Scraping automático diario de novelas con `status="ongoing"` para detectar nuevos capítulos
- Limpieza de tareas stale cada 30 minutos
- Reporte diario de estadísticas de scraping por email/log
```python
CELERY_BEAT_SCHEDULE = {
    "scrape-ongoing-novels": {
        "task": "app.tasks.scrape_ongoing_novels",
        "schedule": crontab(hour=3, minute=0),  # 3:00 AM diario
    },
    "cleanup-stale-tasks": {
        "task": "app.tasks.cleanup_stale_tasks",
        "schedule": 1800.0,  # cada 30 min
    },
}
```

---

### Fase 9 — Docker Compose Completo y DevOps

> **Contexto**: Unificar todos los servicios (Django API, Next.js frontend, MongoDB, Redis, Selenium worker, Celery Beat) en un solo `docker-compose.yml` con health checks, volúmenes persistentes y configuración por variables de entorno.

**9.1** Crear `docker-compose.yml` unificado con todos los servicios:
```yaml
services:
  mongodb:
    image: mongo:7
    volumes:
      - mongodb_data:/data/db
      - ./mongod.conf:/etc/mongod.conf
    ports:
      - "27017:27017"
    healthcheck:
      test: mongosh --eval "db.adminCommand('ping')"
      interval: 10s
      timeout: 5s
      retries: 5
    env_file: .env

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: redis-cli ping
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./recopilarnovelasdjango
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: curl -f http://localhost:8000/api/health/ || exit 1
      interval: 30s
      timeout: 10s
      retries: 3

  selenium-worker:
    build:
      dockerfile: Dockerfile.selenium-worker
      context: ./recopilarnovelasdjango
    env_file: .env
    environment:
      - DISPLAY=:99
      - C_FORCE_ROOT=true
    command: celery -A recopilarnovelasdjango worker -l info -Q scraping -c 2 --max-tasks-per-child=10
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2"
    shm_size: "2gb"

  celery-beat:
    build:
      context: ./recopilarnovelasdjango
      dockerfile: Dockerfile
    command: celery -A recopilarnovelasdjango beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy

  frontend:
    build:
      context: ./recopilarnovelasnextjs
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    env_file: .env
    depends_on:
      api:
        condition: service_healthy

volumes:
  mongodb_data:
  redis_data:
```

**9.2** Crear `.env.example` completo con todas las variables de todos los servicios:
```env
# Django
DJANGO_SECRET_KEY=cambiar-en-produccion
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.11

# MongoDB
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DATABASE=recopilarnovelas

# Redis
REDIS_URL=redis://redis:6379/2
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.11:3000

# Scraping
MAX_CHROME_INSTANCES=3
SCRAPING_RATE_LIMIT_MIN=2
SCRAPING_RATE_LIMIT_MAX=5
SCRAPING_MAX_CHAPTERS_PER_SESSION=500

# Next.js
API_URL=http://api:8000
```

**9.3** Crear `mongod.conf` optimizado para el contenedor:
```yaml
storage:
  dbPath: /data/db
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
    collectionConfig:
      blockCompressor: snappy
operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
net:
  port: 27017
  bindIp: 0.0.0.0
```

**9.4** Agregar scripts de utilidad:
- `scripts/start-dev.sh` — levantar todos los servicios en modo desarrollo
- `scripts/backup-mongodb.sh` — backup diario de MongoDB con `mongodump`
- `scripts/restore-mongodb.sh` — restaurar desde backup
- `scripts/logs.sh` — tail de logs de todos los servicios con colores

**9.5** Consideraciones de producción (documentar en README):
- Usar `gunicorn` con 4 workers + `uvicorn` para async en vez de `runserver`
- HTTPS con Nginx reverse proxy o Traefik como servicio adicional en compose
- Volumen separado para logs
- Secrets con Docker secrets en vez de `.env` file en producción
- Monitoreo: Flower para Celery (`celery -A recopilarnovelasdjango flower`) en puerto 5555
- Rate limiting a nivel de Nginx además del de Django

---

### Consideraciones Transversales

**C.1 — Retrocompatibilidad API**: Todas las fases mantienen las URLs y estructura JSON actuales del API. Los ViewSets siguen respondiendo en el mismo formato. La migración a PyMongo (Fase 6) es transparente para Next.js porque los ViewSets siguen devolviendo los mismos dicts serializados.

**C.2 — Estrategia anti-detección Cloudflare**: La combinación `undetected-chromedriver` + Chrome real (no Chromium) + Xvfb (display virtual, modo no-headless) es actualmente la más efectiva. Headless mode es cada vez más detectable. Si Cloudflare actualiza sus checks, considerar:
- Actualizar `undetected-chromedriver` (se actualiza frecuentemente)
- Agregar plugin `stealth.min.js` via `driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {...})`
- Proxies residenciales como último recurso (servicio de pago)

**C.3 — Memoria y recursos**: Chrome consume ~300-500MB de RAM por instancia. Con 3 instancias simultáneas + overhead, el contenedor `selenium-worker` necesita 2-4GB. Configurar `shm_size: 2gb` en Docker y `--disable-dev-shm-usage` en Chrome para evitar crashes.

**C.4 — Manejo de fallos de scraping**: No todos los capítulos se scrapearán exitosamente. El sistema debe:
- Guardar resultado parcial si la tarea falla a mitad
- Permitir reintentar desde el último capítulo exitoso (`start_url` del siguiente pendiente)
- Registrar capítulos fallidos en una cola de retry separada
- No reescribir capítulos ya existentes en MongoDB (verificar antes de insertar)

**C.5 — Limpieza de contenido scrapeado**: El HTML de los sitios de novelas está lleno de basura. El scraper debe:
- Eliminar todos los `<script>`, `<style>`, `<ins>` (Google Ads), `<iframe>`
- Eliminar divs con clases que contengan "ad", "sponsor", "donate", "social"
- Convertir `<br><br>` consecutivos en saltos de párrafo `<p>`
- Preservar itálicas (`<em>`, `<i>`) y negritas (`<strong>`, `<b>`) del texto original
- Normalizar encoding a UTF-8 (algunos sitios usan GB2312 o EUC-KR)

**C.6 — Genero como array nativo**: Al migrar a PyMongo (Fase 6.6), el campo `genero` pasa de string HTML a array. Esto requiere:
- Script de migración que parsee los strings existentes y los convierta a arrays
- Actualizar serializers para devolver `genero` como string comma-separated (retrocompatibilidad) o array (si Next.js se adapta)
- Actualizar `GeneroViewSet` para usar `$unwind` + `$group` directo
- Actualizar `NovelaSitioViewSet` para usar `$nin` en vez de regex

**C.7 — Orden de dependencias entre fases**:
- Fases 1-5 son independientes de 6-9 y pueden ejecutarse primero
- Fase 7 (Selenium) depende de Fase 8 (Celery) para ejecución async
- Fase 8 (Celery) depende de tener Redis (incluido en Fase 9)
- Fase 6 (PyMongo) es independiente pero beneficia a Fase 7 (repositories simplifican el scraper)
- Fase 9 unifica todo y debe ser la última

---

### Orden de Implementación Actualizado

```
Semana 1  │ Fase 1 — Bugs (1.1–1.6)
          │ Fase 2 — Seguridad (2.1–2.6)
──────────┤
Semana 2  │ Fase 3 — Rendimiento (3.1–3.6)
          │ Fase 4.1–4.3 — Limpieza y error handler
──────────┤
Semana 3  │ Fase 4.4–4.9 — Logging, health, export, Docker
          │ Fase 5.1–5.4 — Frontend Docker, errores, standalone
──────────┤
Semana 4  │ Fase 4.7 — Tests
          │ Fase 5.5–5.8 — Seguridad imágenes, SEO, error boundaries
──────────┤
Semana 5  │ Fase 6.1–6.4 — PyMongo + Repositories (migración core)
          │ Fase 6.5–6.6 — Aggregation pipelines + diseño documentos
──────────┤
Semana 6  │ Fase 6.7–6.9 — Config MongoDB + migración datos + índices
          │ Fase 8.1–8.2 — Celery + Redis + tareas
──────────┤
Semana 7  │ Fase 7.1–7.3 — Docker Selenium + scraper service + site configs
          │ Fase 7.4–7.5 — Pool de drivers + anti-detección
──────────┤
Semana 8  │ Fase 8.3–8.6 — API scraping + Redis caché + Beat
          │ Fase 9.1–9.5 — Docker Compose completo + scripts + producción
```

### Verificación

- Ejecutar Django tests con `python manage.py test app`
- Verificar cada endpoint con `curl http://192.168.1.11:8000/api/sitios/` y comparar JSON con la estructura actual
- Ejecutar `npm run build` en Next.js para verificar que compila sin errores
- Verificar visualmente las 3 páginas: Home, Sitio, Novela
- Verificar descarga EPUB/PDF
- Ejecutar `docker-compose up` en ambos proyectos
- Verificar scraping: `curl -X POST http://localhost:8000/api/scraping/iniciar/` con una novela de prueba
- Verificar progreso: `curl http://localhost:8000/api/scraping/progreso/{task_id}/`
- Verificar Celery workers: `celery -A recopilarnovelasdjango inspect active`
- Verificar MongoDB indexes: `db.app_novela.getIndexes()` en mongosh
- Verificar Redis: `redis-cli ping` → `PONG`
- Verificar Flower dashboard: `http://localhost:5555`
- Ejecutar migration script: `python scripts/export_mongodb_for_migration.py --phase verify`

### Decisiones Actualizadas

- **Migrar de Djongo a PyMongo** (Fase 6) — Djongo está abandonado y limita el uso real de MongoDB. PyMongo con patrón Repository desacopla mejor y permite aggregation pipelines, índices compuestos, y operaciones atómicas reales.
- **Selenium + undetected-chromedriver sobre Playwright** — Los sitios de novelas (NovelBin, FanMTL, MTLNovel) usan Cloudflare y detectan headless browsers estándar. `undetected-chromedriver` + Chrome real + Xvfb es la combinación más efectiva actualmente para bypass.
- **Celery + Redis para scraping async** (Fase 8) — Scraping síncrono en requests HTTP bloquea el servidor. Celery permite workers dedicados, progreso en tiempo real, cancelación, y tareas programadas.
- **Redis triple función**: broker de Celery (db 0), result backend (db 1), caché de Django (db 2) — un solo servicio Redis simplifica la infraestructura.
- **Docker Compose unificado** (Fase 9) — Todos los servicios en un solo compose con health checks y dependencias correctas. Evita la configuración manual de cada servicio por separado.
- **Retrocompatibilidad siempre** — ningún paso cambia URLs ni estructura JSON del API. Los cambios internos son transparentes para Next.js. Excepción controlada: `genero` puede cambiar de string a array si Next.js se adapta (ver C.6).
