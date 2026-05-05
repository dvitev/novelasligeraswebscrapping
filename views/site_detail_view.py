"""Vista de detalle de sitio – lista paginada de novelas con búsqueda."""

import logging
import threading
import flet as ft

from config.constants import NOVELAS_POR_PAGINA
from views.theme import AppColors

logger = logging.getLogger(__name__)


class SiteDetailViewBuilder:
    """Construye la vista de un sitio con sus novelas paginadas y búsqueda server-side."""

    def __init__(self, page, repo, navigate_to_home, navigate_to_novela):
        self.page = page
        self.repo = repo
        self.navigate_to_home = navigate_to_home
        self.navigate_to_novela = navigate_to_novela
        self._debounce_page_timer = None

    # ------------------------------------------------------------------
    # Navegación de página
    # ------------------------------------------------------------------
    def _ir_pagina(self, sitio_id, pagina, query=""):
        """Navega a la página indicada conservando el query de búsqueda."""
        q_part = f"&query={query}" if query else ""
        self.page.go(f"/sitio/{sitio_id}?pagina={pagina}{q_part}")

    def _ir_a_pagina_debounced(self, sitio_id, total_paginas, query, input_ir_pagina):
        """Navega a la página escrita en el input con debounce de 200 ms."""
        if self._debounce_page_timer:
            self._debounce_page_timer.cancel()

        def ejecutar():
            try:
                p = int(input_ir_pagina.value or "1")
                p = max(1, min(p, total_paginas))
                self._ir_pagina(sitio_id, p, query)
            except ValueError:
                pass

        self._debounce_page_timer = threading.Timer(0.2, ejecutar)
        self._debounce_page_timer.start()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self, sitio_id, pagina=1, query=""):
        logger.info(f"Cargando vista de sitio {sitio_id}, página {pagina}, query='{query}'")
        sitio, novelas_pagina, total_novelas = self.repo.load_sitio_details_paginado(
            sitio_id, pagina, NOVELAS_POR_PAGINA, query=query,
        )

        if not sitio:
            return self._error_view(sitio_id)

        total_paginas = max(1, (total_novelas + NOVELAS_POR_PAGINA - 1) // NOVELAS_POR_PAGINA)
        page = self.page

        # --- Buscador con debounce 300 ms ---
        debounce_timer = None

        def on_search_change(e):
            nonlocal debounce_timer
            if debounce_timer:
                debounce_timer.cancel()
            text = e.control.value.strip()

            def ejecutar():
                q_part = f"&query={text}" if text else ""
                page.go(f"/sitio/{sitio_id}?pagina=1{q_part}")

            debounce_timer = threading.Timer(0.3, ejecutar)
            debounce_timer.start()

        search_field = ft.TextField(
            value=query,
            hint_text="🔍 Buscar novela…",
            width=300,
            height=38,
            text_size=13,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY_LIGHT,
            on_change=on_search_change,
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_radius=10,
        )

        # --- Paginación ---
        controles_paginacion = []
        if total_paginas > 1:
            btn_anterior = ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT_ROUNDED, icon_size=24,
                    disabled=(pagina <= 1),
                    on_click=lambda _: self._ir_pagina(sitio_id, pagina - 1, query) if pagina > 1 else None,
                    icon_color=AppColors.PRIMARY_LIGHT if pagina > 1 else AppColors.TEXT_MUTED,
                    tooltip="Página Anterior",
                ),
                bgcolor=AppColors.BG_CARD if pagina > 1 else ft.Colors.TRANSPARENT,
                border_radius=10,
            )
            txt_pagina = ft.Container(
                content=ft.Row([
                    ft.Text(f"{pagina}", size=16, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY_LIGHT),
                    ft.Text(" / ", size=14, color=AppColors.TEXT_MUTED),
                    ft.Text(f"{total_paginas}", size=14, color=AppColors.TEXT_SECONDARY),
                ], spacing=2),
                padding=ft.Padding(15, 8, 15, 8),
                border_radius=10,
                bgcolor=AppColors.BG_CARD,
            )
            btn_siguiente = ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_size=24,
                    disabled=(pagina >= total_paginas),
                    on_click=lambda _: self._ir_pagina(sitio_id, pagina + 1, query) if pagina < total_paginas else None,
                    icon_color=AppColors.PRIMARY_LIGHT if pagina < total_paginas else AppColors.TEXT_MUTED,
                    tooltip="Página Siguiente",
                ),
                bgcolor=AppColors.BG_CARD if pagina < total_paginas else ft.Colors.TRANSPARENT,
                border_radius=10,
            )
            input_ir_pagina = ft.TextField(
                value=str(pagina),
                width=50,
                height=32,
                text_size=11,
                text_align=ft.TextAlign.CENTER,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY_LIGHT,
                input_filter=ft.NumbersOnlyInputFilter(),
                on_change=lambda _: self._ir_a_pagina_debounced(
                    sitio_id, total_paginas, query, input_ir_pagina,
                ),
            )
            spinner_paginacion = ft.ProgressRing(
                width=16, height=16, stroke_width=2,
                color=AppColors.PRIMARY_LIGHT, visible=False,
            )
            controles_paginacion = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            btn_anterior, txt_pagina, btn_siguiente,
                            ft.Container(width=10),
                            ft.Text("Ir a:", size=10, color=AppColors.TEXT_MUTED),
                            input_ir_pagina,
                            spinner_paginacion,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=ft.Padding(0, 10, 0, 10),
                ),
            ]

        # --- Header del sitio ---
        site_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.LANGUAGE_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=28),
                        padding=12, border_radius=50,
                        bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
                    ),
                    ft.Column([
                        ft.Text(sitio['nombre'], size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                        ft.Text(sitio.get('url', 'N/A'), size=11, color=AppColors.TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{total_novelas}", size=24, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                            ft.Text("novelas", size=11, color=AppColors.TEXT_MUTED),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        padding=ft.Padding(15, 10, 15, 10),
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.1, AppColors.SECONDARY),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=ft.Padding(20, 15, 20, 15),
            margin=ft.Margin(15, 5, 15, 10),
            border_radius=16,
            bgcolor=AppColors.BG_CARD,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
        )

        return ft.View(
            f"/sitio/{sitio_id}",
            [
                ft.AppBar(
                    title=ft.Row([
                        ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=22),
                        ft.Text(f"  {sitio['nombre']}", weight=ft.FontWeight.W_600, size=16),
                    ]),
                    bgcolor=AppColors.BG_CARD,
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK_ROUNDED,
                        on_click=lambda _: self.navigate_to_home(),
                        icon_color=AppColors.TEXT_PRIMARY,
                        tooltip="Volver al inicio",
                    ),
                    elevation=0,
                    actions=[search_field, ft.Container(width=15)],
                ),
                site_header,
                *controles_paginacion,
                ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=200,
                    spacing=15,
                    run_spacing=20,
                    padding=ft.Padding(15, 5, 15, 15),
                    controls=[self._create_novela_card(novela) for novela in novelas_pagina],
                ),
                *controles_paginacion,
            ],
            bgcolor=AppColors.BG_DARK,
            spacing=5,
            padding=0,
        )

    # ------------------------------------------------------------------
    # Tarjeta de novela
    # ------------------------------------------------------------------
    def _create_novela_card(self, novela):
        page = self.page
        status = novela.get('status', '').lower()
        status_color = (
            AppColors.ACCENT_GREEN if 'complet' in status
            else AppColors.ACCENT_ORANGE if 'ongoing' in status
            else AppColors.TEXT_MUTED
        )
        status_text = novela.get('status', 'Desconocido')[:15]

        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Image(
                            src=novela['imagen_url'],
                            fit=ft.ImageFit.COVER,
                            repeat=ft.ImageRepeat.NO_REPEAT,
                            border_radius=ft.border_radius.all(14),
                        ),
                        border_radius=ft.border_radius.all(14),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                    ft.Container(
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_center,
                            end=ft.alignment.bottom_center,
                            colors=[
                                ft.Colors.TRANSPARENT, ft.Colors.TRANSPARENT,
                                ft.Colors.with_opacity(0.7, AppColors.BG_DARK),
                                ft.Colors.with_opacity(0.95, AppColors.BG_DARK),
                            ],
                        ),
                        border_radius=ft.border_radius.all(14),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(
                                    content=ft.Text(status_text, size=9, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                    bgcolor=status_color,
                                    padding=ft.Padding(8, 4, 8, 4),
                                    border_radius=8,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(expand=True),
                                ft.Text(novela['nombre'], size=11, weight=ft.FontWeight.W_600,
                                        color=AppColors.TEXT_PRIMARY, max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.LEFT),
                                ft.Text(f"✍️ {novela.get('autor', 'Desconocido')[:20]}", size=9,
                                        color=AppColors.TEXT_MUTED, max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.Padding(10, 8, 10, 12),
                    ),
                ],
            ),
            width=180, height=260,
            border_radius=14,
            bgcolor=AppColors.BG_CARD,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=12,
                color=ft.Colors.with_opacity(0.25, AppColors.BG_DARK),
                offset=ft.Offset(0, 4),
            ),
            on_click=lambda e, nid=novela['_id']: self.navigate_to_novela(nid),
            on_hover=lambda e: (
                setattr(e.control, 'scale', 1.03 if e.data == "true" else 1.0),
                setattr(e.control, 'shadow', ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20 if e.data == "true" else 12,
                    color=ft.Colors.with_opacity(0.4 if e.data == "true" else 0.25, AppColors.PRIMARY),
                    offset=ft.Offset(0, 8 if e.data == "true" else 4),
                )),
                page.update(),
            ),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            ink=True,
            ink_color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
        )

    # ------------------------------------------------------------------
    # Error view
    # ------------------------------------------------------------------
    def _error_view(self, sitio_id):
        return ft.View(
            f"/sitio/{sitio_id}",
            [
                ft.AppBar(
                    title=ft.Text("Error", size=16),
                    bgcolor=AppColors.ERROR,
                    leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.navigate_to_home(),
                                          icon_color=AppColors.TEXT_PRIMARY),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=60, color=AppColors.ERROR),
                        ft.Text("Sitio no encontrado", size=20, color=AppColors.TEXT_PRIMARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ],
            bgcolor=AppColors.BG_DARK,
        )
