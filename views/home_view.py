"""Vista Home – lista de sitios disponibles."""

import logging
import flet as ft

from views.theme import AppColors

logger = logging.getLogger(__name__)


class HomeViewBuilder:
    """Construye la vista principal que muestra los sitios disponibles."""

    def __init__(self, page, repo, navigate_to_detail):
        self.page = page
        self.repo = repo
        self.navigate_to_detail = navigate_to_detail

    # ------------------------------------------------------------------
    # Loading helpers – FIX: hide_loading siempre se invoca
    # ------------------------------------------------------------------
    def _show_loading(self):
        self.page.splash = ft.ProgressBar(color=AppColors.PRIMARY_LIGHT, bgcolor=AppColors.BG_ELEVATED)
        self.page.update()

    def _hide_loading(self):
        self.page.splash = None
        self.page.update()

    # ------------------------------------------------------------------
    # Componentes
    # ------------------------------------------------------------------
    def _create_sitio_button(self, sitio):
        page = self.page
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.LANGUAGE_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=36),
                        padding=15,
                        border_radius=50,
                        bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
                    ),
                    ft.Text(sitio['nombre'], size=14, weight=ft.FontWeight.W_600,
                            color=AppColors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        sitio.get('url', 'Sin URL')[:30] + '...' if len(sitio.get('url', '')) > 30 else sitio.get('url', 'Sin URL'),
                        size=10, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=20,
            border_radius=16,
            bgcolor=AppColors.BG_CARD,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=15,
                color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
                offset=ft.Offset(0, 4),
            ),
            on_click=lambda e, sid=sitio['_id']: self.navigate_to_detail(sid),
            on_hover=lambda e: setattr(e.control, 'bgcolor', AppColors.BG_ELEVATED if e.data == "true" else AppColors.BG_CARD) or page.update(),
            ink=True,
            ink_color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
            tooltip=f"🌐 Ver novelas de {sitio['nombre']}",
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self):
        self._show_loading()
        try:
            sitios = self.repo.load_home_data()

            header = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, size=40, color=AppColors.PRIMARY_LIGHT),
                                ft.Column(
                                    controls=[
                                        ft.Text("Novelas Manager", size=28, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                                        ft.Text("Gestiona y descarga tus novelas favoritas", size=13, color=AppColors.TEXT_MUTED),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=15,
                        ),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(ft.Icons.LANGUAGE, color=AppColors.SECONDARY, size=18),
                                            ft.Text(f"{len(sitios)} Sitios", size=13, color=AppColors.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                                        ], spacing=6),
                                        padding=ft.Padding(12, 8, 12, 8),
                                        border_radius=20,
                                        bgcolor=ft.Colors.with_opacity(0.1, AppColors.SECONDARY),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            margin=ft.Margin(0, 10, 0, 0),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=ft.Padding(20, 25, 20, 20),
                margin=ft.Margin(20, 0, 20, 10),
                border_radius=20,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[AppColors.BG_CARD, AppColors.BG_ELEVATED],
                ),
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.PRIMARY)),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=20,
                    color=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
                    offset=ft.Offset(0, 4),
                ),
            )

            return ft.View(
                "/",
                [
                    ft.AppBar(
                        title=ft.Row([
                            ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=24),
                            ft.Text("  Sitios de Novelas", weight=ft.FontWeight.W_600),
                        ]),
                        bgcolor=AppColors.BG_CARD,
                        center_title=False,
                        elevation=0,
                    ),
                    header,
                    ft.Container(
                        content=ft.Text("📚 Selecciona un sitio para explorar", size=14,
                                        color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_500),
                        padding=ft.Padding(25, 10, 25, 5),
                    ),
                    ft.GridView(
                        expand=True,
                        runs_count=5,
                        max_extent=220,
                        spacing=20,
                        run_spacing=20,
                        padding=ft.Padding(20, 10, 20, 20),
                        controls=[self._create_sitio_button(sitio) for sitio in sitios],
                    ),
                ],
                bgcolor=AppColors.BG_DARK,
                padding=0,
            )
        finally:
            self._hide_loading()  # FIX: siempre se invoca
