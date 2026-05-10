import reflex as rx
import requests
import os
import asyncio
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")


class State(rx.State):
    """Estado global de la aplicación"""
    
    loading: bool = False
    error: str = ""
    
    sitios: list[dict] = []
    sitio_actual: dict = {}
    
    novelas: list[dict] = []
    novela_actual: dict = {}
    capitulos: list[dict] = []
    contenidos: list[dict] = []
    conteo: dict = {"cantidad_capitulos": 0, "cantidad_contenido_capitulos": 0}
    
    search_query: str = ""
    genero_seleccionado: str = ""
    generos_disponibles: list[str] = []
    
    pagina_actual: int = 1
    novels_per_page: int = 30
    caps_per_page: int = 50
    
    pagina_capitulos: int = 1

    @rx.event(background=True)
    async def load_sitios(self):
        self.loading = True
        self.error = ""
        try:
            async with self.background_task():
                response = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/sitios/?format=json", timeout=10)
                )
                if response.status_code == 200:
                    self.sitios = response.json()
                else:
                    self.error = f"Error al cargar sitios: {response.status_code}"
        except Exception as e:
            self.error = f"Error de conexión: {str(e)}"
        finally:
            self.loading = False

    @rx.event(background=True)
    async def load_sitio_detalle(self, sitio_id: str):
        self.loading = True
        self.error = ""
        try:
            async with self.background_task():
                sitio_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/sitios/{sitio_id}/", timeout=10)
                )
                if sitio_req.status_code == 200:
                    self.sitio_actual = sitio_req.json()
                else:
                    self.error = "Sitio no encontrado"
                    self.loading = False
                    return
                
                novelas_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/novelassitio/{sitio_id}/", timeout=10)
                )
                if novelas_req.status_code == 200:
                    self.novelas = novelas_req.json()
                
                generos_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/generos/{sitio_id}/", timeout=10)
                )
                if generos_req.status_code == 200:
                    self.generos_disponibles = generos_req.json().get("generos", [])
                
                self.pagina_actual = 1
                self.search_query = ""
                self.genero_seleccionado = ""
        except Exception as e:
            self.error = f"Error al cargar sitio: {str(e)}"
        finally:
            self.loading = False

    @rx.event(background=True)
    async def load_novela_detalle(self, novela_id: str):
        self.loading = True
        self.error = ""
        try:
            async with self.background_task():
                novela_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/novelas/{novela_id}/", timeout=10)
                )
                if novela_req.status_code == 200:
                    self.novela_actual = novela_req.json()
                else:
                    self.error = "Novela no encontrada"
                    self.loading = False
                    return
                
                capitulos_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/capitulosnovela/{novela_id}/", timeout=10)
                )
                if capitulos_req.status_code == 200:
                    self.capitulos = capitulos_req.json()
                
                conteo_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/conteocapitulosnovela/{novela_id}/", timeout=10)
                )
                if conteo_req.status_code == 200:
                    self.conteo = conteo_req.json()
                
                contenidos_req = await asyncio.to_thread(
                    lambda: requests.get(f"{API_URL}/api/contenidocapitulo/", timeout=10)
                )
                if contenidos_req.status_code == 200:
                    self.contenidos = contenidos_req.json()
                
                self.pagina_capitulos = 1
        except Exception as e:
            self.error = f"Error al cargar novela: {str(e)}"
        finally:
            self.loading = False

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value
        self.pagina_actual = 1

    @rx.event
    def set_genero_seleccionado(self, value: str):
        self.genero_seleccionado = value
        self.pagina_actual = 1

    @rx.event
    def ir_pagina(self, pagina: int):
        total_paginas = self.total_paginas_novelas
        if pagina < 1:
            pagina = 1
        if pagina > total_paginas:
            pagina = total_paginas
        self.pagina_actual = pagina

    @rx.event
    def ir_pagina_capitulos(self, pagina: int):
        total_paginas = self.total_paginas_capitulos
        if pagina < 1:
            pagina = 1
        if pagina > total_paginas:
            pagina = total_paginas
        self.pagina_capitulos = pagina

    @property
    def novelas_filtradas(self) -> list[dict]:
        resultado = self.novelas
        if self.search_query.strip():
            query = self.search_query.lower()
            resultado = [n for n in resultado if query in n.get("nombre", "").lower()]
        if self.genero_seleccionado:
            resultado = [n for n in resultado if self.genero_seleccionado in n.get("genero", "")]
        return resultado

    @property
    def total_paginas_novelas(self) -> int:
        return max(1, (len(self.novelas_filtradas) + self.novels_per_page - 1) // self.novels_per_page)

    @property
    def novelas_pagina(self) -> list[dict]:
        inicio = (self.pagina_actual - 1) * self.novels_per_page
        fin = inicio + self.novels_per_page
        return self.novelas_filtradas[inicio:fin]

    @property
    def total_paginas_capitulos(self) -> int:
        return max(1, (len(self.capitulos) + self.caps_per_page - 1) // self.caps_per_page)

    @property
    def capitulos_pagina(self) -> list[dict]:
        inicio = (self.pagina_capitulos - 1) * self.caps_per_page
        fin = inicio + self.caps_per_page
        return self.capitulos[inicio:fin]

    @property
    def capitulo_ids_con_contenido_set(self) -> list[str]:
        ids = []
        for c in self.contenidos:
            cap_id = c.get("capitulo_id")
            if isinstance(cap_id, dict):
                ids.append(str(cap_id.get("_id", "")))
            else:
                ids.append(str(cap_id))
        return ids

    @property
    def total_capitulos(self) -> int:
        return self.conteo.get("cantidad_capitulos", len(self.capitulos))

    @property
    def capitulos_descargados(self) -> int:
        return self.conteo.get("cantidad_contenido_capitulos", 0)

    @property
    def porcentaje_progreso(self) -> float:
        if self.total_capitulos == 0:
            return 0.0
        return (self.capitulos_descargados / self.total_capitulos) * 100

    @property
    def todos_descargados(self) -> bool:
        return self.total_capitulos > 0 and self.capitulos_descargados >= self.total_capitulos

    @property
    def generos_lista(self) -> list[str]:
        return self.generos_disponibles

    @property
    def epub_url(self) -> str:
        return f"{API_URL}/generar_epub/{self.novela_actual.get('_id', '')}/"

    @property
    def pdf_url(self) -> str:
        return f"{API_URL}/generar_pdf/{self.novela_actual.get('_id', '')}/"


def status_badge(status: str) -> rx.Component:
    status_lower = status.lower() if status else ""
    if "complet" in status_lower:
        class_name = "status-completed"
        label = status or "Completo"
    elif "ongoing" in status_lower or "emision" in status_lower:
        class_name = "status-ongoing"
        label = status or "En emisión"
    else:
        class_name = "status-unknown"
        label = status or "Desconocido"
    
    return rx.badge(label[:15], class_name=f"status-badge {class_name}")


def site_card(sitio: dict) -> rx.Component:
    url = sitio.get("url", "Sin URL")
    if len(url) > 30:
        url = url[:30] + "…"
    
    return rx.link(
        rx.card(
            rx.vstack(
                rx.box(rx.text("🌐", font_size="28px"), class_name="icon-circle"),
                rx.text(sitio.get("nombre", "Sin nombre"), class_name="site-name"),
                rx.text(url, class_name="site-url"),
                spacing="2",
                align="center",
            ),
            class_name="site-card",
        ),
        href=f"/sitio/{sitio.get('_id', '')}",
        underline="none",
    )


def novel_card(novela: dict) -> rx.Component:
    imagen_url = novela.get("imagen_url", "/imagenes/no-cover.svg")
    nombre = novela.get("nombre", "Sin título")
    autor = novela.get("autor", "Desconocido")
    status = novela.get("status", "")
    
    return rx.link(
        rx.box(
            rx.image(src=imagen_url, alt=f"Portada de {nombre}", class_name="novel-cover-img"),
            rx.box(class_name="overlay"),
            rx.vstack(
                status_badge(status),
                rx.box(
                    rx.text(nombre, class_name="novel-name"),
                    rx.text(f"✍️ {autor[:20]}", class_name="novel-author"),
                    class_name="card-bottom",
                ),
                class_name="card-content",
                justify="end",
            ),
            class_name="novel-card",
        ),
        href=f"/novela/{novela.get('_id', '')}",
        underline="none",
    )


def pagination_component(pagina_actual: int, total_paginas: int, on_prev: rx.EventHandler, on_next: rx.EventHandler) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.button("‹", disabled=pagina_actual <= 1, on_click=on_prev, class_name="pagination-btn"),
            rx.box(
                rx.text(str(pagina_actual), class_name="current"),
                rx.text(" / ", class_name="separator"),
                rx.text(str(total_paginas), class_name="total"),
                class_name="pagination-info",
            ),
            rx.button("›", disabled=pagina_actual >= total_paginas, on_click=on_next, class_name="pagination-btn"),
            align="center",
            gap="2",
        ),
        class_name="pagination",
    )


