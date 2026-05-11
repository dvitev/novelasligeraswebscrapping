"""
Novelas Manager – Punto de entrada de la aplicación Flet.

Orquesta la inicialización de servicios, repositorios y vistas.
Toda la lógica reside en los paquetes config/, repositories/, services/ y views/.
"""

import logging
import flet as ft

from config.database import Database
from repositories.data_repository import DataRepository
from services.translation_service import TranslationService
from services.export_service import ExportService
from services.scraping_service import ScrapingService
from views.theme import AppColors, create_dark_theme
from views.home_view import HomeViewBuilder
from views.site_detail_view import SiteDetailViewBuilder
from views.novel_detail_view import NovelDetailViewBuilder

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    """Punto de entrada principal de la aplicación Flet."""
    page.title = "📚 Novelas Manager"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = create_dark_theme()
    page.bgcolor = AppColors.BG_DARK
    page.padding = 0
    page.window.min_width = 800
    page.window.min_height = 600

    # ── Infraestructura ──────────────────────────────────────
    db = Database()
    repo = DataRepository(db)
    translation_svc = TranslationService()

    filepicker = ft.FilePicker()
    page.overlay.append(filepicker)

    # ── Controles compartidos ────────────────────────────────
    txt_number = ft.Text(
        value="0", text_align=ft.TextAlign.CENTER, size=32,
        weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT,
    )
    btn_epub = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.BOOK_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
            ft.Text("EPUB", weight=ft.FontWeight.W_700, size=14),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=AppColors.ACCENT_GREEN, color=AppColors.TEXT_PRIMARY, expand=True,
        tooltip="📖 Generar archivo EPUB",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14), elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.ACCENT_GREEN),
            animation_duration=300,
        ),
    )
    btn_pdf = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.PICTURE_AS_PDF_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
            ft.Text("PDF", weight=ft.FontWeight.W_700, size=14),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=AppColors.ACCENT_RED, color=AppColors.TEXT_PRIMARY, expand=True,
        tooltip="📄 Generar archivo PDF",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14), elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.ACCENT_RED),
            animation_duration=300,
        ),
    )
    btn_procesar = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.DOWNLOAD_FOR_OFFLINE_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
            ft.Text("PROCESAR", weight=ft.FontWeight.W_700, size=14),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_PRIMARY, expand=True,
        tooltip="⚡ Obtener capítulos faltantes",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14), elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.PRIMARY),
            animation_duration=300,
        ),
    )
    progress_ring = ft.ProgressRing(
        visible=False, stroke_width=4, color=AppColors.PRIMARY_LIGHT,
        stroke_cap=ft.StrokeCap.ROUND,
    )

    # ── Banner ───────────────────────────────────────────────
    banner = ft.Banner(
        content=ft.Row([]),
        actions=[ft.TextButton(text="✕ Cerrar",
                               on_click=lambda _: page.close(banner),
                               style=ft.ButtonStyle(color=AppColors.TEXT_PRIMARY))],
        bgcolor=AppColors.BG_ELEVATED,
        surface_tint_color=AppColors.PRIMARY,
    )

    def open_banner(fondo, icono, contenido):
        banner.bgcolor = fondo
        banner.leading = icono
        banner.content.controls = contenido
        page.open(banner)

    # ── Diccionario de controles compartidos ─────────────────
    ui_controls = {
        'btn_epub': btn_epub,
        'btn_pdf': btn_pdf,
        'btn_procesar': btn_procesar,
        'progress_ring': progress_ring,
        'txt_number': txt_number,
        'open_banner': open_banner,
    }

    # ── Servicios ────────────────────────────────────────────
    export_svc = ExportService(page, repo, translation_svc, filepicker, ui_controls)
    scraping_svc = ScrapingService(page, repo, translation_svc, ui_controls)

    # ── Navegación ───────────────────────────────────────────
    def navigate_to_home():
        page.go("/")

    def navigate_to_detail(sitio_id):
        page.go(f"/sitio/{sitio_id}")

    def navigate_to_novela_detail(novel_id):
        page.go(f"/novela/{novel_id}")

    # ── Builders de vistas ───────────────────────────────────
    home_builder = HomeViewBuilder(page, repo, navigate_to_detail)
    site_builder = SiteDetailViewBuilder(page, repo, navigate_to_home, navigate_to_novela_detail)
    novel_builder = NovelDetailViewBuilder(
        page, repo, export_svc, scraping_svc, navigate_to_detail, ui_controls,
    )

    # ── Enrutamiento ─────────────────────────────────────────
    def route_change(route):
        page.views.clear()

        # Parsear ruta y query params
        raw = page.route or "/"
        path = raw.split("?")[0]
        query_params = {}
        if "?" in raw:
            try:
                query_params = dict(p.split("=") for p in raw.split("?")[1].split("&") if "=" in p)
            except ValueError:
                logger.warning(f"Error al parsear query params: {raw}")

        parts = path.split("/")
        pagina = int(query_params.get("pagina", 1))
        query = query_params.get("query", "")

        if path == "/":
            page.views.append(home_builder.build())
        elif len(parts) > 2 and parts[1] == "sitio":
            page.views.append(site_builder.build(parts[2], pagina=pagina, query=query))
        elif len(parts) > 2 and parts[1] == "novela":
            page.views.append(novel_builder.build(parts[2]))

        page.update()

    page.on_route_change = route_change
    page.go(page.route)

    def on_close(event):
        """Limpieza al cerrar la aplicación."""
        repo.close()
        db.close()

    page.on_close = on_close


if __name__ == "__main__":
    ft.app(target=main)
