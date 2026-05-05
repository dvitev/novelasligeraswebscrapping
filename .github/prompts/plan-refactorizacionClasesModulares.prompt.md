# Plan: Refactorización completa a clases modulares

Descomponer `recopilarnovelas_flet.py` (2086 líneas, ~42 funciones en `main()`) en 12 archivos con clases independientes, corrigiendo 3 bugs críticos, añadiendo buscador server-side `$regex` e índices MongoDB.

## Estructura final de archivos

```
recopilarnovelas_flet.py              # ~70 líneas — orquestador
config/
  __init__.py                         # re-exports Database, constants
  database.py                         # Database singleton + indexes
  constants.py                        # Todas las constantes
repositories/
  __init__.py                         # re-export DataRepository
  data_repository.py                  # DataRepository + búsquedas $regex
services/
  __init__.py                         # re-exports 3 servicios
  translation_service.py              # TranslationService
  export_service.py                   # ExportService + PDF class
  scraping_service.py                 # ScrapingService (threading)
views/
  __init__.py                         # re-exports builders + theme
  theme.py                            # AppColors, create_dark_theme
  home_view.py                        # HomeViewBuilder
  site_detail_view.py                 # SiteDetailViewBuilder + buscador
  novel_detail_view.py                # NovelDetailViewBuilder + buscador
```

---

## Step 1 — Crear `config/__init__.py`, `config/constants.py` y `config/database.py`

### `config/constants.py`

Mover todas las constantes de líneas 52–75 del archivo original:

- `FANMTL_SITIO_ID`, `TUNOVELA_LIGERA_SITIO_ID`, `CHARACTER_LIMITS`, `DEFAULT_SLEEP_TIME`, `PARAGRAPH_DELIMITER`, `TEMP_IMAGE_FILENAME`, `PINGO_FONT_PATH`, `NOVELAS_POR_PAGINA`, `CAPITULOS_POR_PAGINA`.
- Corregir `PINGO_FONT_PATH` para usar `os.path.join` con `os.sep` en vez de forward slashes.

### `config/database.py`

Clase `Database`:

- `__init__(self, uri, db_name)`: crea `MongoClient(uri, serverSelectionTimeoutMS=5000)`, guarda `self.db`, expone propiedades `sitios`, `novelas`, `capitulos`, `contenido_capitulos` que retornan las 4 colecciones (`app_sitio`, `app_novela`, `app_capitulo`, `app_contenidocapitulo`).
- `ensure_indexes(self)`: crea 3 índices:
  - `app_novela`: `{'sitio_id': 1, 'nombre': 1}` (compuesto para búsquedas `$regex` por sitio).
  - `app_capitulo`: `{'novela_id': 1, 'created_at': 1}`.
  - `app_contenidocapitulo`: `{'novela_id': 1, 'capitulo_id': 1}`.
- `close(self)`: cierra `MongoClient`.
- Mover `MONGO_URI` y `DB_NAME` de líneas 37–38 como parámetros por defecto desde `os.getenv`.

### `config/__init__.py`

```python
from .database import Database
from .constants import *
```

---

## Step 2 — Crear `repositories/__init__.py` y `repositories/data_repository.py`

### Clase `DataRepository(db: Database)`

Extraer 8 métodos existentes de líneas 1014–1080, 463–471 y 620–627:

