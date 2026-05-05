"""Vista de detalle de novela – capítulos paginados, exportación y scraping."""

import logging
import threading
from datetime import datetime

import flet as ft

from config.constants import CAPITULOS_POR_PAGINA
from views.theme import AppColors

logger = logging.getLogger(__name__)


class NovelDetailViewBuilder:
    """Construye la vista de detalle de una novela con toda su lógica interna."""

    def __init__(self, page, repo, export_svc, scraping_svc,
                 navigate_to_detail, ui_controls):
        self.page = page
        self.repo = repo
        self.export_svc = export_svc
        self.scraping_svc = scraping_svc
        self.navigate_to_detail = navigate_to_detail

        # Controles compartidos inyectados
        self.btn_epub = ui_controls['btn_epub']
        self.btn_pdf = ui_controls['btn_pdf']
        self.btn_procesar = ui_controls['btn_procesar']
        self.progress_ring = ui_controls['progress_ring']
        self.txt_number = ui_controls['txt_number']
        self.open_banner = ui_controls['open_banner']

        # Estado de instancia (sustituye global/nonlocal)
        self.contar_capitulos = 0
        self.lista_capitulos = []
        self.ids_contenido_capitulo = set()
        self.mapa_capitulo_indice = {}
        self.pagina_capitulos_actual = 1
        self.todos_capitulos = []
        self.total_paginas_capitulos = 1
        self.debounce_timer = None
        self.lv_capitulos = None
        self.spinner_paginacion = None

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
    # Paginación de capítulos
    # ------------------------------------------------------------------
    def _obtener_capitulos_pagina(self, pagina):
        inicio = (pagina - 1) * CAPITULOS_POR_PAGINA
        fin = inicio + CAPITULOS_POR_PAGINA
        return self.todos_capitulos[inicio:fin], inicio + 1

    def _actualizar_lista_capitulos(self, pagina, novela_id,
                                     txt_pagina_actual, input_ir_pagina,
                                     btn_anterior, btn_siguiente):
        self.pagina_capitulos_actual = pagina
        self.page.session.set(f"pagina_caps_{novela_id}", pagina)

        caps_pagina, offset = self._obtener_capitulos_pagina(pagina)
        nuevos = [self._create_chapter_item(cap, offset + idx) for idx, cap in enumerate(caps_pagina)]

        # Reemplazar contenido y sincronizar la referencia del ListView
        self.lista_capitulos.clear()
        self.lista_capitulos.extend(nuevos)
        if self.lv_capitulos is not None:
            self.lv_capitulos.controls = self.lista_capitulos

        txt_pagina_actual.value = f"{pagina}/{self.total_paginas_capitulos}"
        input_ir_pagina.value = str(pagina)
        btn_anterior.disabled = (pagina <= 1)
        btn_siguiente.disabled = (pagina >= self.total_paginas_capitulos)

    def _calcular_visibilidad_capitulo(self, cap_id):
        indice_global = self.mapa_capitulo_indice.get(str(cap_id), 0)
        if indice_global == 0:
            return False, -1
        inicio = (self.pagina_capitulos_actual - 1) * CAPITULOS_POR_PAGINA + 1
        fin = inicio + CAPITULOS_POR_PAGINA - 1
        es_visible = inicio <= indice_global <= fin
        indice_relativo = (indice_global - inicio) if es_visible else -1
        return es_visible, indice_relativo

    # ------------------------------------------------------------------
    # Callback de scraping – actualiza UI del capítulo descargado
    # ------------------------------------------------------------------
    def _on_chapter_done(self, cap_id):
        self.contar_capitulos += 1
        self.txt_number.value = str(self.contar_capitulos)
        self.ids_contenido_capitulo.add(str(cap_id))

        es_visible, idx_rel = self._calcular_visibilidad_capitulo(str(cap_id))
        if es_visible and 0 <= idx_rel < len(self.lista_capitulos):
            container = self.lista_capitulos[idx_rel]
            if hasattr(container, 'content') and hasattr(container.content, 'controls'):
                row_controls = container.content.controls
                if len(row_controls) >= 3:
                    row_controls[0].bgcolor = AppColors.ACCENT_GREEN
                    row_controls[0].content.color = AppColors.TEXT_PRIMARY
                    if hasattr(row_controls[1], 'controls') and len(row_controls[1].controls) > 0:
                        row_controls[1].controls[0].color = AppColors.TEXT_PRIMARY
                    row_controls[2].name = ft.Icons.CHECK_CIRCLE_ROUNDED
                    row_controls[2].color = AppColors.ACCENT_GREEN
                    container.bgcolor = ft.Colors.with_opacity(0.05, AppColors.ACCENT_GREEN)
                    container.border = ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.ACCENT_GREEN))

    # ------------------------------------------------------------------
    # Componentes
    # ------------------------------------------------------------------
    def _create_chapter_item(self, capitulo, index):
        is_downloaded = str(capitulo['_id']) in self.ids_contenido_capitulo
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(f"{index}", size=11, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT_PRIMARY if is_downloaded else AppColors.TEXT_MUTED),
                    width=35, height=35, border_radius=8,
                    bgcolor=AppColors.ACCENT_GREEN if is_downloaded else AppColors.BG_ELEVATED,
                    alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Text(
                        capitulo['nombre'][:50] + ('...' if len(capitulo['nombre']) > 50 else ''),
                        size=12, weight=ft.FontWeight.W_500,
                        color=AppColors.TEXT_PRIMARY if is_downloaded else AppColors.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        capitulo.get('created_at', 'N/A').strftime('%d/%m/%Y')
                        if isinstance(capitulo.get('created_at'), datetime) else 'Sin fecha',
                        size=10, color=AppColors.TEXT_MUTED,
                    ),
                ], spacing=2, expand=True),
                ft.Icon(
                    name=ft.Icons.CHECK_CIRCLE_ROUNDED if is_downloaded else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                    color=AppColors.ACCENT_GREEN if is_downloaded else AppColors.TEXT_MUTED,
                    size=20,
                ),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(10, 8, 10, 8),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.05, AppColors.ACCENT_GREEN) if is_downloaded else ft.Colors.TRANSPARENT,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.ACCENT_GREEN if is_downloaded else AppColors.BORDER)),
        )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self, novela_id):
        self._show_loading()
        try:
            self.contar_capitulos = 0
            novela, capitulos = self.repo.load_novela_details(novela_id)
            if not novela:
                return self._error_view(novela_id)

            self.ids_contenido_capitulo = self.repo.load_ids_contenido_capitulos_novela(novela_id)
            self.contar_capitulos = len(self.ids_contenido_capitulo)
            self.txt_number.value = str(self.contar_capitulos)

            self.todos_capitulos = capitulos
            self.mapa_capitulo_indice = {str(cap['_id']): idx for idx, cap in enumerate(capitulos, 1)}
            self.pagina_capitulos_actual = self.page.session.get(f"pagina_caps_{novela_id}") or 1
            self.total_paginas_capitulos = max(1, (len(capitulos) + CAPITULOS_POR_PAGINA - 1) // CAPITULOS_POR_PAGINA)
            if self.pagina_capitulos_actual > self.total_paginas_capitulos:
                self.pagina_capitulos_actual = 1

            # --- Controles de paginación de capítulos ---
            txt_pagina_actual = ft.Text(
                f"{self.pagina_capitulos_actual}/{self.total_paginas_capitulos}",
                size=11, color=AppColors.TEXT_SECONDARY,
            )
            input_ir_pagina = ft.TextField(
                value=str(self.pagina_capitulos_actual),
                width=50, height=32, text_size=11,
                text_align=ft.TextAlign.CENTER,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY_LIGHT,
                input_filter=ft.NumbersOnlyInputFilter(),
                on_change=lambda e: self._ir_a_pagina_debounced(
                    novela_id, txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig,
                ),
            )
            btn_ant = ft.IconButton(
                ft.Icons.CHEVRON_LEFT_ROUNDED,
                on_click=lambda _: self._ir_pagina(
                    self.pagina_capitulos_actual - 1, novela_id,
                    txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig,
                ),
                icon_color=AppColors.PRIMARY_LIGHT, icon_size=20,
                tooltip="Página anterior",
                disabled=(self.pagina_capitulos_actual <= 1),
            )
            btn_sig = ft.IconButton(
                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                on_click=lambda _: self._ir_pagina(
                    self.pagina_capitulos_actual + 1, novela_id,
                    txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig,
                ),
                icon_color=AppColors.PRIMARY_LIGHT, icon_size=20,
                tooltip="Página siguiente",
                disabled=(self.pagina_capitulos_actual >= self.total_paginas_capitulos),
            )
            self.spinner_paginacion = ft.ProgressRing(
                width=16, height=16, stroke_width=2,
                color=AppColors.PRIMARY_LIGHT, visible=False,
            )

            # Inicializar lista
            caps_inicial, offset_inicial = self._obtener_capitulos_pagina(self.pagina_capitulos_actual)
            self.lista_capitulos = [self._create_chapter_item(cap, offset_inicial + idx) for idx, cap in enumerate(caps_inicial)]
            self.lv_capitulos = ft.ListView(controls=self.lista_capitulos, spacing=4, height=350)

            # --- Botones de exportación y scraping ---
            all_downloaded = len(self.todos_capitulos) == self.contar_capitulos
            self.btn_epub.on_click = lambda _: self.export_svc.crear_epub(novela, self.todos_capitulos)
            self.btn_epub.disabled = not all_downloaded
            self.btn_pdf.on_click = lambda _: self.export_svc.crear_pdf(novela, self.todos_capitulos)
            self.btn_pdf.disabled = not all_downloaded

            # Capítulos faltantes (set difference optimizado)
            todos_ids = [str(c['_id']) for c in self.todos_capitulos]
            cap_faltantes = self.repo.get_capitulos_faltantes(todos_ids, self.ids_contenido_capitulo)
            self.btn_procesar.disabled = len(cap_faltantes) == 0
            self.btn_procesar.on_click = lambda _: self.scraping_svc.obtener_capitulos(
                cap_faltantes, novela_id, on_chapter_done=self._on_chapter_done,
            )

            # --- Status badge ---
            status = novela.get('status', '').lower()
            status_color = (
                AppColors.ACCENT_GREEN if 'complet' in status
                else AppColors.ACCENT_ORANGE if 'ongoing' in status
                else AppColors.TEXT_MUTED
            )
            status_icon = ft.Icons.CHECK_CIRCLE_ROUNDED if 'complet' in status else ft.Icons.PENDING_ROUNDED
            progreso_pct = (self.contar_capitulos / len(capitulos) * 100) if len(capitulos) > 0 else 0

            return ft.View(
                f"/novela/{novela_id}",
                [
                    ft.AppBar(
                        title=ft.Row([
                            ft.Icon(ft.Icons.BOOK_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=22),
                            ft.Text(f"  {novela['nombre'][:40]}{'...' if len(novela['nombre']) > 40 else ''}",
                                    weight=ft.FontWeight.W_600, size=14),
                        ]),
                        bgcolor=AppColors.BG_CARD,
                        leading=ft.IconButton(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            on_click=lambda _: self.navigate_to_detail(novela['sitio_id']),
                            icon_color=AppColors.TEXT_PRIMARY,
                            tooltip="Volver a la lista",
                        ),
                        elevation=0,
                    ),
                    # Info principal
                    ft.ResponsiveRow([
                        ft.Column(col={"xs": 12, "sm": 12, "md": 3}, controls=[
                            ft.Container(
                                content=ft.Image(
                                    src=novela['imagen_url'], fit=ft.ImageFit.CONTAIN,
                                    border_radius=ft.border_radius.all(16), height=250,
                                ),
                                border_radius=16,
                                shadow=ft.BoxShadow(spread_radius=0, blur_radius=20,
                                                     color=ft.Colors.with_opacity(0.4, AppColors.PRIMARY),
                                                     offset=ft.Offset(0, 8)),
                                margin=ft.Margin(0, 0, 0, 10),
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(status_icon, color=AppColors.TEXT_PRIMARY, size=16),
                                    ft.Text(novela.get('status', 'N/A'), size=12,
                                            weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                bgcolor=status_color,
                                padding=ft.Padding(12, 6, 12, 6),
                                border_radius=20,
                                alignment=ft.alignment.center,
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column(col={"xs": 12, "sm": 12, "md": 9}, controls=[
                            ft.Text(novela['nombre'], size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                            ft.Container(height=10),
                            ft.Row([
                                self._info_card("Autor", novela.get('autor', 'Desconocido')[:20],
                                                ft.Icons.PERSON_ROUNDED, AppColors.SECONDARY),
                                self._info_card("Género", novela.get('genero', 'N/A')[:20],
                                                ft.Icons.CATEGORY_ROUNDED, AppColors.ACCENT_PINK),
                                self._info_card("Capítulos", str(len(capitulos)),
                                                ft.Icons.MENU_BOOK_ROUNDED, AppColors.ACCENT_ORANGE),
                            ], spacing=8),
                            ft.Container(height=10),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=16),
                                        ft.Text("Sinopsis", size=13, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                    ], spacing=6),
                                    ft.Text(
                                        novela.get('sinopsis', 'Sin sinopsis disponible')[:300]
                                        + ('...' if len(novela.get('sinopsis', '')) > 300 else ''),
                                        size=11, color=AppColors.TEXT_SECONDARY,
                                    ),
                                ], spacing=6),
                                padding=12, border_radius=10,
                                bgcolor=AppColors.BG_CARD,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
                            ),
                        ]),
                    ], spacing=15, run_spacing=10),
                    ft.Divider(height=1, color=AppColors.BORDER),
                    # Progreso + controles + capítulos
                    ft.ResponsiveRow([
                        ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("📊 Progreso", size=13, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                    ft.Container(height=8),
                                    ft.Row([self.txt_number,
                                            ft.Text(f" / {len(capitulos)}", size=14, color=AppColors.TEXT_MUTED)],
                                           alignment=ft.MainAxisAlignment.CENTER),
                                    ft.ProgressBar(
                                        value=progreso_pct / 100,
                                        color=AppColors.ACCENT_GREEN if progreso_pct == 100 else AppColors.PRIMARY,
                                        bgcolor=AppColors.BG_ELEVATED,
                                    ),
                                    ft.Text(f"{progreso_pct:.1f}%", size=10,
                                            color=AppColors.ACCENT_GREEN if progreso_pct == 100 else AppColors.TEXT_MUTED),
                                    ft.Container(height=10),
                                    self.btn_epub, self.btn_pdf, self.btn_procesar,
                                    ft.Container(height=5),
                                    ft.Container(content=self.progress_ring, alignment=ft.alignment.center),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                                padding=15, border_radius=12,
                                bgcolor=AppColors.BG_CARD,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
                            ),
                        ], col={"xs": 12, "sm": 12, "md": 3}),
                        ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.LIST_ALT_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=18),
                                        ft.Text("Capítulos", size=13, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                        ft.Container(expand=True),
                                        ft.Container(
                                            content=ft.Text(f"{self.contar_capitulos}/{len(self.todos_capitulos)}",
                                                            size=11, weight=ft.FontWeight.W_600, color=AppColors.ACCENT_GREEN),
                                            padding=ft.Padding(8, 3, 8, 3),
                                            border_radius=15,
                                            bgcolor=ft.Colors.with_opacity(0.15, AppColors.ACCENT_GREEN),
                                        ),
                                    ], spacing=8),
                                    ft.Container(height=8),
                                    ft.Row([
                                        btn_ant, txt_pagina_actual, btn_sig,
                                        ft.Container(width=10),
                                        ft.Text("Ir a:", size=10, color=AppColors.TEXT_MUTED),
                                        input_ir_pagina,
                                        self.spinner_paginacion,
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                                    ft.Container(height=6),
                                    self.lv_capitulos,
                                ]),
                                padding=12, border_radius=12,
                                bgcolor=AppColors.BG_CARD,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
                            ),
                        ], col={"xs": 12, "sm": 12, "md": 9}),
                    ], spacing=10, run_spacing=10),
                ],
                bgcolor=AppColors.BG_DARK,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                padding=ft.Padding(15, 10, 15, 15),
            )
        finally:
            self._hide_loading()  # FIX: siempre se invoca

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _info_card(label, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=18),
                ft.Text(label, size=9, color=AppColors.TEXT_MUTED),
                ft.Text(value, size=11, weight=ft.FontWeight.W_500, color=AppColors.TEXT_PRIMARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=10, border_radius=10,
            bgcolor=AppColors.BG_ELEVATED,
            expand=True,
        )

    def _ir_pagina(self, nueva_pagina, novela_id,
                   txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig):
        if 1 <= nueva_pagina <= self.total_paginas_capitulos:
            self.spinner_paginacion.visible = True
            self.page.update()
            self._actualizar_lista_capitulos(
                nueva_pagina, novela_id,
                txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig,
            )
            self.spinner_paginacion.visible = False
            self.page.update()

    def _ir_a_pagina_debounced(self, novela_id,
                                txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig):
        if self.debounce_timer:
            self.debounce_timer.cancel()

        def ejecutar():
            try:
                pagina = int(input_ir_pagina.value or "1")
                pagina = max(1, min(pagina, self.total_paginas_capitulos))
                self.spinner_paginacion.visible = True
                self.page.update()
                self._actualizar_lista_capitulos(
                    pagina, novela_id,
                    txt_pagina_actual, input_ir_pagina, btn_ant, btn_sig,
                )
                self.spinner_paginacion.visible = False
                self.page.update()
            except ValueError:
                pass

        self.debounce_timer = threading.Timer(0.2, ejecutar)
        self.debounce_timer.start()

    def _error_view(self, novela_id):
        return ft.View(
            f"/novela/{novela_id}",
            [
                ft.AppBar(
                    title=ft.Text("Error", size=16),
                    bgcolor=ft.Colors.ERROR,
                    leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/")),
                ),
                ft.Text("Novela no encontrada", size=20),
            ],
        )