def loading_spinner() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3", class_name="spinner"),
            rx.text("Cargando...", class_name="loading-text"),
            align="center",
        ),
        class_name="loading-container",
    )


def error_message(message: str) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text("⚠️", font_size="60px"),
            rx.text("Error", font_size="20px", font_weight="bold"),
            rx.text(message, color="gray"),
            rx.link(rx.button("← Volver al inicio", class_name="btn btn-process"), href="/", underline="none"),
            align="center",
            gap="4",
        ),
        class_name="error-container",
    )


def empty_state(message: str, icon: str = "📭") -> rx.Component:
    return rx.center(
        rx.vstack(rx.text(icon, font_size="40px"), rx.text(message), align="center"),
        class_name="empty-state",
    )


def info_card(icon: str, label: str, value: str) -> rx.Component:
    return rx.box(
        rx.text(icon, class_name="info-icon"),
        rx.text(label, class_name="info-label"),
        rx.text(value, class_name="info-value"),
        class_name="info-card",
    )


@rx.page(route="/", on_load=State.load_sitios)
def index() -> rx.Component:
    return rx.container(
        rx.box(
            rx.heading("📖 Novelas Manager", size="8"),
            rx.text("Gestiona y descarga tus novelas favoritas"),
            rx.badge(f"🌐 {len(State.sitios)} Sitios disponibles", class_name="badge"),
            class_name="home-header",
        ),
        rx.text("📚 Selecciona un sitio para explorar", class_name="home-subtitle"),
        rx.cond(
            State.loading,
            loading_spinner(),
            rx.cond(
                State.error,
                error_message(State.error),
                rx.cond(
                    len(State.sitios) == 0,
                    empty_state("No se encontraron sitios. Verifica la conexión con la API."),
                    rx.grid(rx.foreach(State.sitios, site_card), class_name="grid grid-sites"),
                ),
            ),
        ),
        class_name="page-container",
    )