- `load_home_data(self)` → de `load_home_data` (línea 1014). Usa `self.db.sitios.find()`.
- `load_sitio_details_paginado(self, sitio_id, pagina, por_pagina, query="")` → de línea 1025. **NUEVO**: si `query` no vacío, añadir `{'nombre': {'$regex': query, '$options': 'i'}}` al filtro de `find()` y `count_documents()`.
- `load_novela_details(self, novela_id)` → de línea 1047.
- `load_ids_capitulos_novela(self, novela_id)` → de línea 1055. Retorna `set`.
- `load_ids_urls_capitulos_novela(self, novela_id)` → de línea 1063. Retorna `dict`.
- `load_ids_contenido_capitulos_novela(self, novela_id)` → de línea 1071. Retorna `set`.
- `enviar_contenido_capitulo(self, novela_id, capitulo_id, texto)` → de línea 463.
- `obtener_contenido_capitulos(self, novela_id)` → de línea 620. Retorna `dict {cap_id: texto}`.
- **NUEVO** `buscar_capitulos(self, novela_id, query)` → `self.db.capitulos.find({'novela_id': novela_id, 'nombre': {'$regex': query, '$options': 'i'}}).sort('created_at', 1)`.
- **NUEVO** `get_capitulos_faltantes(self, todos_ids, ids_con_contenido)` → retorna `set(todos_ids) - set(ids_con_contenido)` — reemplaza `comparar_diccionarios` de línea 1079.

### `repositories/__init__.py`

```python
from .data_repository import DataRepository
```

---

## Step 3 — Crear `services/__init__.py` y `services/translation_service.py`

### Clase `TranslationService`

Extraer de líneas 376–428:

- `@staticmethod traducir(texto: str) -> str` — el cuerpo exacto de `traducir`, usando `translators as ts` y `google_translator`.
- `@staticmethod traducir_texto_largo(texto: str, delimitador: str) -> str` — el cuerpo exacto, llamando `TranslationService.traducir()` internamente.
- Imports propios: `translators as ts`, `google_trans_new.google_translator`, `logging`, y `CHARACTER_LIMITS` de `config.constants`.

---

## Step 4 — Crear `services/export_service.py`

### Clase `PDF(FPDF)`

Mover de líneas 239–265 al inicio del módulo. Sin cambios en sus métodos (`header`, `footer`, `chapter_title`, `chapter_body`, `add_section`, `print_chapter`).

### Clase `ExportService`

`__init__(self, page, repo, translation_svc, filepicker, ui_controls)`:

- `self.page = page`
- `self.repo = repo` (DataRepository)
- `self.translation = translation_svc` (TranslationService)
- `self.filepicker = filepicker`
- `self.btn_epub = ui_controls['btn_epub']` (igual para `btn_pdf`, `btn_procesar`, `progress_ring`, `open_banner`)
- **Estado como atributos** (elimina `nonlocal`/`global`): `self.cancelar = False`, `self.progreso_bar = None`, `self.texto_progreso = None`, `self._portada = None`.

### Métodos privados

De las helpers no usadas (líneas 643–710), ahora **sí invocados**:

- `_preparar_ui(self, formato)` — deshabilita botones, muestra `progress_ring`, crea `ProgressBar`. Tomado de `preparar_ui_exportacion`.
- `_actualizar_progreso(self, idx, total, nombre, formato)` — actualiza barra cada 5 caps. Tomado de `actualizar_progreso_exportacion`.
- `_finalizar_ui(self)` — restaura botones, oculta `progress_ring`, limpia portada temporal. Tomado de `finalizar_ui_exportacion`.
- `_descargar_imagen(self, url)` → de línea 580.
- `_descargar_y_preparar_portada(self, url)` → de línea 629. Llama `self._descargar_imagen`.
- `_limpiar_portada(self)` → de línea 703.
- `_sanitizar_nombre(self, nombre)` → de línea 612.

### Métodos públicos

- `crear_epub(self, novela, capitulos)` — De líneas 735–888. Llama `self._preparar_ui('epub')`, luego `threading.Thread(target=self._epub_worker, args=(novela, capitulos), daemon=True).start()`.
- `_epub_worker(self, novela, capitulos)` — Lógica actual de `_epub_worker`, pero usando `self.repo.obtener_contenido_capitulos()`, `self._descargar_y_preparar_portada()`, `self.translation.traducir()`, `self._actualizar_progreso()` (reemplazando inline `open_banner` cada 5 caps), y `self._finalizar_ui()` en `finally`.
- `crear_pdf(self, novela, capitulos)` / `_pdf_worker(self, novela, capitulos)` — Mismo patrón, de líneas 890–1002.

---

## Step 5 — Crear `services/scraping_service.py`

