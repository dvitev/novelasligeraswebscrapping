import base64
import os
import flet as ft
from pymongo import MongoClient
from bson.objectid import ObjectId
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from google_trans_new import google_translator
from langdetect import detect, DetectorFactory
import translators as ts
import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs
from datetime import datetime
import csv
import time
import pandas as pd
from ebooklib import epub
from uuid import uuid4
import requests
import os
from tempfile import gettempdir
from urllib.parse import urlparse
from fpdf import FPDF
import logging
import threading

# --- Logging Configuration ---
# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.1.11:27017")
DB_NAME = "recopilarnovelas"
COLLECTION_SITIOS = "app_sitio"
COLLECTION_NOVELAS = "app_novela"
COLLECTION_CAPITULOS = "app_capitulo"
COLLECTION_CONTENIDO_CAPITULOS = 'app_contenidocapitulo'

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection_sitios = db[COLLECTION_SITIOS]
collection_novelas = db[COLLECTION_NOVELAS]
collection_capitulos = db[COLLECTION_CAPITULOS]
collection_contenido_capitulos = db[COLLECTION_CONTENIDO_CAPITULOS]

# IDs de Sitios (Constantes para mejorar mantenibilidad)
FANMTL_SITIO_ID = '67de23f6e131d527f2995103'
TUNOVELA_LIGERA_SITIO_ID = '680ecb15e1ce8081ecb8b4d1'

# --- Límites de caracteres para servicios de traducción (ajusta según sea necesario) ---
CHARACTER_LIMITS = {
    'google': 5000, # Ejemplo, verifica el límite real
    'google_new': 5000, # Ejemplo, verifica el límite real
    'bing': 5000, # Ejemplo, verifica el límite real
    # Agrega límites para otros servicios si los usas (ej. deepl, libre)
}

# --- Additional Constants ---
DEFAULT_SLEEP_TIME = 3
PARAGRAPH_DELIMITER = "---PARAGRAPH_DELIMITER---"
TEMP_IMAGE_FILENAME = "imagen_descargada.jpg"
PINGO_FONT_PATH = os.path.join(os.getcwd(), 'recopilarnovelasdjango', 'static', 'fonts', 'Poppins-Regular.ttf')

# --- Constantes de Paginación ---
NOVELAS_POR_PAGINA = 20 # Ajusta este número según el rendimiento deseado
CAPITULOS_POR_PAGINA = 50 # Capítulos por página en vista de detalle de novela

# --- Constantes de Colores Personalizados ---
class AppColors:
    """Paleta de colores moderna para la aplicación"""
    # Colores primarios - Gradiente púrpura/azul
    PRIMARY = "#7C3AED"  # Violeta vibrante
    PRIMARY_LIGHT = "#A78BFA"
    PRIMARY_DARK = "#5B21B6"
    
    # Colores secundarios - Cyan/Teal
    SECONDARY = "#06B6D4"
    SECONDARY_LIGHT = "#22D3EE"
    
    # Colores de acento
    ACCENT_GREEN = "#10B981"
    ACCENT_ORANGE = "#F59E0B"
    ACCENT_RED = "#EF4444"
    ACCENT_PINK = "#EC4899"
    
    # Fondos oscuros con tonos azulados
    BG_DARK = "#0F172A"  # Fondo principal
    BG_CARD = "#1E293B"  # Fondo de tarjetas
    BG_ELEVATED = "#334155"  # Elementos elevados
    BG_HOVER = "#475569"  # Estado hover
    
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

# --- Tema Oscuro Personalizado ---
def create_dark_theme():
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
        appbar_theme=ft.AppBarTheme(
            color=AppColors.TEXT_PRIMARY,
        ),
        elevated_button_theme=ft.ElevatedButtonTheme(
            text_style=ft.TextStyle(color=AppColors.TEXT_PRIMARY, weight=ft.FontWeight.W_600)
        ),
        card_theme=ft.CardTheme(
            color=AppColors.BG_CARD,
            surface_tint_color=AppColors.BG_ELEVATED
        ),
        list_tile_theme=ft.ListTileTheme(
            icon_color=AppColors.PRIMARY_LIGHT,
            text_color=AppColors.TEXT_SECONDARY
        )
    )

# --- Componentes UI Reutilizables ---
def create_gradient_container(content, colors=None, border_radius=12, padding=20):
    """Crea un contenedor con efecto de gradiente visual"""
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
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, AppColors.PRIMARY),
            offset=ft.Offset(0, 4),
        ),
    )

def create_glass_container(content, border_radius=12, padding=15):
    """Crea un contenedor con efecto glassmorphism"""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=ft.Colors.with_opacity(0.1, AppColors.TEXT_PRIMARY),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, AppColors.TEXT_PRIMARY)),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
        ),
    )

def create_action_button(text, icon, color, on_click=None, tooltip="", disabled=False):
    """Crea un botón de acción estilizado"""
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
    """Crea una tarjeta de estadística estilizada"""
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


class AppState:
    loading = False

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        # Nota: {{nb}} será reemplazado por alias_nb_pages() en crearpdf
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")
    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f"{label}", new_x="LMARGIN",
                new_y="NEXT", align="L", fill=True)
        self.ln(4)
    def chapter_body(self, texto):
        self.set_font('Poppins-Regular', size=12)
        # Printing justified text:
        self.write_html(texto)
        # Performing a line break:
        self.ln()
    def add_section(self, title):
        self.start_section(title)
    def print_chapter(self, title, texto):
        self.add_page()
        # self.start_section(title)
        self.chapter_title(title)
        self.chapter_body(texto)