@rx.page(route="/sitio/[id]", on_load=State.load_sitio_detalle)
def sitio_detalle() -> rx.Component:
    return rx.container(
        rx.box(
            rx.link(rx.text("←", class_name="appbar-back"), href="/", underline="none"),
            rx.hstack(rx.text("📚", class_name="icon"), rx.text(State.sitio_actual.get("nombre", ""), class_name="appbar-title"), align="center", gap="2"),
            class_name="appbar",
        ),
        rx.cond(
            State.loading,
            loading_spinner(),
            rx.cond(
                State.error,
                error_message(State.error),
                rx.fragment(
                    rx.box(
                        rx.box(class_name="icon-circle", children=rx.text("🌐", font_size="24px")),
                        rx.vstack(
                            rx.heading(State.sitio_actual.get("nombre", ""), size="6"),
                            rx.text(State.sitio_actual.get("url", "N/A"), class_name="site-url-text"),
                            align="start",
                        ),
                        rx.box(
                            rx.text(str(len(State.novelas)), class_name="stat-number"),
                            rx.text("novelas", class_name="stat-label"),
                            class_name="stat-badge",
                        ),
                        class_name="site-header",
                    ),
                    rx.box(
                        rx.hstack(
                            rx.box(
                                rx.text("🔍", class_name="search-icon"),
                                rx.input(placeholder="Buscar novela…", value=State.search_query, on_change=State.set_search_query, class_name="search-input"),
                                class_name="search-wrapper",
                            ),
                            rx.cond(
                                len(State.generos_lista) > 0,
                                rx.select(["Todos los géneros"] + State.generos_lista, value=State.genero_seleccionado, on_change=State.set_genero_seleccionado, class_name="filter-select"),
                                rx.fragment(),
                            ),
                            class_name="toolbar",
                        ),
                    ),
                    rx.cond(State.total_paginas_novelas > 1, pagination_component(State.pagina_actual, State.total_paginas_novelas, State.ir_pagina(State.pagina_actual - 1), State.ir_pagina(State.pagina_actual + 1)), rx.fragment()),
                    rx.cond(
                        len(State.novelas_filtradas) > 0,
                        rx.grid(rx.foreach(State.novelas_pagina, novel_card), class_name="grid grid-novels"),
                        empty_state("No se encontraron novelas con los filtros seleccionados."),
                    ),
                    rx.cond(State.total_paginas_novelas > 1, pagination_component(State.pagina_actual, State.total_paginas_novelas, State.ir_pagina(State.pagina_actual - 1), State.ir_pagina(State.pagina_actual + 1)), rx.fragment()),
                ),
            ),
        ),
        class_name="page-container",
    )