### Clase `ScrapingService`

`__init__(self, page, repo, translation_svc, ui_controls)`:

- `self.page`, `self.repo`, `self.translation`
- `self.open_banner = ui_controls['open_banner']`
- `self.progress_ring = ui_controls['progress_ring']`
- `self.btn_procesar/epub/pdf = ui_controls[...]`
- **Estado de instancia**: `self.cancelar = False`, `self.contar_capitulos = 0`.

### Métodos privados

- `_instanciar_driver(self)` → de línea 1082. Usar `os.path.join(os.getcwd(), 'geckodriver', 'geckodriver.exe')` (fix path).
- `_extraer_y_guardar_contenido(self, soup, selector_css, novela_id, capitulo_id, traducir_flag, delimitador)` → de líneas 473–530. Usa `self.repo.enviar_contenido_capitulo()` y `self.translation.traducir_texto_largo()`.
- `_manejar_driver(self, driver, novela_id, capitulo_id)` → de líneas 534–578. Usa `self.repo` para `find_one` de novela y despacha según `sitio_id` a `self._extraer_y_guardar_contenido`.
- `_scraping_worker(self, cap_faltantes, novela_id, on_chapter_done)` — Lógica de líneas 1095–1181. **FIX CRÍTICO**: ya ejecuta en hilo separado. Llama `on_chapter_done(cap_id)` callback por cada capítulo completado (para actualizar UI desde la vista). Añadir `if self.cancelar: break` al inicio del loop.

### Método público

- `obtener_capitulos(self, cap_faltantes, novela_id, on_chapter_done)` — **No-bloqueante**: lanza `threading.Thread(target=self._scraping_worker, args=(...), daemon=True).start()`. Recibe callback `on_chapter_done` que la vista usará para actualizar contadores y visibilidad.
- `cancelar_scraping(self)` — Pone `self.cancelar = True`.

---

## Step 6 — Crear `views/theme.py`

Mover de nivel de módulo:

- `AppColors` clase completa de líneas 76–109.
- `create_dark_theme()` de líneas 112–148.
- Las 4 funciones `create_gradient_container`, `create_glass_container`, `create_action_button`, `create_stat_card` de líneas 150–234.

---

## Step 7 — Crear `views/home_view.py`

### Clase `HomeViewBuilder`

`__init__(self, page, repo, navigate_to_detail)`:

- `self.page`, `self.repo`, `self.navigate = navigate_to_detail`.

### Métodos

- `build(self) -> ft.View` — Lógica de `create_home_view` de líneas 1341–1446. Llama `self.repo.load_home_data()`, construye header y `GridView` con `_create_sitio_button`. **FIX: llamar `self._hide_loading()` antes del `return`**.
- `_create_sitio_button(self, sitio)` → de líneas 1185–1240. El `on_click` usa `self.navigate(id)`.
- `_show_loading(self)` / `_hide_loading(self)` — De líneas 1004–1012. Métodos de instancia sobre `self.page.splash`. **Eliminar clase `AppState`**.

---

## Step 8 — Crear `views/site_detail_view.py`

### Clase `SiteDetailViewBuilder`

`__init__(self, page, repo, navigate_to_detail, navigate_to_novela)`:

### Métodos

- `build(self, sitio_id, pagina=1, query="") -> ft.View` — Lógica de `create_detail_view` de líneas 1448–1610. Llama `self.repo.load_sitio_details_paginado(sitio_id, pagina, NOVELAS_POR_PAGINA, query=query)`.
  - **NUEVO: Buscador server-side** — Añadir `ft.TextField(hint_text="🔍 Buscar novela...", on_change=self._on_search_change)` entre `site_header` y `controles_paginacion`.
  - `_on_search_change(self, e)` — Debounce 300ms con `threading.Timer`. Al ejecutar, navega a `page.go(f"/sitio/{sitio_id}?pagina=1&q={query}")`. El `route_change` del orquestador extrae `q` del query string y lo pasa a `build()`.