def main(page: ft.Page):
    page.title = "📚 Novelas Manager"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = create_dark_theme()
    page.bgcolor = AppColors.BG_DARK
    page.padding = 0
    
    # Configuración de ventana para mejor apariencia
    page.window.min_width = 800
    page.window.min_height = 600

    filepicker = ft.FilePicker()
    save_file_path = ft.Text()
    page.overlay.append(filepicker)

    contar_capitulos = 0
    lista_capitulos = []
    ids_contenido_capitulo = set()  # Cambiado a set para búsquedas O(1)
    
    # --- Variables para paginación de capítulos ---
    mapa_capitulo_indice = {}  # {cap_id: índice_1based}
    pagina_capitulos_actual = 1
    todos_capitulos = []  # Lista completa para EPUB/PDF
    debounce_timer = None
    lv_capitulos = None  # Referencia al ListView
    spinner_paginacion = None  # Mini-spinner para cambios de página
    total_paginas_capitulos = 1
    
    # --- Variables para control de exportación ---
    cancelar_exportacion = False
    progreso_exportacion = None  # Referencia a ProgressBar de exportación
    texto_progreso_exportacion = None  # Referencia a Text de progreso

    txt_number = ft.Text(
        value="0", 
        text_align=ft.TextAlign.CENTER, 
        size=32, 
        weight=ft.FontWeight.BOLD,
        color=AppColors.PRIMARY_LIGHT
    )

    # --- Botones con estilo moderno y gradientes ---
    btn_epub = ft.ElevatedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.BOOK_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
                ft.Text("EPUB", weight=ft.FontWeight.W_700, size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=AppColors.ACCENT_GREEN,
        color=AppColors.TEXT_PRIMARY,
        expand=True,
        tooltip="📖 Generar archivo EPUB",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14),
            elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.ACCENT_GREEN),
            animation_duration=300,
        )
    )
    
    btn_pdf = ft.ElevatedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.PICTURE_AS_PDF_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
                ft.Text("PDF", weight=ft.FontWeight.W_700, size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=AppColors.ACCENT_RED,
        color=AppColors.TEXT_PRIMARY,
        expand=True,
        tooltip="📄 Generar archivo PDF",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14),
            elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.ACCENT_RED),
            animation_duration=300,
        )
    )
    
    btn_procesar = ft.ElevatedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD_FOR_OFFLINE_OUTLINED, color=AppColors.TEXT_PRIMARY, size=20),
                ft.Text("PROCESAR", weight=ft.FontWeight.W_700, size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=AppColors.PRIMARY,
        color=AppColors.TEXT_PRIMARY,
        expand=True,
        tooltip="⚡ Obtener capítulos faltantes",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 14, 16, 14),
            elevation=6,
            shadow_color=ft.Colors.with_opacity(0.4, AppColors.PRIMARY),
            animation_duration=300,
        )
    )

    def traducir(texto: str) -> str:
        """Traduce texto usando múltiples servicios de traducción"""
        translators = [
            ('google', lambda t: ts.translate_text(t, translator='google', to_language='es')),
            ('google_new', lambda t: google_translator().translate(t, lang_tgt='es')),
            ('bing', lambda t: ts.translate_text(t, translator='bing', to_language='es')),
        ]
        for name, func in translators:
            try:
                return func(texto)
            except Exception as e:
                logger.warning(f"Fallo en {name}: {e}")
                continue
        return texto

    def traducir_texto_largo(texto: str, delimitador: str = '--- párrafo_delimiter ---') -> str:
        """
        Traduce texto largo dividiéndolo si excede el límite de caracteres del servicio.
        Esta función envuelve la función `traducir` original para manejar límites.
        """
        # Determinar el límite (usamos el más restrictivo o uno por defecto)
        # En una implementación más robusta, podrías probar con el servicio específico
        limit = min(CHARACTER_LIMITS.values(), default=4500)

        if len(texto) <= limit:
            # Si el texto está dentro del límite, traducir directamente
            return traducir(texto)
        else:
            # Dividir el texto en partes más pequeñas
            # Esta es una división simple por caracteres. Para HTML, podría ser más compleja.
            # Una forma más segura es dividir por el delimitador.
            partes = texto.split(delimitador)
            partes_traducidas = []
            parte_actual = ""

            for parte in partes:
                # Añadir el delimitador de vuelta para la construcción (excepto la primera)
                parte_con_delimitador = (delimitador if parte_actual else "") + parte
                # Verificar si añadir esta parte excedería el límite
                if len(parte_actual + parte_con_delimitador) > limit and parte_actual:
                    # Si sí, traducir la parte_actual y comenzar una nueva
                    partes_traducidas.append(traducir(parte_actual))
                    parte_actual = parte # Comenzar con la parte actual
                else:
                    # Si no, añadir la parte a la parte_actual
                    parte_actual += parte_con_delimitador

            # Traducir la última parte acumulada
            if parte_actual:
                partes_traducidas.append(traducir(parte_actual))

            # Unir todas las partes traducidas
            return "".join(partes_traducidas)

    def close_banner(e):
        page.close(banner)

    # --- Banner con estilo moderno glassmorphism ---
    banner = ft.Banner(
        content=ft.Row([]),
        actions=[
            ft.TextButton(
                text="✕ Cerrar", 
                on_click=close_banner,
                style=ft.ButtonStyle(
                    color=AppColors.TEXT_PRIMARY,
                )
            ),
        ],
        bgcolor=AppColors.BG_ELEVATED,
        surface_tint_color=AppColors.PRIMARY,
    )

    # --- Progress Ring con estilo mejorado ---
    progress_ring = ft.ProgressRing(
        visible=False, 
        stroke_width=4, 
        color=AppColors.PRIMARY_LIGHT,
        stroke_cap=ft.StrokeCap.ROUND,
    )

    def open_banner(fondo, icono, contenido):
        banner.bgcolor=fondo
        banner.leading=icono
        banner.content.controls=contenido
        page.open(banner)

    def enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo):
        novel_data={
            'novela_id': novela_id,
            'capitulo_id': capitulo_id,
            'texto': texto_capitulo,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        return str(collection_contenido_capitulos.insert_one(novel_data).inserted_id)

    def _extraer_y_guardar_contenido(soup, selector_css, novela_id, capitulo_id, traducir_flag=False, delimitador=PARAGRAPH_DELIMITER):
        """Función auxiliar para extraer y guardar contenido de capítulos."""
        div_contenido = soup.find('div', class_=selector_css)
        if div_contenido:
            p_tags = div_contenido.find_all('p')
            # Filtramos los párrafos que tienen texto
            p_tags_con_texto = [p for p in p_tags if p.getText().strip()]
            
            if p_tags_con_texto:
                textos_originales = [p.getText().strip() for p in p_tags_con_texto]
            else:
                # Obtener HTML interno y dividir por <br>
                html_str = str(div_contenido)
                br_separated = html_str.split('<br/>')
                textos_originales = [
                    bs(part, 'html.parser').get_text().strip()
                    for part in br_separated
                    if bs(part, 'html.parser').get_text().strip()
                ]
            if textos_originales:
                texto_capitulo = ""
                if traducir_flag:
                    texto_a_traducir = delimitador.join(textos_originales)
                    texto_traducido_completo = traducir_texto_largo(texto_a_traducir, delimitador)
                    # Reemplazar el delimitador por etiquetas <p> para construir el HTML
                    texto_capitulo = f"<p>{texto_traducido_completo.replace(delimitador, '</p><p>')}</p>"
                else:
                    texto_capitulo = ''.join([f"<p>{texto}</p>" for texto in textos_originales])
            else:
                texto_capitulo = "<p>(Sin contenido)</p>"

            _id = enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo)
            logger.info(f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}")
            open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
                [
                    ft.Text(
                        value=f"✅ Contenido creado con id:{_id}",
                        color=AppColors.TEXT_PRIMARY,
                        size=14,
                        weight=ft.FontWeight.W_500,
                    ),
                ]
            )
            return _id
        else:
            logger.error(f"Error: No se encontró el contenido del capítulo con selector {selector_css}.")
            open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                [
                    ft.Text(
                        value=f"❌ No se encontró contenido con selector {selector_css}",
                        color=AppColors.TEXT_PRIMARY,
                        size=14,
                    ),
                ]
            )
            return None

    def manejar_driver_capitulos(driver, novela_id, capitulo_id):
        # --- Cambio aquí: Obtener novela_doc una sola vez ---
        novela_doc = collection_novelas.find_one({'_id': ObjectId(novela_id)})
        if not novela_doc:
            logger.error("Error: Novela no encontrada.")
            open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                [
                    ft.Text(
                        value="❌ Novela no encontrada",
                        color=AppColors.TEXT_PRIMARY,
                        size=14,
                    ),
                ]
            )
            return

        sitio_id = novela_doc.get('sitio_id')

        # FANMTL.com
        if FANMTL_SITIO_ID == sitio_id: # Usar constante
            time.sleep(DEFAULT_SLEEP_TIME)
            soup = bs(driver.page_source, 'html.parser')
            _id = _extraer_y_guardar_contenido(soup, 'chapter-content', novela_id, capitulo_id, traducir_flag=True, delimitador=PARAGRAPH_DELIMITER)

        # tunovelaligera.com
        elif TUNOVELA_LIGERA_SITIO_ID == sitio_id: # Usar elif y constante
            time.sleep(DEFAULT_SLEEP_TIME)
            soup = bs(driver.page_source, 'html.parser')
            _id = _extraer_y_guardar_contenido(soup, 'entry-content_wrap', novela_id, capitulo_id, traducir_flag=False, delimitador=PARAGRAPH_DELIMITER)

        else:
            logger.warning("Validar sitio para manejar driver no es FANMTL.com o tunovelaligera.com")
            open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=AppColors.WARNING, size=40),
                [
                    ft.Text(
                        value="⚠️ Sitio no soportado: FANMTL.com o tunovelaligera.com",
                        color=AppColors.TEXT_PRIMARY,
                        size=14,
                    ),
                ]
            )

    def descargar_imagen(url):
        # Obtener carpeta temporal
        temp_dir = gettempdir()
        # Extraer nombre del archivo de la URL
        parsed_url = urlparse(url)
        nombre_archivo = os.path.basename(parsed_url.path)
        # Si la URL no contiene nombre, usar uno por defecto
        if not nombre_archivo:
            nombre_archivo = TEMP_IMAGE_FILENAME
        # Ruta completa de destino
        ruta_destino = os.path.join(temp_dir, nombre_archivo)

        try:
            # Descargar la imagen
            respuesta = requests.get(url, stream=True, timeout=30) # Añadir timeout
            respuesta.raise_for_status()  # Verificar errores HTTP

            # Guardar la imagen
            with open(ruta_destino, 'wb') as archivo:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    if chunk:
                        archivo.write(chunk)

            logger.info(f"Imagen descargada en: {ruta_destino}")
            return ruta_destino
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red al descargar: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al descargar: {str(e)}")
            return None

    def sanitizar_nombre(nombre):
        """Elimina caracteres no válidos para nombres de archivo"""
        return "".join(c for c in nombre if c.isalnum() or c in (' ', '_', '-')).rstrip()

    # ============================================================
    # FUNCIONES AUXILIARES PARA EXPORTACIÓN (EPUB/PDF)
    # ============================================================
    
    def obtener_contenido_capitulos(novela_id):
        """Obtiene el contenido de todos los capítulos de una novela desde BD."""
        return {
            str(x['capitulo_id']): x['texto']
            for x in collection_contenido_capitulos.find(
                {'novela_id': str(novela_id)}
            ).sort('created_at', 1)
        }
    
    def descargar_y_preparar_portada(url):
        """
        Descarga imagen y retorna (ruta_temporal, bytes).
        Raises: Exception si falla la descarga.
        """
        portada = descargar_imagen(url)
        if not portada or not os.path.exists(portada):
            raise Exception("Error al obtener la portada")
        
        with open(portada, 'rb') as f:
            portada_bytes = f.read()
        
        return portada, portada_bytes
    
    def preparar_ui_exportacion(formato):
        """Prepara UI para exportación: deshabilita botones, muestra progreso."""
        global cancelar_exportacion, progreso_exportacion, texto_progreso_exportacion
        cancelar_exportacion = False
        
        progress_ring.visible = True
        btn_epub.disabled = True
        btn_pdf.disabled = True
        btn_procesar.disabled = True
        
        # Crear componentes de progreso si no existen
        progreso_exportacion = ft.ProgressBar(
            value=0,
            color=AppColors.ACCENT_GREEN if formato == 'epub' else AppColors.ACCENT_RED,
            bgcolor=AppColors.BG_ELEVATED,
        )
        texto_progreso_exportacion = ft.Text(
            value=f"📦 Preparando {formato.upper()}...",
            size=11,
            color=AppColors.TEXT_MUTED,
            text_align=ft.TextAlign.CENTER,
        )
        page.update()
    
    def actualizar_progreso_exportacion(idx, total, nombre, formato):
        """Actualiza progreso de exportación (cada 5 capítulos o al final)."""
        global progreso_exportacion, texto_progreso_exportacion
        
        porcentaje = idx / total if total > 0 else 0
        emoji = "📖" if formato == 'epub' else "📄"
        
        if progreso_exportacion:
            progreso_exportacion.value = porcentaje
        if texto_progreso_exportacion:
            texto_progreso_exportacion.value = f"{emoji} [{idx}/{total}] {nombre[:35]}..."
        
        # Actualizar UI solo cada 5 capítulos o al final para mejor rendimiento
        if idx % 5 == 0 or idx == total:
            page.update()
    
    def finalizar_ui_exportacion(portada_path=None):
        """Restaura UI después de exportación y limpia recursos."""
        global cancelar_exportacion
        cancelar_exportacion = False
        
        progress_ring.visible = False
        btn_epub.disabled = False
        btn_pdf.disabled = False
        btn_procesar.disabled = False
        
        # Limpiar archivo temporal de portada
        if portada_path and os.path.exists(portada_path):
            try:
                os.remove(portada_path)
                logger.info("Archivo temporal de portada eliminado.")
            except OSError as oe:
                logger.warning(f"No se pudo eliminar el archivo temporal: {oe}")
        
        page.update()
    
    def limpiar_portada_temporal(portada_path):
        """Limpia archivo temporal de portada."""
        if portada_path and os.path.exists(portada_path):
            try:
                os.remove(portada_path)
                logger.info("Archivo temporal de portada eliminado.")
            except OSError as oe:
                logger.warning(f"No se pudo eliminar el archivo temporal: {oe}")

    # ============================================================
    # FUNCIONES DE PAGINACIÓN DE CAPÍTULOS
    # ============================================================
    
    def calcular_visibilidad_capitulo(cap_id):
        """
        Calcula si un capítulo está visible en la página actual.
        Retorna: (es_visible, indice_relativo) donde indice_relativo es 0-based para lista
        """
        global mapa_capitulo_indice, pagina_capitulos_actual
        
        indice_global = mapa_capitulo_indice.get(str(cap_id), 0)  # 1-based
        if indice_global == 0:
            return (False, -1)
        
        inicio = (pagina_capitulos_actual - 1) * CAPITULOS_POR_PAGINA + 1  # 1-based
        fin = inicio + CAPITULOS_POR_PAGINA - 1
        
        es_visible = inicio <= indice_global <= fin
        indice_relativo = (indice_global - inicio) if es_visible else -1  # 0-based para lista
        
        return (es_visible, indice_relativo)

    def crearepub(novela, capitulos):
        """Genera archivo EPUB en hilo separado con progreso visual y opción de cancelación."""
        nonlocal cancelar_exportacion
        portada = None  # Para limpieza en finally
        
        def _epub_worker():
            nonlocal portada, cancelar_exportacion
            try:
                # Preparar UI
                progress_ring.visible = True
                btn_epub.disabled = True
                btn_pdf.disabled = True
                btn_procesar.disabled = True
                page.update()
                
                # Obtener contenido de BD
                contenido_capitulos_novela = obtener_contenido_capitulos(novela['_id'])
                
                # Verificar cancelación
                if cancelar_exportacion:
                    raise Exception("Exportación cancelada por el usuario")
                
                # Descargar portada (una sola lectura)
                portada, portada_bytes = descargar_y_preparar_portada(novela['imagen_url'])
                base64_cover = base64.b64encode(portada_bytes).decode('utf-8')
                
                # Crear libro EPUB
                book = epub.EpubBook()
                book.set_identifier(str(novela['_id']))
                book.set_title(novela['nombre'])
                book.set_language('es')
                book.add_author(novela['autor'])
                book.set_cover('cover.jpg', portada_bytes)  # Usar bytes ya leídos
                
                # Traducciones
                nombre_traducido = traducir(novela['nombre']) or novela['nombre']
                sinopsis_traducida = traducir(novela['sinopsis']) or novela['sinopsis']
                
                # Introducción con formato base64 corregido
                intro_html = f"""
                <h1>{nombre_traducido}</h1>
                <img src="data:image/jpeg;base64,{base64_cover}"
                    style="width: 300px; height: auto; margin: 0 auto; display: block;">
                <h2>Detalles de la Novela</h2>
                <table style="width:100%; border-collapse: collapse;">
                <tr><td style="font-weight:bold;">Novela ID</td><td>{novela.get('_id', 'N/A')}</td></tr>
                <tr><td style="font-weight:bold;">Nombre</td><td>{nombre_traducido}</td></tr>
                <tr><td style="font-weight:bold; vertical-align:top;">Sinopsis</td><td>{sinopsis_traducida}</td></tr>
                <tr><td style="font-weight:bold;">Autor</td><td>{novela.get('autor', 'N/A')}</td></tr>
                <tr><td style="font-weight:bold;">Género</td><td>{novela.get('genero', 'N/A')}</td></tr>
                <tr><td style="font-weight:bold;">Estado</td><td>{novela.get('status', 'N/A')}</td></tr>
                <tr><td style="font-weight:bold;">URL</td><td><a href="{novela.get('url', '#')}">{novela.get('url', 'N/A')}</a></td></tr>
                <tr><td style="font-weight:bold;">Creado</td><td>{novela.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('created_at'), datetime) else 'N/A'}</td></tr>
                </table>
                """
                
                intro = epub.EpubHtml(title='Introducción', file_name='intro.xhtml', lang='es')
                intro.content = intro_html
                book.add_item(intro)
                
                # Procesar capítulos con progreso
                chapters = [intro]
                total = len(capitulos)
                zfill_length = len(str(total))
                
                for idx, capitulo in enumerate(capitulos, 1):
                    # Verificar cancelación
                    if cancelar_exportacion:
                        raise Exception("Exportación cancelada por el usuario")
                    
                    nombre_capitulo = capitulo['nombre']
                    contenido = contenido_capitulos_novela.get(str(capitulo['_id']), '')
                    
                    chapter = epub.EpubHtml(
                        title=nombre_capitulo,
                        file_name=f'cap_{idx:0{zfill_length}}.xhtml',
                        lang='es',
                    )
                    chapter.content = f"<h1>{nombre_capitulo}</h1>{contenido}"
                    book.add_item(chapter)
                    chapters.append(chapter)
                    
                    # Actualizar progreso (cada 5 capítulos para rendimiento)
                    if idx % 5 == 0 or idx == total:
                        open_banner(
                            AppColors.BG_ELEVATED,
                            ft.Icon(ft.Icons.BOOK_OUTLINED, color=AppColors.ACCENT_GREEN, size=40),
                            [ft.Text(value=f"📖 [{idx}/{total}] {nombre_capitulo[:40]}...", color=AppColors.TEXT_PRIMARY, size=12)]
                        )
                        page.update()
                
                # Notas y estructura
                notas = epub.EpubHtml(title='Notas', file_name='notas.xhtml', lang='es')
                notas.content = "<h1>Notas</h1><p>Generado con Novelas Manager</p>"
                book.add_item(notas)
                
                book.toc = (
                    epub.Link('intro.xhtml', 'Introducción', 'intro'),
                    (epub.Section('Capítulos'), chapters[1:]),
                    (epub.Section('Apéndices'), [notas])
                )
                book.spine = chapters + [notas]
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                # CSS
                css = epub.EpubItem(
                    uid="style_css", file_name="style/style.css",
                    content="body{font-family:serif;}h1{font-size:1.8em;}table{border:1px solid #ccc;margin:1em 0;}td{border:1px solid #ccc;padding:5px;}"
                )
                book.add_item(css)
                
                # Guardar
                nombre_archivo = sanitizar_nombre(novela['nombre']) + '.epub'
                
                def save_file_result(e: ft.FilePickerResultEvent):
                    try:
                        if e.path is None:
                            open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=AppColors.WARNING, size=40),
                                       [ft.Text(value="⚠️ Operación cancelada", color=AppColors.TEXT_PRIMARY, size=14)])
                            return
                        
                        epub.write_epub(e.path, book, {})
                        logger.info(f"EPUB guardado en: {e.path}")
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
                                   [ft.Text(value="✅ EPUB guardado exitosamente", color=AppColors.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_500)])
                    except PermissionError:
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.LOCK_ROUNDED, color=AppColors.ERROR, size=40),
                                   [ft.Text(value="🔒 Error: Permisos denegados", color=AppColors.TEXT_PRIMARY, size=14)])
                    except Exception as ex:
                        logger.error(f"Error al guardar EPUB: {str(ex)}")
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                   [ft.Text(value=f"❌ Error: {str(ex)[:50]}", color=AppColors.TEXT_PRIMARY, size=14)])
                    finally:
                        limpiar_portada_temporal(portada)
                        page.update()
                
                filepicker.on_result = save_file_result
                filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["epub"])
                
            except Exception as e:
                logger.error(f"Error en crearepub: {str(e)}")
                open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                           [ft.Text(value=f"❌ Error: {str(e)[:60]}", color=AppColors.TEXT_PRIMARY, size=14)])
                limpiar_portada_temporal(portada)
            finally:
                progress_ring.visible = False
                btn_epub.disabled = False
                btn_pdf.disabled = False
                btn_procesar.disabled = False
                page.update()
        
        # Ejecutar en hilo separado
        threading.Thread(target=_epub_worker, daemon=True).start()

    def crearpdf(novela, capitulos):
        """Genera archivo PDF en hilo separado con progreso visual y opción de cancelación."""
        nonlocal cancelar_exportacion
        portada = None  # Para limpieza en finally
        
        def _pdf_worker():
            nonlocal portada, cancelar_exportacion
            try:
                # Preparar UI
                progress_ring.visible = True
                btn_epub.disabled = True
                btn_pdf.disabled = True
                btn_procesar.disabled = True
                page.update()
                
                # Obtener contenido de BD
                contenido_capitulos_novela = obtener_contenido_capitulos(novela['_id'])
                
                # Verificar cancelación
                if cancelar_exportacion:
                    raise Exception("Exportación cancelada por el usuario")
                
                # Descargar portada (una sola lectura)
                portada, _ = descargar_y_preparar_portada(novela['imagen_url'])
                
                # Traducciones
                nombre_traducido = traducir(novela['nombre']) or novela['nombre']
                sinopsis_traducida = traducir(novela['sinopsis']) or novela['sinopsis']
                
                # Crear PDF
                pdf = PDF(orientation='P', unit='mm', format='A4')
                pdf.add_font('Poppins-Regular', '', PINGO_FONT_PATH, uni=True)
                pdf.set_font('Poppins-Regular', size=12)
                pdf.set_title(nombre_traducido)
                pdf.set_author(novela['autor'])
                pdf.set_creator('Novelas Manager - David Eliceo Vite Vergara')
                pdf.alias_nb_pages()
                
                # Página inicial con portada
                pdf.add_page()
                pdf.chapter_title(nombre_traducido)
                pdf.image(name=portada, x=pdf.epw / 3, w=75)
                pdf.write_html(text="<h5>Resumen:</h5>")
                pdf.write_html(text=f"<p>{sinopsis_traducida}</p>")
                pdf.write(text=f"Url de Novela: {novela['url']}")
                
                # Procesar capítulos con progreso
                total = len(capitulos)
                
                for idx, capitulo in enumerate(capitulos, 1):
                    # Verificar cancelación
                    if cancelar_exportacion:
                        raise Exception("Exportación cancelada por el usuario")
                    
                    capitulo_id = str(capitulo['_id'])
                    nombre_capitulo = capitulo['nombre']
                    contenido = contenido_capitulos_novela.get(capitulo_id, '')
                    
                    pdf.print_chapter(f"{nombre_capitulo}", f"{contenido}")
                    
                    # Actualizar progreso (cada 5 capítulos para rendimiento)
                    if idx % 5 == 0 or idx == total:
                        open_banner(
                            AppColors.BG_ELEVATED,
                            ft.Icon(ft.Icons.PICTURE_AS_PDF_OUTLINED, color=AppColors.ACCENT_GREEN, size=40),
                            [ft.Text(value=f"📄 [{idx}/{total}] {nombre_capitulo[:40]}...", color=AppColors.TEXT_PRIMARY, size=12)]
                        )
                        page.update()
                
                # Guardar
                nombre_archivo = sanitizar_nombre(novela['nombre']) + '.pdf'
                
                def save_file_result(e: ft.FilePickerResultEvent):
                    try:
                        if e.path is None:
                            open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=AppColors.WARNING, size=40),
                                       [ft.Text(value="⚠️ Operación cancelada", color=AppColors.TEXT_PRIMARY, size=14)])
                            return
                        
                        with open(e.path, 'wb') as filepdf:
                            pdf.output(filepdf)
                        
                        logger.info(f"PDF guardado en: {e.path}")
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
                                   [ft.Text(value="✅ PDF guardado exitosamente", color=AppColors.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_500)])
                    except PermissionError:
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.LOCK_ROUNDED, color=AppColors.ERROR, size=40),
                                   [ft.Text(value="🔒 Error: Permisos denegados", color=AppColors.TEXT_PRIMARY, size=14)])
                    except Exception as ex:
                        logger.error(f"Error al guardar PDF: {str(ex)}")
                        open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                   [ft.Text(value=f"❌ Error: {str(ex)[:50]}", color=AppColors.TEXT_PRIMARY, size=14)])
                    finally:
                        limpiar_portada_temporal(portada)
                        page.update()
                
                filepicker.on_result = save_file_result
                filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["pdf"])
                
            except Exception as e:
                logger.error(f"Error en crearpdf: {str(e)}")
                open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                           [ft.Text(value=f"❌ Error: {str(e)[:60]}", color=AppColors.TEXT_PRIMARY, size=14)])
                limpiar_portada_temporal(portada)
            finally:
                progress_ring.visible = False
                btn_epub.disabled = False
                btn_pdf.disabled = False
                btn_procesar.disabled = False
                page.update()
        
        # Ejecutar en hilo separado
        threading.Thread(target=_pdf_worker, daemon=True).start()

    def show_loading():
        AppState.loading = True
        page.splash = ft.ProgressBar(color=AppColors.PRIMARY_LIGHT, bgcolor=AppColors.BG_ELEVATED)
        page.update()

    def hide_loading():
        AppState.loading = False
        page.splash = None
        page.update()

    def load_home_data():
        try:
            sitios = []
            for sitio in collection_sitios.find():
                sitios.append(sitio)
            return sitios
        except Exception as e:
            logger.error(f"Error loading home: {e}")
            return []

    # --- Modificar load_sitio_details para paginación ---
    def load_sitio_details_paginado(sitio_id, pagina=1, por_pagina=NOVELAS_POR_PAGINA):
        """
        Carga detalles del sitio y un subconjunto paginado de novelas.
        Devuelve: (sitio_doc, lista_novelas_pagina, total_novelas)
        """
        try:
            sitio = collection_sitios.find_one({'_id': ObjectId(sitio_id)})
            if not sitio:
                return None, [], 0

            skip = (pagina - 1) * por_pagina
            # 1. Obtener el conteo total de novelas para este sitio
            total_novelas = collection_novelas.count_documents({'sitio_id': sitio_id})
            # 2. Obtener solo las novelas para la página actual
            novelas_cursor = collection_novelas.find({'sitio_id': sitio_id}).skip(skip).limit(por_pagina).sort('_id', 1) # Ordenar para consistencia
            novelas_pagina = list(novelas_cursor) # Convertir cursor a lista

            return sitio, novelas_pagina, total_novelas
        except Exception as e:
            logger.error(f"Error loading sitio details (paginado) for sitio {sitio_id}, page {pagina}: {e}")
            return None, [], 0

    def load_novela_details(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort
            return collection_novelas.find_one({'_id': ObjectId(novela_id)}), [capitulo for capitulo in collection_capitulos.find({'novela_id': novela_id}).sort('created_at', 1)]
        except Exception as e:
            logger.error(f"Error loading novela details: {e}")
            return None, []

    def load_ids_capitulos_novela(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort y projection correctamente
            return {str(capitulo['_id']) for capitulo in collection_capitulos.find({'novela_id': novela_id}, {'_id': 1}).sort('created_at', 1)}
        except Exception as e:
            logger.error(f"Error loading capitulo novela details: {e}")
            return set() # Devolver un conjunto vacío en caso de error

    def load_ids_urls_capitulos_novela(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort y projection correctamente
            return {str(capitulo['_id']):capitulo['url'] for capitulo in collection_capitulos.find({'novela_id': novela_id}, {'_id': 1, 'url': 1}).sort('created_at', 1)}
        except Exception as e:
            logger.error(f"Error loading ids urls capitulos details: {e}")
            return {} # Devolver un diccionario vacío en caso de error

    def load_ids_contenido_capitulos_novela(novela_id):
        """Retorna un set de IDs de capítulos con contenido descargado para búsquedas O(1)"""
        try:
            return {str(contenido['capitulo_id']) for contenido in collection_contenido_capitulos.find({'novela_id': novela_id}, {'capitulo_id': 1, '_id': 0}).sort('created_at', 1)}
        except Exception as e:
            logger.error(f"Error loading ids contenido capitulos novela details: {e}")
            return set()  # Devolver un conjunto vacío en caso de error

    def comparar_diccionarios(dic1, dic2):
        return [x for x in dic1 if x not in dic2]

    def instanciar_driver():
        # options = webdriver.ChromeOptions()
        options = webdriver.FirefoxOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        # return uc.Chrome(options=options, service = Service(executable_path=ChromeDriverManager().install()))
        return webdriver.Firefox(options=options, service=Service(executable_path=f"{os.getcwd()}/geckodriver/geckodriver.exe"))

    def obtener_capitulos_webscrapping(cap_faltantes, novela_id):
        global contar_capitulos
        global lista_capitulos
        global ids_contenido_capitulo # Asegurarse de usar la global
        global mapa_capitulo_indice
        global pagina_capitulos_actual
        progress_ring.visible = True
        page.update()

        urls_capitulos = load_ids_urls_capitulos_novela(novela_id)
        driver = instanciar_driver()
        try: # Añadir try/finally para asegurar driver.quit()
            for cap in urls_capitulos:
                if str(cap) in cap_faltantes:
                    max_intentos = 3 # Añadir límite de reintentos
                    intento = 0
                    while intento < max_intentos:
                        try:
                            driver.get(urls_capitulos[cap])
                            manejar_driver_capitulos(driver, novela_id, str(cap))
                            
                            # Actualizar siempre el contador y el set
                            contar_capitulos += 1
                            txt_number.value = str(contar_capitulos)
                            ids_contenido_capitulo.add(str(cap))  # Usar .add() para set
                            
                            # Actualizar UI solo si el capítulo es visible en la página actual
                            es_visible, idx_rel = calcular_visibilidad_capitulo(str(cap))
                            if es_visible and 0 <= idx_rel < len(lista_capitulos):
                                # Actualizar el ícono del capítulo descargado
                                container = lista_capitulos[idx_rel]
                                if hasattr(container, 'content') and hasattr(container.content, 'controls'):
                                    row_controls = container.content.controls
                                    if len(row_controls) >= 3:
                                        # Actualizar el contenedor del número
                                        row_controls[0].bgcolor = AppColors.ACCENT_GREEN
                                        row_controls[0].content.color = AppColors.TEXT_PRIMARY
                                        # Actualizar el texto del capítulo
                                        if hasattr(row_controls[1], 'controls') and len(row_controls[1].controls) > 0:
                                            row_controls[1].controls[0].color = AppColors.TEXT_PRIMARY
                                        # Actualizar el ícono de estado
                                        row_controls[2].name = ft.Icons.CHECK_CIRCLE_ROUNDED
                                        row_controls[2].color = AppColors.ACCENT_GREEN
                                        # Actualizar fondo del contenedor
                                        container.bgcolor = ft.Colors.with_opacity(0.05, AppColors.ACCENT_GREEN)
                                        container.border = ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.ACCENT_GREEN))
                            
                            page.update()
                            break
                        except requests.exceptions.RequestException as re:
                            intento += 1
                            logger.warning(f"Intento {intento} fallido para capítulo {cap} (Error de red): {re}")
                            if intento == max_intentos:
                                logger.error(f"Error persistente de red al obtener capítulo {cap}")
                                open_banner(
                                    AppColors.BG_ELEVATED,
                                    ft.Icon(ft.Icons.WIFI_OFF_ROUNDED, color=AppColors.ERROR, size=40),
                                    [
                                        ft.Text(
                                            value=f"📡 Error de red en capítulo {cap}",
                                            color=AppColors.TEXT_PRIMARY,
                                            size=14,
                                        ),
                                    ]
                                )
                            time.sleep(2) # Esperar antes de reintentar
                        except Exception as error:
                            intento += 1
                            logger.error(f"Intento {intento} fallido para capítulo {cap} (Error desconocido): {error}")
                            if intento == max_intentos:
                                logger.error(f"Error persistente al obtener capítulo {cap}")
                                open_banner(
                                    AppColors.BG_ELEVATED,
                                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                    [
                                        ft.Text(
                                            value=f"❌ Error al obtener capítulo {cap}",
                                            color=AppColors.TEXT_PRIMARY,
                                            size=14,
                                        ),
                                    ]
                                )
                            time.sleep(2) # Esperar antes de reintentar
        finally:
            driver.quit()
            logger.info("WebDriver cerrado.")
        progress_ring.visible = False
        btn_procesar.disabled = True
        btn_epub.disabled = False
        btn_pdf.disabled = False
        page.update()
        # No es necesario navegar de nuevo, la vista se actualiza por el page.update()
        # navigate_to_novela_detail(novela_id)

    def create_sitio_button(sitio):
        """Crea un botón de sitio con diseño de tarjeta moderna"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.LANGUAGE_ROUNDED,
                            color=AppColors.PRIMARY_LIGHT,
                            size=36,
                        ),
                        padding=15,
                        border_radius=50,
                        bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
                    ),
                    ft.Text(
                        sitio['nombre'],
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.TEXT_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        sitio.get('url', 'Sin URL')[:30] + '...' if len(sitio.get('url', '')) > 30 else sitio.get('url', 'Sin URL'),
                        size=10,
                        color=AppColors.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
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
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
                offset=ft.Offset(0, 4),
            ),
            on_click=lambda e, id=sitio['_id']: navigate_to_detail(id),
            on_hover=lambda e: setattr(e.control, 'bgcolor', AppColors.BG_ELEVATED if e.data == "true" else AppColors.BG_CARD) or page.update(),
            ink=True,
            ink_color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
            tooltip=f"🌐 Ver novelas de {sitio['nombre']}",
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def create_novela_card(novela):
        """Crea una tarjeta de novela con diseño moderno y efectos hover"""
        # Determinar color de estado
        status = novela.get('status', '').lower()
        status_color = AppColors.ACCENT_GREEN if 'complet' in status else AppColors.ACCENT_ORANGE if 'ongoing' in status else AppColors.TEXT_MUTED
        status_text = novela.get('status', 'Desconocido')[:15]
        
        return ft.Container(
            content=ft.Stack(
                controls=[
                    # Imagen de fondo con overlay
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
                    # Gradiente oscuro en la parte inferior
                    ft.Container(
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_center,
                            end=ft.alignment.bottom_center,
                            colors=[
                                ft.Colors.TRANSPARENT,
                                ft.Colors.TRANSPARENT,
                                ft.Colors.with_opacity(0.7, AppColors.BG_DARK),
                                ft.Colors.with_opacity(0.95, AppColors.BG_DARK),
                            ],
                        ),
                        border_radius=ft.border_radius.all(14),
                    ),
                    # Contenido superpuesto
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                # Badge de estado en la esquina superior
                                ft.Container(
                                    content=ft.Text(
                                        status_text,
                                        size=9,
                                        weight=ft.FontWeight.W_600,
                                        color=AppColors.TEXT_PRIMARY,
                                    ),
                                    bgcolor=status_color,
                                    padding=ft.Padding(8, 4, 8, 4),
                                    border_radius=8,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(expand=True),  # Espaciador
                                # Título de la novela
                                ft.Text(
                                    novela['nombre'],
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT_PRIMARY,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                                # Autor
                                ft.Text(
                                    f"✍️ {novela.get('autor', 'Desconocido')[:20]}",
                                    size=9,
                                    color=AppColors.TEXT_MUTED,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.Padding(10, 8, 10, 12),
                    ),
                ],
            ),
            width=180,
            height=260,
            border_radius=14,
            bgcolor=AppColors.BG_CARD,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.25, AppColors.BG_DARK),
                offset=ft.Offset(0, 4),
            ),
            on_click=lambda e, id=novela['_id']: navigate_to_novela_detail(id),
            on_hover=lambda e: (
                setattr(e.control, 'scale', 1.03 if e.data == "true" else 1.0),
                setattr(e.control, 'shadow', ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20 if e.data == "true" else 12,
                    color=ft.Colors.with_opacity(0.4 if e.data == "true" else 0.25, AppColors.PRIMARY),
                    offset=ft.Offset(0, 8 if e.data == "true" else 4),
                )),
                page.update()
            ),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            ink=True,
            ink_color=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
        )

    def create_home_view():
        show_loading()
        sitios = load_home_data()
        
        # Header decorativo
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, size=40, color=AppColors.PRIMARY_LIGHT),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Novelas Manager",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        "Gestiona y descarga tus novelas favoritas",
                                        size=13,
                                        color=AppColors.TEXT_MUTED,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    # Estadísticas rápidas
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
                spread_radius=0,
                blur_radius=20,
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
                    content=ft.Text(
                        "📚 Selecciona un sitio para explorar",
                        size=14,
                        color=AppColors.TEXT_MUTED,
                        weight=ft.FontWeight.W_500,
                    ),
                    padding=ft.Padding(25, 10, 25, 5),
                ),
                ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=220,
                    spacing=20,
                    run_spacing=20,
                    padding=ft.Padding(20, 10, 20, 20),
                    controls=[create_sitio_button(sitio) for sitio in sitios]
                )
            ],
            bgcolor=AppColors.BG_DARK,
            padding=0,
        )

    # --- Modificar create_detail_view para manejar paginación ---
    def create_detail_view(sitio_id, pagina=1):
        logger.info(f"Cargando vista de sitio {sitio_id}, página {pagina}")
        sitio, novelas_pagina, total_novelas = load_sitio_details_paginado(sitio_id, pagina, NOVELAS_POR_PAGINA)
        
        if not sitio:
            return ft.View(
                f"/sitio/{sitio_id}",
                [
                    ft.AppBar(
                        title=ft.Text("Error", size=16),
                        bgcolor=AppColors.ERROR,
                        leading=ft.IconButton(
                            ft.Icons.ARROW_BACK,
                            on_click=lambda _: page.go("/"),
                            icon_color=AppColors.TEXT_PRIMARY,
                        )
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=60, color=AppColors.ERROR),
                            ft.Text("Sitio no encontrado", size=20, color=AppColors.TEXT_PRIMARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                        alignment=ft.alignment.center,
                        expand=True,
                    )
                ],
                bgcolor=AppColors.BG_DARK,
            )

        total_paginas = (total_novelas + NOVELAS_POR_PAGINA - 1) // NOVELAS_POR_PAGINA

        def ir_a_pagina(p):
            page.go(f"/sitio/{sitio_id}?pagina={p}")

        # --- Controles de Paginación Modernos ---
        controles_paginacion = []
        if total_paginas > 1:
            btn_anterior = ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
                    icon_size=24,
                    disabled=(pagina <= 1),
                    on_click=lambda _: ir_a_pagina(pagina - 1) if pagina > 1 else None,
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
                    icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
                    icon_size=24,
                    disabled=(pagina >= total_paginas),
                    on_click=lambda _: ir_a_pagina(pagina + 1) if pagina < total_paginas else None,
                    icon_color=AppColors.PRIMARY_LIGHT if pagina < total_paginas else AppColors.TEXT_MUTED,
                    tooltip="Página Siguiente",
                ),
                bgcolor=AppColors.BG_CARD if pagina < total_paginas else ft.Colors.TRANSPARENT,
                border_radius=10,
            )
            
            controles_paginacion = [
                ft.Container(
                    content=ft.Row(
                        controls=[btn_anterior, txt_pagina, btn_siguiente],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    padding=ft.Padding(0, 10, 0, 10),
                )
            ]

        # --- Header del sitio con información ---
        site_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.LANGUAGE_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=28),
                        padding=12,
                        border_radius=50,
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
                        on_click=lambda _: page.go("/"),
                        icon_color=AppColors.TEXT_PRIMARY,
                        tooltip="Volver al inicio",
                    ),
                    elevation=0,
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
                    controls=[create_novela_card(novela) for novela in novelas_pagina]
                ),
                *controles_paginacion,
            ],
            bgcolor=AppColors.BG_DARK,
            spacing=5,
            padding=0,
        )

    def create_novel_detail_view(novela_id):
        global contar_capitulos
        global lista_capitulos
        global ids_contenido_capitulo # Asegurarse de usar la global
        global mapa_capitulo_indice
        global pagina_capitulos_actual
        global todos_capitulos
        global debounce_timer
        global lv_capitulos
        global spinner_paginacion
        global total_paginas_capitulos
        
        show_loading()
        contar_capitulos=0
        novela, capitulos = load_novela_details(novela_id)
        if not novela:
            return ft.View(
                f"/novela/{novela_id}",
                [
                    ft.AppBar(
                        title=ft.Text("Error", size=16),
                        bgcolor=ft.Colors.ERROR,
                        leading=ft.IconButton(
                            ft.Icons.ARROW_BACK,
                            on_click=lambda _: page.go("/")
                        )
                    ),
                    ft.Text("Sitio no encontrado", size=20)
                ]
            )

        ids_contenido_capitulo = load_ids_contenido_capitulos_novela(novela_id) # Actualizar la global
        contar_capitulos = len(ids_contenido_capitulo)
        txt_number.value=str(contar_capitulos)
        
        # Guardar todos los capítulos para exportación y mapeo
        todos_capitulos = capitulos
        mapa_capitulo_indice = {str(cap['_id']): idx for idx, cap in enumerate(capitulos, 1)}
        
        # Restaurar página de sesión o empezar en 1
        pagina_capitulos_actual = page.session.get(f"pagina_caps_{novela_id}") or 1
        total_paginas_capitulos = max(1, (len(capitulos) + CAPITULOS_POR_PAGINA - 1) // CAPITULOS_POR_PAGINA)
        
        # Asegurar que la página actual es válida
        if pagina_capitulos_actual > total_paginas_capitulos:
            pagina_capitulos_actual = 1

        # --- Lista de capítulos con diseño moderno ---
        def create_chapter_item(capitulo, index):
            is_downloaded = str(capitulo['_id']) in ids_contenido_capitulo
            return ft.Container(
                content=ft.Row([
                    # Número de capítulo
                    ft.Container(
                        content=ft.Text(f"{index}", size=11, weight=ft.FontWeight.W_600, 
                                       color=AppColors.TEXT_PRIMARY if is_downloaded else AppColors.TEXT_MUTED),
                        width=35,
                        height=35,
                        border_radius=8,
                        bgcolor=AppColors.ACCENT_GREEN if is_downloaded else AppColors.BG_ELEVATED,
                        alignment=ft.alignment.center,
                    ),
                    # Información del capítulo
                    ft.Column([
                        ft.Text(capitulo['nombre'][:50] + ('...' if len(capitulo['nombre']) > 50 else ''), 
                               size=12, weight=ft.FontWeight.W_500, 
                               color=AppColors.TEXT_PRIMARY if is_downloaded else AppColors.TEXT_SECONDARY),
                        ft.Text(
                            f"{capitulo.get('created_at', 'N/A').strftime('%d/%m/%Y') if isinstance(capitulo.get('created_at'), datetime) else 'Sin fecha'}",
                            size=10, color=AppColors.TEXT_MUTED
                        ),
                    ], spacing=2, expand=True),
                    # Icono de estado
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
        
        def obtener_capitulos_pagina(pagina):
            """Obtiene los capítulos de la página indicada."""
            inicio = (pagina - 1) * CAPITULOS_POR_PAGINA
            fin = inicio + CAPITULOS_POR_PAGINA
            return capitulos[inicio:fin], inicio + 1  # Retorna capítulos y offset para índices
        
        def actualizar_lista_capitulos(pagina):
            """Actualiza la lista de capítulos para la página dada."""
            global pagina_capitulos_actual
            pagina_capitulos_actual = pagina
            page.session.set(f"pagina_caps_{novela_id}", pagina)  # Persistir en sesión
            
            caps_pagina, offset = obtener_capitulos_pagina(pagina)
            lista_capitulos.clear()
            for idx, cap in enumerate(caps_pagina):
                lista_capitulos.append(create_chapter_item(cap, offset + idx))
            
            # Actualizar UI de paginación
            txt_pagina_actual.value = f"{pagina}/{total_paginas_capitulos}"
            input_ir_pagina.value = str(pagina)
            btn_anterior.disabled = (pagina <= 1)
            btn_siguiente.disabled = (pagina >= total_paginas_capitulos)
            
        def ir_pagina_anterior(e):
            """Navega a la página anterior."""
            if pagina_capitulos_actual > 1:
                spinner_paginacion.visible = True
                page.update()
                actualizar_lista_capitulos(pagina_capitulos_actual - 1)
                spinner_paginacion.visible = False
                page.update()
        
        def ir_pagina_siguiente(e):
            """Navega a la página siguiente."""
            if pagina_capitulos_actual < total_paginas_capitulos:
                spinner_paginacion.visible = True
                page.update()
                actualizar_lista_capitulos(pagina_capitulos_actual + 1)
                spinner_paginacion.visible = False
                page.update()
        
        def ir_a_pagina_debounced(e):
            """Maneja el cambio de página con debounce de 200ms."""
            global debounce_timer
            if debounce_timer:
                debounce_timer.cancel()
            
            def ejecutar_cambio():
                try:
                    pagina = int(input_ir_pagina.value or "1")
                    pagina = max(1, min(pagina, total_paginas_capitulos))
                    spinner_paginacion.visible = True
                    page.update()
                    actualizar_lista_capitulos(pagina)
                    spinner_paginacion.visible = False
                    page.update()
                except ValueError:
                    pass
            
            debounce_timer = threading.Timer(0.2, ejecutar_cambio)
            debounce_timer.start()
        
        # Crear controles de paginación
        btn_anterior = ft.IconButton(
            ft.Icons.CHEVRON_LEFT_ROUNDED,
            on_click=ir_pagina_anterior,
            icon_color=AppColors.PRIMARY_LIGHT,
            icon_size=20,
            tooltip="Página anterior",
            disabled=(pagina_capitulos_actual <= 1),
        )
        
        btn_siguiente = ft.IconButton(
            ft.Icons.CHEVRON_RIGHT_ROUNDED,
            on_click=ir_pagina_siguiente,
            icon_color=AppColors.PRIMARY_LIGHT,
            icon_size=20,
            tooltip="Página siguiente",
            disabled=(pagina_capitulos_actual >= total_paginas_capitulos),
        )
        
        txt_pagina_actual = ft.Text(
            f"{pagina_capitulos_actual}/{total_paginas_capitulos}", 
            size=11, color=AppColors.TEXT_SECONDARY
        )
        
        input_ir_pagina = ft.TextField(
            value=str(pagina_capitulos_actual),
            width=50,
            height=32,
            text_size=11,
            text_align=ft.TextAlign.CENTER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY_LIGHT,
            input_filter=ft.NumbersOnlyInputFilter(),
            on_change=ir_a_pagina_debounced,
        )
        
        spinner_paginacion = ft.ProgressRing(
            width=16, height=16, 
            stroke_width=2, 
            color=AppColors.PRIMARY_LIGHT,
            visible=False,
        )
        
        # Inicializar lista de capítulos con la página actual
        caps_inicial, offset_inicial = obtener_capitulos_pagina(pagina_capitulos_actual)
        lista_capitulos = [create_chapter_item(cap, offset_inicial + idx) for idx, cap in enumerate(caps_inicial)]
        
        # Crear el ListView referenciado globalmente
        lv_capitulos = ft.ListView(
            controls=lista_capitulos,
            spacing=4,
            height=350,
        )

        # Usar todos_capitulos para exportación (todos los capítulos, no solo la página actual)
        btn_epub.on_click=lambda _: crearepub(novela, todos_capitulos)
        btn_epub.disabled=False if len(todos_capitulos) == contar_capitulos else True
        btn_pdf.on_click=lambda _: crearpdf(novela, todos_capitulos)
        btn_pdf.disabled=False if len(todos_capitulos) == contar_capitulos else True

        cap_faltantes = comparar_diccionarios([str(x['_id']) for x in todos_capitulos], ids_contenido_capitulo)
        btn_procesar.disabled= not (len(cap_faltantes) > 0) # Corrección: lógica más clara
        btn_procesar.on_click=lambda _: obtener_capitulos_webscrapping(cap_faltantes, novela_id)

        # IDs de Sitios (Constantes para mejorar mantenibilidad)
        FANMTL_SITIO_ID = '67de23f6e131d527f2995103'
        TUNOVELA_LIGERA_SITIO_ID = '680ecb15e1ce8081ecb8b4d1'

        etiquetas = {
            '_id': 'Novela ID',
            'sitio_id':'Sitio ID',
            'nombre': 'Nombre Novela',
            'sinopsis': 'Sinopsis Novela',
            'autor': 'Autor Novela',
            'genero': 'Generos Novela',
            'status': 'Status Novela', # Corrección ortográfica
            'url': 'Url Novela',
            'imagen_url': 'Url Imagen Novela',
            'created_at': 'Fecha Creacion en Base de Datos',
            'updated_at': 'Fecha Modificacion en Base de Datos',
        }

        # --- Determinar estado de la novela para badge ---
        status = novela.get('status', '').lower()
        status_color = AppColors.ACCENT_GREEN if 'complet' in status else AppColors.ACCENT_ORANGE if 'ongoing' in status else AppColors.TEXT_MUTED
        status_icon = ft.Icons.CHECK_CIRCLE_ROUNDED if 'complet' in status else ft.Icons.PENDING_ROUNDED
        
        # --- Calcular porcentaje de progreso ---
        progreso_porcentaje = (contar_capitulos / len(capitulos) * 100) if len(capitulos) > 0 else 0
        
        # --- Vista de detalles con diseño moderno ---
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
                        on_click=lambda _: navigate_to_detail(novela['sitio_id']),
                        icon_color=AppColors.TEXT_PRIMARY,
                        tooltip="Volver a la lista",
                    ),
                    elevation=0,
                ),
                # --- Sección principal con información de la novela ---
                ft.ResponsiveRow([
                    # Columna de la imagen con efectos
                    ft.Column(
                        col={"xs": 12, "sm": 12, "md": 3},
                        controls=[
                            ft.Container(
                                content=ft.Image(
                                    src=novela['imagen_url'],
                                    fit=ft.ImageFit.CONTAIN,
                                    border_radius=ft.border_radius.all(16),
                                    height=250,
                                ),
                                border_radius=16,
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=20,
                                    color=ft.Colors.with_opacity(0.4, AppColors.PRIMARY),
                                    offset=ft.Offset(0, 8),
                                ),
                                margin=ft.Margin(0, 0, 0, 10),
                            ),
                            # Badge de estado
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
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    # Columna de los detalles
                    ft.Column(
                        col={"xs": 12, "sm": 12, "md": 9},
                        controls=[
                            # Título de la novela
                            ft.Text(novela['nombre'], size=20, weight=ft.FontWeight.BOLD, 
                                   color=AppColors.TEXT_PRIMARY),
                            ft.Container(height=10),
                            # Info cards en fila
                            ft.Row([
                                ft.Container(
                                    content=ft.Column([
                                        ft.Icon(ft.Icons.PERSON_ROUNDED, color=AppColors.SECONDARY, size=18),
                                        ft.Text("Autor", size=9, color=AppColors.TEXT_MUTED),
                                        ft.Text(novela.get('autor', 'Desconocido')[:20], size=11, 
                                               weight=ft.FontWeight.W_500, color=AppColors.TEXT_PRIMARY),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=10,
                                    border_radius=10,
                                    bgcolor=AppColors.BG_ELEVATED,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Icon(ft.Icons.CATEGORY_ROUNDED, color=AppColors.ACCENT_PINK, size=18),
                                        ft.Text("Género", size=9, color=AppColors.TEXT_MUTED),
                                        ft.Text(novela.get('genero', 'N/A')[:20], size=11, 
                                               weight=ft.FontWeight.W_500, color=AppColors.TEXT_PRIMARY),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=10,
                                    border_radius=10,
                                    bgcolor=AppColors.BG_ELEVATED,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=AppColors.ACCENT_ORANGE, size=18),
                                        ft.Text("Capítulos", size=9, color=AppColors.TEXT_MUTED),
                                        ft.Text(f"{len(capitulos)}", size=11, 
                                               weight=ft.FontWeight.W_500, color=AppColors.TEXT_PRIMARY),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=10,
                                    border_radius=10,
                                    bgcolor=AppColors.BG_ELEVATED,
                                    expand=True,
                                ),
                            ], spacing=8),
                            ft.Container(height=10),
                            # Sinopsis
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=16),
                                        ft.Text("Sinopsis", size=13, weight=ft.FontWeight.W_600, color=AppColors.TEXT_PRIMARY),
                                    ], spacing=6),
                                    ft.Text(
                                        novela.get('sinopsis', 'Sin sinopsis disponible')[:300] + ('...' if len(novela.get('sinopsis', '')) > 300 else ''),
                                        size=11,
                                        color=AppColors.TEXT_SECONDARY,
                                    ),
                                ], spacing=6),
                                padding=12,
                                border_radius=10,
                                bgcolor=AppColors.BG_CARD,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
                            ),
                        ],
                    ),
                ], spacing=15, run_spacing=10),
                ft.Divider(height=1, color=AppColors.BORDER),
                # --- Sección de progreso y controles ---
                ft.ResponsiveRow([
                    # Panel de progreso
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("📊 Progreso", size=13, weight=ft.FontWeight.W_600, 
                                       color=AppColors.TEXT_PRIMARY),
                                ft.Container(height=8),
                                # Indicador de progreso
                                ft.Row([
                                    txt_number,
                                    ft.Text(f" / {len(capitulos)}", size=14, color=AppColors.TEXT_MUTED),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.ProgressBar(
                                    value=progreso_porcentaje / 100,
                                    color=AppColors.ACCENT_GREEN if progreso_porcentaje == 100 else AppColors.PRIMARY,
                                    bgcolor=AppColors.BG_ELEVATED,
                                ),
                                ft.Text(f"{progreso_porcentaje:.1f}%", size=10, 
                                       color=AppColors.ACCENT_GREEN if progreso_porcentaje == 100 else AppColors.TEXT_MUTED),
                                ft.Container(height=10),
                                # Botones de acción
                                btn_epub,
                                btn_pdf,
                                btn_procesar,
                                ft.Container(height=5),
                                ft.Container(
                                    content=progress_ring,
                                    alignment=ft.alignment.center,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                            padding=15,
                            border_radius=12,
                            bgcolor=AppColors.BG_CARD,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.1, AppColors.BORDER)),
                        ),
                    ], col={"xs": 12, "sm": 12, "md": 3}),
                    # Lista de capítulos
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.LIST_ALT_ROUNDED, color=AppColors.PRIMARY_LIGHT, size=18),
                                    ft.Text("Capítulos", size=13, weight=ft.FontWeight.W_600, 
                                           color=AppColors.TEXT_PRIMARY),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Text(f"{contar_capitulos}/{len(todos_capitulos)}", size=11, 
                                                       weight=ft.FontWeight.W_600, color=AppColors.ACCENT_GREEN),
                                        padding=ft.Padding(8, 3, 8, 3),
                                        border_radius=15,
                                        bgcolor=ft.Colors.with_opacity(0.15, AppColors.ACCENT_GREEN),
                                    ),
                                ], spacing=8),
                                ft.Container(height=8),
                                # Controles de paginación
                                ft.Row([
                                    btn_anterior,
                                    txt_pagina_actual,
                                    btn_siguiente,
                                    ft.Container(width=10),
                                    ft.Text("Ir a:", size=10, color=AppColors.TEXT_MUTED),
                                    input_ir_pagina,
                                    spinner_paginacion,
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                                ft.Container(height=6),
                                lv_capitulos,
                            ]),
                            padding=12,
                            border_radius=12,
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

    # --- Modificar route_change para manejar el parámetro de página ---
    def route_change(route):
        # ... manejo de loading ...
        page.views.clear()
        if page.route == "/":
            page.views.append(create_home_view())
        else:
            parts = page.route.split("?")[0].split("/") # Separar ruta de query params
            query_params = {}
            if "?" in page.route:
                query_string = page.route.split("?")[1]
                # Parseo básico más robusto
                try:
                    query_params = dict(param.split("=") for param in query_string.split("&") if param)
                except ValueError:
                    logger.warning(f"Error al parsear query params: {query_string}")
                    query_params = {}

            pagina = int(query_params.get("pagina", 1)) # Obtener página, por defecto 1
            if len(parts) > 2 and parts[1] == "sitio":
                # Pasar el número de página a create_detail_view
                page.views.append(create_detail_view(parts[2], pagina=pagina))
            elif len(parts) > 2 and parts[1] == "novela":
                page.views.append(create_novel_detail_view(parts[2]))
        # ... manejo de loading ...
        page.update()

    def navigate_to_detail(sitio_id):
        page.go(f"/sitio/{sitio_id}")

    def navigate_to_novela_detail(novel_id):
        page.go(f"/novela/{novel_id}")

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)