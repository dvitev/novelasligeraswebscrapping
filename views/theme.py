"""Tema visual de la aplicación – paleta de colores y componentes reutilizables."""

import flet as ft


# ============================================================
# Paleta de colores moderna
# ============================================================
class AppColors:
    """Colores centralizados para toda la aplicación."""

    # Primarios – gradiente púrpura/azul
    PRIMARY = "#7C3AED"
    PRIMARY_LIGHT = "#A78BFA"
    PRIMARY_DARK = "#5B21B6"

    # Secundarios – Cyan/Teal
    SECONDARY = "#06B6D4"
    SECONDARY_LIGHT = "#22D3EE"

    # Acentos
    ACCENT_GREEN = "#10B981"
    ACCENT_ORANGE = "#F59E0B"
    ACCENT_RED = "#EF4444"
    ACCENT_PINK = "#EC4899"

    # Fondos oscuros con tonos azulados
    BG_DARK = "#0F172A"
    BG_CARD = "#1E293B"
    BG_ELEVATED = "#334155"
    BG_HOVER = "#475569"

    # Bordes y divisores
    BORDER = "#475569"
    BORDER_LIGHT = "#64748B"

    # Texto
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"

    # Estados
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"


# ============================================================
# Tema oscuro personalizado
# ============================================================
def create_dark_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=ft.Colors.DEEP_PURPLE,
        color_scheme=ft.ColorScheme(
            primary=AppColors.PRIMARY,
            secondary=AppColors.SECONDARY,
            surface=AppColors.BG_CARD,
            background=AppColors.BG_DARK,
            on_surface=AppColors.TEXT_PRIMARY,
            on_background=AppColors.TEXT_PRIMARY,
            error=AppColors.ERROR,
        ),
        text_theme=ft.TextTheme(
            headline_medium=ft.TextStyle(size=28, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
            headline_small=ft.TextStyle(size=22, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
            title_medium=ft.TextStyle(size=16, weight=ft.FontWeight.W_500, color=AppColors.TEXT_PRIMARY),
            body_medium=ft.TextStyle(size=14, color=AppColors.TEXT_SECONDARY),
            body_small=ft.TextStyle(size=12, color=AppColors.TEXT_MUTED),
        ),
        visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        appbar_theme=ft.AppBarTheme(color=AppColors.TEXT_PRIMARY),
        elevated_button_theme=ft.ElevatedButtonTheme(
            text_style=ft.TextStyle(color=AppColors.TEXT_PRIMARY, weight=ft.FontWeight.W_600),
        ),
        card_theme=ft.CardTheme(color=AppColors.BG_CARD, surface_tint_color=AppColors.BG_ELEVATED),
        list_tile_theme=ft.ListTileTheme(icon_color=AppColors.PRIMARY_LIGHT, text_color=AppColors.TEXT_SECONDARY),
    )


# ============================================================
# Componentes UI reutilizables
# ============================================================
def create_gradient_container(content, colors=None, border_radius=12, padding=20):
    """Contenedor con gradiente visual."""
    if colors is None:
        colors = [AppColors.PRIMARY_DARK, AppColors.BG_CARD]
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=colors,
        ),
        shadow=ft.BoxShadow(
            spread_radius=1, blur_radius=15,
            color=ft.Colors.with_opacity(0.3, AppColors.PRIMARY),
            offset=ft.Offset(0, 4),
        ),
    )


def create_glass_container(content, border_radius=12, padding=15):
    """Contenedor con efecto glassmorphism."""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=ft.Colors.with_opacity(0.1, AppColors.TEXT_PRIMARY),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, AppColors.TEXT_PRIMARY)),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=20,
            color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
        ),
    )


def create_action_button(text, icon, color, on_click=None, tooltip="", disabled=False):
    """Botón de acción estilizado."""
    return ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=AppColors.TEXT_PRIMARY, size=18),
                    ft.Text(text, weight=ft.FontWeight.W_600, size=13),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=color,
            color=AppColors.TEXT_PRIMARY,
            on_click=on_click,
            disabled=disabled,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(20, 12, 20, 12),
                elevation=4,
                animation_duration=200,
            ),
        ),
        tooltip=tooltip,
    )


def create_stat_card(title, value, icon, color):
    """Tarjeta de estadística."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, color=color, size=28),
                    padding=10,
                    border_radius=50,
                    bgcolor=ft.Colors.with_opacity(0.15, color),
                ),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Text(title, size=12, color=AppColors.TEXT_MUTED),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        ),
        padding=15,
        border_radius=12,
        bgcolor=AppColors.BG_CARD,
        border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
    )