- `_create_novela_card(self, novela)` → de líneas 1240–1339. El `on_click` usa `self.navigate_to_novela(id)`.

---

## Step 9 — Crear `views/novel_detail_view.py`

### Clase `NovelDetailViewBuilder`

`__init__(self, page, repo, export_svc, scraping_svc, navigate_to_detail, ui_controls)`:

- `self.page`, `self.repo`, `self.export`, `self.scraping`, `self.navigate`.
- Recibe `ui_controls` dict con `btn_epub`, `btn_pdf`, `btn_procesar`, `progress_ring`, `txt_number`, `open_banner`.

### Estado como atributos de instancia

Reemplaza los 11 `global` de líneas 1603–1613:

- `self.contar_capitulos`, `self.lista_capitulos`, `self.ids_contenido`, `self.mapa_indice`, `self.pagina_actual`, `self.todos_capitulos`, `self.debounce_timer`, `self.lv_capitulos`, `self.spinner`, `self.total_paginas`.

### Métodos

- `build(self, novela_id) -> ft.View` — Lógica de `create_novel_detail_view` de líneas 1603–2048. **FIX: llamar `self._hide_loading()` antes del `return`**. **Eliminar** dict `etiquetas` (línea 1820) y constantes duplicadas (línea 1816).
  - Wiring de botones: `btn_epub.on_click = lambda _: self.export.crear_epub(novela, self.todos_capitulos)`. Igual para `btn_pdf` y `btn_procesar.on_click = lambda _: self.scraping.obtener_capitulos(faltantes, novela_id, self._on_chapter_done)`.
  - **NUEVO: Buscador de capítulos** — Añadir `ft.TextField(hint_text="🔍 Buscar capítulo...", on_change=self._on_search_caps)` antes de la fila de paginación, dentro del panel de capítulos.
- `_on_search_caps(self, e)` — Debounce 300ms. Si query vacío, restaura paginación normal con `self._actualizar_lista(self.pagina_actual)`. Si no, llama `self.repo.buscar_capitulos(novela_id, query)` y reemplaza `self.lv_capitulos.controls` con los resultados filtrados.
- `_create_chapter_item(self, capitulo, index)` → de líneas 1656–1692.
- `_obtener_pagina(self, pagina)` → de línea 1694.
- `_actualizar_lista(self, pagina)` → de línea 1700. Usa `self.pagina_actual` en vez de `global`.
- `_ir_anterior(self, e)` / `_ir_siguiente(self, e)` / `_ir_a_pagina_debounced(self, e)`.
- `_calcular_visibilidad(self, cap_id)` → de línea 716. Usa `self.mapa_indice` y `self.pagina_actual`.
- `_on_chapter_done(self, cap_id)` — Callback invocado por `ScrapingService` por cada capítulo completado. Actualiza `self.contar_capitulos += 1`, `self.ids_contenido.add(cap_id)`, actualiza UI de visibilidad igual que líneas 1115–1137, y `self.page.update()`.
- `_show_loading(self)` / `_hide_loading(self)`.

### `views/__init__.py`

```python
from .theme import AppColors, create_dark_theme
from .home_view import HomeViewBuilder
from .site_detail_view import SiteDetailViewBuilder
from .novel_detail_view import NovelDetailViewBuilder
```

---

## Step 10 — Refactorizar `recopilarnovelas_flet.py` como orquestador (~70 líneas)