def format_date(timestamp) -> rx.Component:
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return rx.text(dt.strftime("%d/%m/%Y"), class_name="chapter-date")
    except:
        pass
    return rx.text("Sin fecha", class_name="chapter-date")


@rx.page(route="/novela/[id]", on_load=State.load_novela_detalle)
def novela_detalle() -> rx.Component:
    def chapter_item(cap: dict, idx: int):
        cap_id = str(cap.get("_id", ""))
        is_downloaded = rx.cond(
            rx.Var.create(State.capitulo_ids_con_contenido_set).contains(cap_id),
            True,
            False
        )
        return rx.box(
            rx.box(
                rx.text(str((State.pagina_capitulos - 1) * State.caps_per_page + idx + 1), class_name="chapter-index"),
                class_name=rx.cond(is_downloaded, "chapter-index downloaded", "chapter-index"),
            ),
            rx.box(
                rx.text(rx.cond(len(cap.get("nombre", "")) > 60, cap.get("nombre", "")[:60] + "…", cap.get("nombre", "")), class_name="chapter-name"),
                format_date(cap.get("created_at")),
                class_name="chapter-info",
            ),
            rx.text(rx.cond(is_downloaded, "✓", "○"), class_name="chapter-status-icon"),
            class_name=rx.cond(is_downloaded, "chapter-item downloaded", "chapter-item"),
        )

    return rx.container(
        rx.box(
            rx.link(rx.text("←", class_name="appbar-back"), href=rx.cond(State.novela_actual.get("sitio_id"), f"/sitio/{State.novela_actual.get('sitio_id', '')}", "/"), underline="none"),
            rx.hstack(rx.text("📖", class_name="icon"), rx.text(State.novela_actual.get("nombre", "")[:40] + rx.cond(len(State.novela_actual.get("nombre", "")) > 40, "…", ""), class_name="appbar-title"), align="center", gap="2"),
            class_name="appbar",
        ),
        rx.cond(
            State.loading,
            loading_spinner(),
            rx.cond(
                State.error,
                error_message(State.error),
                rx.box(
                    rx.box(
                        rx.box(
                            rx.image(src=rx.cond(State.novela_actual.get("imagen_url"), State.novela_actual.get("imagen_url"), "/imagenes/no-cover.svg"), alt="Portada", class_name="novel-cover-img-detail"),
                            class_name="novel-cover",
                        ),
                        rx.badge(
                            rx.cond(
                                State.novela_actual.get("status", "").lower().contains("complet"),
                                "✅",
                                rx.cond(State.novela_actual.get("status", "").lower().contains("ongoing"), "⏳", ""),
                            ),
                            State.novela_actual.get("status", "N/A"),
                            class_name=rx.cond(
                                State.novela_actual.get("status", "").lower().contains("complet"),
                                "novel-status-badge status-completed",
                                rx.cond(State.novela_actual.get("status", "").lower().contains("ongoing"), "novel-status-badge status-ongoing", "novel-status-badge status-unknown"),
                            ),
                        ),
                        class_name="novel-cover-container",
                    ),
                    rx.box(
                        rx.heading(State.novela_actual.get("nombre", ""), size="6"),
                        rx.hstack(
                            info_card("👤", "Autor", State.novela_actual.get("autor", "Desconocido")[:25]),
                            info_card("🏷️", "Género", rx.cond(len(State.novela_actual.get("genero", "").split(",")) > 0, State.novela_actual.get("genero", "").split(",")[0][:20], "N/A")),
                            info_card("📖", "Capítulos", str(len(State.capitulos))),
                            class_name="info-cards",
                            gap="2",
                            wrap="wrap",
                        ),
                        rx.box(
                            rx.text("📝 Sinopsis", font_weight="bold"),
                            rx.text(rx.cond(State.novela_actual.get("sinopsis"), rx.cond(len(State.novela_actual.get("sinopsis", "")) > 500, State.novela_actual.get("sinopsis", "")[:500] + "…", State.novela_actual.get("sinopsis", "")), "Sin sinopsis disponible."), class_name="synopsis-text"),
                            class_name="synopsis-box",
                        ),
                        rx.cond(
                            len(State.novela_actual.get("genero", "").split(",")) > 0,
                            rx.wrap(rx.foreach(State.novela_actual.get("genero", "").split(","), lambda g: rx.badge(g.strip(), class_name="genre-tag")), gap="2", class_name="genre-tags"),
                            rx.fragment(),
                        ),
                        rx.cond(State.novela_actual.get("url"), rx.link("🔗 Ver en sitio original", href=State.novela_actual.get("url"), is_external=True, class_name="original-link"), rx.fragment()),
                        class_name="novel-info",
                    ),
                    class_name="novel-detail-top",
                ),
                rx.divider(class_name="divider"),
                rx.box(
                    rx.box(
                        rx.text("📊 Progreso", font_weight="bold"),
                        rx.box(
                            rx.text(str(State.capitulos_descargados), class_name="downloaded"),
                            rx.text(f"/ {State.total_capitulos}", class_name="total"),
                            class_name="progress-numbers",
                        ),
                        rx.box(
                            rx.box(class_name=rx.cond(State.porcentaje_progreso >= 100, "progress-bar-fill complete", "progress-bar-fill partial"), style={"width": rx.cond(State.porcentaje_progreso > 100, "100%", f"{State.porcentaje_progreso}%")}),
                            class_name="progress-bar-container",
                        ),
                        rx.text(f"{State.porcentaje_progreso:.1f}%", class_name="progress-percent"),
                        rx.vstack(
                            rx.link(rx.button("📖 EPUB", class_name="btn btn-epub"), href=State.epub_url, is_external=True, underline="none", style=rx.cond(State.todos_descargados, {"opacity": 1, "pointer_events": "auto"}, {"opacity": 0.4, "pointer_events": "none"})),
                            rx.link(rx.button("📄 PDF", class_name="btn btn-pdf"), href=State.pdf_url, is_external=True, underline="none", style=rx.cond(State.todos_descargados, {"opacity": 1, "pointer_events": "auto"}, {"opacity": 0.4, "pointer_events": "none"})),
                            width="100%",
                            class_name="action-buttons",
                        ),
                        rx.cond(State.todos_descargados, rx.fragment(), rx.text(f"⚠️ Faltan {State.total_capitulos - State.capitulos_descargados} capítulos por descargar", class_name="warning-text")),
                        class_name="progress-panel",
                    ),
                    rx.box(
                        rx.hstack(rx.text("📋 Capítulos", font_weight="bold"), rx.badge(f"{State.capitulos_descargados}/{State.total_capitulos}", class_name="count-badge"), class_name="chapters-header"),
                        rx.cond(State.total_paginas_capitulos > 1, pagination_component(State.pagina_capitulos, State.total_paginas_capitulos, State.ir_pagina_capitulos(State.pagina_capitulos - 1), State.ir_pagina_capitulos(State.pagina_capitulos + 1)), rx.fragment()),
                        rx.box(
                            rx.foreach(State.capitulos_pagina, lambda cap, idx: chapter_item(cap, idx)),
                            class_name="chapter-list",
                        ),
                        rx.cond(len(State.capitulos) == 0, empty_state("No hay capítulos registrados"), rx.fragment()),
                        class_name="chapters-panel",
                    ),
                    class_name="novel-detail-bottom",
                ),
                class_name="novel-detail",
            ),
        ),
        class_name="page-container",
    )


app = rx.App()