```python
import flet as ft
from config import Database
from repositories import DataRepository
from services import TranslationService, ExportService, ScrapingService
from views import AppColors, create_dark_theme, HomeViewBuilder, SiteDetailViewBuilder, NovelDetailViewBuilder
import logging

logger = logging.getLogger(__name__)

def main(page: ft.Page):
    page.title = "📚 Novelas Manager"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = create_dark_theme()
    page.bgcolor = AppColors.BG_DARK
    page.padding = 0
    page.window.min_width = 800
    page.window.min_height = 600

    # Infra
    db = Database()
    db.ensure_indexes()
    repo = DataRepository(db)
    translation = TranslationService()

    # UI compartida
    filepicker = ft.FilePicker()
    page.overlay.append(filepicker)

    banner = ft.Banner(...)
    progress_ring = ft.ProgressRing(...)
    txt_number = ft.Text(...)
    btn_epub = ft.ElevatedButton(...)
    btn_pdf = ft.ElevatedButton(...)
    btn_procesar = ft.ElevatedButton(...)

    def close_banner(e):
        page.close(banner)

    def open_banner(fondo, icono, contenido):
        banner.bgcolor = fondo
        banner.leading = icono
        banner.content.controls = contenido
        page.open(banner)

    ui_controls = {
        'btn_epub': btn_epub, 'btn_pdf': btn_pdf,
        'btn_procesar': btn_procesar, 'progress_ring': progress_ring,
        'txt_number': txt_number, 'open_banner': open_banner,
    }

    # Servicios
    export_svc = ExportService(page, repo, translation, filepicker, ui_controls)
    scraping_svc = ScrapingService(page, repo, translation, ui_controls)

    # Navegación
    def navigate_to_detail(sitio_id):
        page.go(f"/sitio/{sitio_id}")

    def navigate_to_novela(novel_id):
        page.go(f"/novela/{novel_id}")

    # Builders
    home = HomeViewBuilder(page, repo, navigate_to_detail)
    site = SiteDetailViewBuilder(page, repo, navigate_to_detail, navigate_to_novela)
    novel = NovelDetailViewBuilder(page, repo, export_svc, scraping_svc, navigate_to_detail, ui_controls)

    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(home.build())
        else:
            parts = page.route.split("?")[0].split("/")
            qp = {}
            if "?" in page.route:
                try:
                    qp = dict(p.split("=") for p in page.route.split("?")[1].split("&") if p)
                except ValueError:
                    pass
            pagina = int(qp.get("pagina", 1))
            query = qp.get("q", "")
            if len(parts) > 2 and parts[1] == "sitio":
                page.views.append(site.build(parts[2], pagina=pagina, query=query))
            elif len(parts) > 2 and parts[1] == "novela":
                page.views.append(novel.build(parts[2]))
        page.update()

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)
```

### Eliminar del archivo original

~2020 líneas. Eliminar imports no usados: `pandas`, `langdetect`/`DetectorFactory`, `undetected_chromedriver`, `ChromeDriverManager`, `By`, `csv`, duplicado de `os`, `AppState`, `save_file_path`.

---

## Bugs corregidos en esta refactorización

| Prioridad | Bug | Fix | Ubicación |
|---|---|---|---|
| 🔴 | Scraping bloquea UI | `threading.Thread` en `ScrapingService.obtener_capitulos()` | `services/scraping_service.py` |
| 🔴 | `hide_loading()` nunca llamado | `self._hide_loading()` al final de cada `build()` | `views/home_view.py`, `views/novel_detail_view.py` |
| 🔴 | `global`/`nonlocal` confusión | Atributos de instancia `self.x` en cada clase | Todos los módulos |
| 🟠 | 3 helpers definidas no usadas | Métodos privados invocados en `ExportService` | `services/export_service.py` |
| 🟠 | Código duplicado epub/pdf | Consolidado en `_preparar_ui`/`_actualizar_progreso`/`_finalizar_ui` | `services/export_service.py` |
| 🟡 | Constantes duplicadas L55+L1816 | Una sola fuente en `constants.py` | `config/constants.py` |
| 🟡 | `comparar_diccionarios` ineficiente | `set difference` en `DataRepository` | `repositories/data_repository.py` |
| 🟡 | `etiquetas` dict no usado | Eliminado | — |
| 🟡 | 8 imports no usados | Eliminados | `recopilarnovelas_flet.py` |
| 🟢 | `MongoClient` nunca cerrado | `Database.close()` disponible | `config/database.py` |
| 🟢 | Sin índices MongoDB | `ensure_indexes()` al inicio | `config/database.py` |
| 🟢 | Geckodriver path con `/` | `os.path.join` correcto | `services/scraping_service.py` |
