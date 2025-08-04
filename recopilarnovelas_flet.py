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

# --- Tema Oscuro Personalizado ---
def create_dark_theme():
    return ft.Theme(
        color_scheme_seed=ft.Colors.DEEP_PURPLE,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.DEEP_PURPLE_300, # Colores más claros para modo oscuro
            secondary=ft.Colors.TEAL_300,
            surface=ft.Colors.GREY_800, # Superficies oscuras
            background=ft.Colors.GREY_900, # Fondo muy oscuro
            on_surface=ft.Colors.WHITE, # Texto sobre superficies oscuras
            on_background=ft.Colors.WHITE, # Texto sobre fondo
            error=ft.Colors.RED_300, # Errores más claros
        ),
        text_theme=ft.TextTheme(
            headline_medium=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            headline_small=ft.TextStyle(size=20, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            title_medium=ft.TextStyle(size=16, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            body_medium=ft.TextStyle(size=14, color=ft.Colors.GREY_300), # Cuerpo de texto más claro
            body_small=ft.TextStyle(size=12, color=ft.Colors.GREY_400),
        ),
        visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        # Ajustar colores de componentes específicos para el modo oscuro
        appbar_theme=ft.AppBarTheme(
            color=ft.Colors.WHITE, # Color del texto del AppBar
        ),
        elevated_button_theme=ft.ElevatedButtonTheme(
            text_style=ft.ButtonStyle(
                color=ft.Colors.WHITE, # Texto blanco en botones
                # bgcolor se define en los botones individuales
            )
        ),
        card_theme=ft.CardTheme(
            color=ft.Colors.GREY_800, # Color de fondo de las tarjetas
            surface_tint_color=ft.Colors.GREY_700 # Tinte de superficie
        ),
        list_tile_theme=ft.ListTileTheme(
            icon_color=ft.Colors.DEEP_PURPLE_200, # Color de íconos en ListTile
            text_color=ft.Colors.GREY_300 # Color de texto en ListTile
        )
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
    page.title = "Consulta de Novelas"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK # Activar modo oscuro
    # Aplicar tema oscuro personalizado
    page.theme = create_dark_theme()
    
    filepicker = ft.FilePicker()
    save_file_path = ft.Text()
    page.overlay.append(filepicker)

    contar_capitulos = 0
    lista_capitulos = []
    ids_contenido_capitulo = []
    txt_number = ft.Text(value="0", text_align=ft.TextAlign.CENTER, size=16, weight=ft.FontWeight.BOLD)
    
    # --- Botones con estilo mejorado para tema oscuro ---
    btn_epub=ft.ElevatedButton(
        "Epub",
        bgcolor=ft.Colors.GREEN_700, # Verde más oscuro para contraste
        color=ft.Colors.WHITE,
        expand=True,
        icon=ft.Icons.BOOK,
        icon_color=ft.Colors.WHITE,
        tooltip="Generar archivo EPUB"
    )
    btn_pdf=ft.ElevatedButton(
        "PDF",
        bgcolor=ft.Colors.RED_700, # Rojo más oscuro para contraste
        color=ft.Colors.WHITE,
        expand=True,
        icon=ft.Icons.PICTURE_AS_PDF,
        icon_color=ft.Colors.WHITE,
        tooltip="Generar archivo PDF"
    )
    btn_procesar=ft.ElevatedButton(
        "Procesar",
        bgcolor=ft.Colors.BLUE_700, # Azul más oscuro para contraste
        color=ft.Colors.WHITE,
        expand=True,
        icon=ft.Icons.LAUNCH,
        icon_color=ft.Colors.WHITE,
        tooltip="Obtener capítulos faltantes"
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
                print(f"Fallo en {name}: {e}")
                continue
        return texto

    def traducir_texto_largo(texto: str, delimitador: str = "\n---PARAGRAPH_DELIMITER---\n") -> str:
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

    # --- Banner con estilo mejorado para tema oscuro ---
    banner = ft.Banner(
        content=ft.Row([]),
        actions=[
            ft.TextButton(text="Cerrar", on_click=close_banner),
        ],
        bgcolor=ft.Colors.GREY_800, # Fondo oscuro para el banner
        surface_tint_color=ft.Colors.DEEP_PURPLE_300 # Tinte del tema primario
    )
    
    progress_ring = ft.ProgressRing(visible=False, stroke_width=5, color=ft.Colors.DEEP_PURPLE_300) # Color del anillo

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

    def manejar_driver_capitulos(driver, novela_id, capitulo_id):
        # --- Cambio aquí: Obtener novela_doc una sola vez ---
        novela_doc = collection_novelas.find_one({'_id': ObjectId(novela_id)})
        if not novela_doc:
            open_banner(
                ft.Colors.RED_900, # Fondo más oscuro para error
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                [
                    ft.Text(
                        value="Error: Novela no encontrada.",
                        color=ft.Colors.WHITE, # Texto blanco
                        size=14
                    ),
                ]
            )
            return # Salir si no se encuentra la novela
        sitio_id = novela_doc.get('sitio_id')
        # FANMTL.com
        if FANMTL_SITIO_ID == sitio_id: # Usar constante
            time.sleep(3)
            soup = bs(driver.page_source, 'html.parser')
            div_contenido = soup.find('div', class_='chapter-content')
            if div_contenido:
                # --- Cambio aquí: Traducir texto completo ---
                # Obtener todos los textos de los párrafos
                textos_originales = [p.getText() for p in div_contenido.find_all('p') if p.getText().strip()]
                if textos_originales: # Solo si hay texto
                    # Unir textos con un delimitador único
                    delimitador = "\n---PARAGRAPH_DELIMITER---\n"
                    texto_a_traducir = delimitador.join(textos_originales)
                    # Traducir el texto completo (manejando límites)
                    texto_traducido_completo = traducir_texto_largo(texto_a_traducir, delimitador)
                    # Dividir el texto traducido de vuelta en párrafos
                    textos_traducidos = texto_traducido_completo.split("--- párrafo_delimiter ---")
                    # Construir el HTML con los textos traducidos
                    # Asegurarse de que haya suficientes textos traducidos
                    texto_capitulo = ''.join([f"<p>{t}</p>" for t in textos_traducidos[:len(textos_originales)]])
                else:
                    texto_capitulo = "<p>(Sin contenido)</p>"
                _id = enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo)
                print(f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}")
                open_banner(
                    ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.GREEN_300, size=40),
                    [
                        ft.Text(
                            value=f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}",
                            color=ft.Colors.WHITE, # Texto blanco
                            size=14
                        ),
                    ]
                )
            else:
                open_banner(
                    ft.Colors.RED_900, # Fondo más oscuro para error
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                    [
                        ft.Text(
                            value="Error: No se encontró el contenido del capítulo en FANMTL.",
                            color=ft.Colors.WHITE, # Texto blanco
                            size=14
                        ),
                    ]
                )
        # tunovelaligera.com
        elif TUNOVELA_LIGERA_SITIO_ID == sitio_id: # Usar elif y constante
            time.sleep(3)
            soup = bs(driver.page_source, 'html.parser')
            div_contenido = soup.find('div', class_='entry-content_wrap')
            if div_contenido:
                # --- Cambio aquí: No se traduce para este sitio según el original ---
                # Obtener todos los textos de los párrafos
                textos_originales = [p.getText() for p in div_contenido.find_all('p') if p.getText().strip()]
                if textos_originales:
                    # Unir textos con un delimitador único (opcional aquí, pero por consistencia)
                    # texto_a_traducir = "\n---PARAGRAPH_DELIMITER---\n".join(textos_originales)
                    # texto_traducido_completo = traducir_texto_largo(texto_a_traducir) # Si se quisiera traducir
                    # textos_traducidos = texto_traducido_completo.split("\n---PARAGRAPH_DELIMITER---\n")
                    # texto_capitulo = ''.join([f"<p>{t}</p>" for t in textos_traducidos[:len(textos_originales)]])
                    texto_capitulo = ''.join([f"<p>{texto}</p>" for texto in textos_originales])
                else:
                    texto_capitulo = "<p>(Sin contenido)</p>"
                _id = enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo)
                print(f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}")
                open_banner(
                    ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.GREEN_300, size=40),
                    [
                        ft.Text(
                            value=f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}",
                            color=ft.Colors.WHITE, # Texto blanco
                            size=14
                        ),
                    ]
                )
            else:
                open_banner(
                    ft.Colors.RED_900, # Fondo más oscuro para error
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                    [
                        ft.Text(
                            value="Error: No se encontró el contenido del capítulo en TunovelaLigera.",
                            color=ft.Colors.WHITE, # Texto blanco
                            size=14
                        ),
                    ]
                )
        else:
            open_banner(
                ft.Colors.AMBER_900, # Fondo más oscuro para advertencia
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_300, size=40),
                [
                    ft.Text(
                        value="Validar sitio para manejar driver no es FANMTL.com o tunovelaligera.com",
                        color=ft.Colors.WHITE, # Texto blanco
                        size=14
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
            nombre_archivo = "imagen_descargada.jpg"
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
            print(f"Imagen descargada en: {ruta_destino}")
            return ruta_destino
        except Exception as e:
            print(f"Error al descargar: {str(e)}")
            return None

    def sanitizar_nombre(nombre):
        """Elimina caracteres no válidos para nombres de archivo"""
        return "".join(c for c in nombre if c.isalnum() or c in (' ', '_', '-')).rstrip()

    def crearepub(novela, capitulos):
        progress_ring.visible = True
        btn_epub.disabled = True
        btn_pdf.disabled = True
        page.update()
        try:
            contenido_capitulos_novela = {
                str(x['capitulo_id']): x['texto'] 
                for x in collection_contenido_capitulos.find(
                    {'novela_id': str(novela['_id'])}
                ).sort('created_at', 1) # Corrección: Usar argumentos separados
            }
            # Descargar portada
            portada = descargar_imagen(novela['imagen_url'])
            if not portada or not os.path.exists(portada):
                raise Exception("Error al obtener la portada")
            with open(portada, 'rb') as img_file:
                base64_cover = base64.b64encode(img_file.read()).decode('utf-8')
            book = epub.EpubBook()
            # Metadatos
            book.set_identifier(str(novela['_id']))
            book.set_title(novela['nombre'])
            book.set_language('es')
            book.add_author(novela['autor'])
            # Añadir portada
            with open(portada, 'rb') as f:
                book.set_cover('cover.jpg', f.read())
            # --- Sección de Introducción Mejorada ---
            # Traducir con respaldo (solo para nombre y sinopsis, como en PDF)
            nombre_traducido = traducir(novela['nombre']) or novela['nombre']
            sinopsis_traducida = traducir(novela['sinopsis']) or novela['sinopsis']
            # Crear contenido HTML para la introducción, incluyendo todos los detalles
            etiquetas = {
                '_id': 'Novela ID',
                'nombre': 'Nombre Novela', # Usamos nombre_traducido
                'sinopsis': 'Sinopsis Novela', # Usamos sinopsis_traducida
                'autor': 'Autor Novela',
                'genero': 'Géneros Novela',
                'status': 'Status Novela',
                'url': 'Url Novela',
                'imagen_url': 'Url Imagen Novela',
                'created_at': 'Fecha Creación en Base de Datos',
                'updated_at': 'Fecha Modificación en Base de Datos',
            }
            intro_html = f"""
            <h1>{nombre_traducido}</h1>
            <img src="image/jpeg;base64,{base64_cover}" 
                style="width: 300px; height: auto; margin: 0 auto; display: block;">
            <h2>Detalles de la Novela</h2>
            <table style="width:100%; border-collapse: collapse;">
            <tr><td style="font-weight:bold;">{etiquetas['_id']}</td><td>{novela.get('_id', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['nombre']}</td><td>{nombre_traducido}</td></tr>
            <tr><td style="font-weight:bold; vertical-align:top;">{etiquetas['sinopsis']}</td><td>{sinopsis_traducida}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['autor']}</td><td>{novela.get('autor', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['genero']}</td><td>{novela.get('genero', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['status']}</td><td>{novela.get('status', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['url']}</td><td><a href="{novela.get('url', '#')}">{novela.get('url', 'N/A')}</a></td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['imagen_url']}</td><td><a href="{novela.get('imagen_url', '#')}">Ver Imagen</a></td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['created_at']}</td><td>{novela.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('created_at'), datetime) else novela.get('created_at', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">{etiquetas['updated_at']}</td><td>{novela.get('updated_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('updated_at'), datetime) else novela.get('updated_at', 'N/A')}</td></tr>
            </table>
            """
            intro = epub.EpubHtml(
                title='Introducción',
                file_name='intro.xhtml',
                lang='es',
            )
            intro.content = intro_html
            book.add_item(intro)
            # --- Fin de la Introducción Mejorada ---
            # Capítulos
            chapters = [intro] # Incluir la intro en el spine y TOC
            zfill_length = len(str(len(capitulos)))
            for idx, capitulo in enumerate(capitulos, 1):
                nombre_capitulo = capitulo['nombre']
                # Obtener contenido con valor por defecto
                contenido = contenido_capitulos_novela.get(str(capitulo['_id']), '')
                chapter = epub.EpubHtml(
                    title=nombre_capitulo,
                    file_name=f'cap_{idx:0{zfill_length}}.xhtml',
                    lang='es',
                )
                chapter.content = f"<h1>{nombre_capitulo}</h1>{contenido}"
                book.add_item(chapter)
                chapters.append(chapter)
                open_banner(
                    ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                    ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_300, size=40),
                    [
                        ft.Text(
                            value=f"{nombre_capitulo} a sido añadido al archivo",
                            color=ft.Colors.WHITE, # Texto blanco
                            size=14
                        ),
                    ]
                )
                page.update()
            # Capítulo de Notas
            notas = epub.EpubHtml(
                title='Notas',
                file_name='notas.xhtml',
                lang='es',
            )
            notas.content = "<h1>Notas</h1><p>Notas adicionales...</p>"
            book.add_item(notas)
            # Estructura del libro
            book.toc = (
                epub.Link('intro.xhtml', 'Introducción', 'intro'),
                (epub.Section('Capítulos'), chapters[1:]),  # Excluir intro duplicada del TOC de capítulos
                (epub.Section('Apéndices'), [notas])
            )
            # Spine correcto (intro + capítulos + notas)
            book.spine = chapters + [notas] # chapters ya incluye intro
            # Añadir componentes estándar
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            # CSS (mejorar compatibilidad)
            style = """
            body { font-family: serif; }
            h1 { font-size: 1.8em; }
            h2 { font-size: 1.4em; }
            table { border: 1px solid #ccc; margin-top: 1em; }
            td { border: 1px solid #ccc; padding: 5px; }
            """
            css = epub.EpubItem(
                uid="style_css",
                file_name="style/style.css",
                content=style
            )
            book.add_item(css)
            # Guardar
            nombre_archivo = sanitizar_nombre(novela['nombre']) + '.epub'
            def save_file_result(e: ft.FilePickerResultEvent):
                try:
                    # Verificar si el usuario canceló
                    if e.path is None:
                        open_banner(
                            ft.Colors.YELLOW_900, # Fondo más oscuro para advertencia
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER_300, size=40),
                            [ft.Text(value="Operación cancelada", color=ft.Colors.WHITE, size=14)] # Texto blanco
                        )
                        return
                    # Guardar el EPUB en la ruta seleccionada
                    epub.write_epub(e.path, book, {})
                    # Mostrar confirmación
                    open_banner(
                        ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_300, size=40),
                        [ft.Text(value=f"EPUB guardado en:\n{e.path}", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                except PermissionError:
                    open_banner(
                        ft.Colors.RED_900, # Fondo más oscuro para error
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                        [ft.Text(value="Error: Permisos denegados para guardar el archivo", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                except Exception as e:
                    open_banner(
                        ft.Colors.RED_900, # Fondo más oscuro para error
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                        [ft.Text(value=f"Error al guardar: {str(e)}", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                finally:
                    # Limpiar archivo temporal
                    if portada and os.path.exists(portada):
                        try:
                            os.remove(portada)
                        except OSError:
                            pass # Ignorar errores al eliminar
            # Dentro de tu función crearepub:
            filepicker.on_result = save_file_result
            filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["epub"])
        except Exception as e:
            open_banner(
                ft.Colors.RED_900, # Fondo más oscuro para error
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                [
                    ft.Text(
                        value=f"Error: {str(e)}",
                        color=ft.Colors.WHITE, # Texto blanco
                        size=14
                    ),
                ]
            )
        finally:
            progress_ring.visible=False
            btn_epub.disabled = False
            btn_pdf.disabled = False
            page.update()

    def crearpdf(novela, capitulos):
        progress_ring.visible = True
        btn_epub.disabled = True
        btn_pdf.disabled = True
        page.update()
        try:
            # Obtener contenido de la base de datos
            contenido_capitulos_novela = {
                str(x['capitulo_id']): x['texto']
                for x in collection_contenido_capitulos.find(
                    {'novela_id': str(novela['_id'])}
                ).sort('created_at', 1) # Corrección: Usar argumentos separados
            }
            # Descargar portada
            portada = descargar_imagen(novela['imagen_url'])
            if not portada or not os.path.exists(portada):
                raise Exception("Error al obtener la portada")
            # Convertir imagen a base64
            with open(portada, 'rb') as img_file:
                base64_cover = base64.b64encode(img_file.read()).decode('utf-8')
            # Traducciones
            nombre_traducido = traducir(novela['nombre']) or novela['nombre']
            sinopsis_traducida = traducir(novela['sinopsis']) or novela['sinopsis']
            pdf = PDF(orientation='P', unit='mm', format='A4')
            pdf.add_font('Poppins-Regular', '', os.path.join(os.getcwd(),'recopilarnovelasdjango','static','fonts', 'Poppins-Regular.ttf'), uni=True)
            pdf.set_font('Poppins-Regular', size=12)
            pdf.set_title(nombre_traducido)
            pdf.set_author(novela['autor'])
            pdf.set_creator('David Eliceo Vite Vergara')
            # Habilitar reemplazo de {{nb}} en el pie de página
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.chapter_title(nombre_traducido)
            pdf.image(name=portada, x=pdf.epw / 3, w=75)
            pdf.write_html(text="<h5>Resumen:</h5>")
            pdf.write_html(text=f"<p>{sinopsis_traducida}</p>")
            pdf.write(text=f"Url de Novela: {novela['url']}")
            # Añadir capítulos
            for idx, capitulo in enumerate(capitulos, 1):
                capitulo_id = str(capitulo['_id'])
                nombre_capitulo = capitulo['nombre']
                contenido = contenido_capitulos_novela.get(capitulo_id, '')
                pdf.print_chapter(f"{nombre_capitulo}", f"{contenido}")
                # Actualizar UI
                open_banner(
                    ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                    ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_300, size=40),
                    [ft.Text(value=f"{nombre_capitulo} añadido al PDF", color=ft.Colors.WHITE, size=14)] # Texto blanco
                )
                page.update()
            # Guardar archivo
            nombre_archivo = sanitizar_nombre(novela['nombre']) + '.pdf'
            def save_file_result(e: ft.FilePickerResultEvent):
                try:
                    if e.path is None:
                        open_banner(
                            ft.Colors.YELLOW_900, # Fondo más oscuro para advertencia
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER_300, size=40),
                            [ft.Text(value="Operación cancelada", color=ft.Colors.WHITE, size=14)] # Texto blanco
                        )
                        return
                    with open(e.path, 'wb') as filepdf:
                        pdf.output(filepdf)
                    open_banner(
                        ft.Colors.GREEN_900, # Fondo más oscuro para éxito
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_300, size=40),
                        [ft.Text(value=f"PDF guardado en:\n{e.path}", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                except PermissionError:
                    open_banner(
                        ft.Colors.RED_900, # Fondo más oscuro para error
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                        [ft.Text(value="Error: Permisos denegados", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                except Exception as ex:
                    open_banner(
                        ft.Colors.RED_900, # Fondo más oscuro para error
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                        [ft.Text(value=f"Error: {str(ex)}", color=ft.Colors.WHITE, size=14)] # Texto blanco
                    )
                finally:
                    # Limpiar archivo temporal
                    if portada and os.path.exists(portada):
                        try:
                            os.remove(portada)
                        except OSError:
                            pass # Ignorar errores al eliminar
            filepicker.on_result = save_file_result
            filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["pdf"])
        except Exception as e:
            open_banner(
                ft.Colors.RED_900, # Fondo más oscuro para error
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                [ft.Text(value=f"Error: {str(e)}", color=ft.Colors.WHITE, size=14)] # Texto blanco
            )
        finally:
            progress_ring.visible = False
            btn_epub.disabled = False
            btn_pdf.disabled = False
            page.update()

    def show_loading():
        AppState.loading = True
        page.splash = ft.ProgressBar(color=ft.Colors.DEEP_PURPLE_300) # Color del indicador de carga
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
            print(f"Error loading home  {e}")
            return []

    def load_sitio_details(sitio_id):
        try:
            sitio = collection_sitios.find_one({'_id': ObjectId(sitio_id)})
            novelas = []
            for novela in collection_novelas.find({'sitio_id': sitio_id}):
                novelas.append(novela)
            return sitio, novelas
        except Exception as e:
            print(f"Error loading sitio details: {e}")
            return None, []

    def load_novela_details(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort
            return collection_novelas.find_one({'_id': ObjectId(novela_id)}), [capitulo for capitulo in collection_capitulos.find({'novela_id': novela_id}).sort('created_at', 1)]
        except Exception as e:
            print(f"Error loading novela details: {e}")
            return None, []

    def load_ids_capitulos_novela(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort y projection correctamente
            return {str(capitulo['_id']) for capitulo in collection_capitulos.find({'novela_id': novela_id}, {'_id': 1}).sort('created_at', 1)}
        except Exception as e:
            print(f"Error loading capitulo novela details: {e}")
            return set() # Devolver un conjunto vacío en caso de error

    def load_ids_urls_capitulos_novela(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort y projection correctamente
            return {str(capitulo['_id']):capitulo['url'] for capitulo in collection_capitulos.find({'novela_id': novela_id}, {'_id': 1, 'url': 1}).sort('created_at', 1)}
        except Exception as e:
            print(f"Error loading ids urls capitulos details: {e}")
            return {} # Devolver un diccionario vacío en caso de error

    def load_ids_contenido_capitulos_novela(novela_id):
        try:
            # Corrección: Usar argumentos separados para sort y projection correctamente
            return [str(contenido['capitulo_id']) for contenido in collection_contenido_capitulos.find({'novela_id': novela_id}, {'capitulo_id': 1, '_id': 0}).sort('created_at', 1)]
        except Exception as e:
            print(f"Error loading ids contenido capitulos novela details: {e}")
            return [] # Devolver una lista vacía en caso de error

    def comparar_diccionarios(dic1, dic2):
        return [x for x in dic1 if x not in dic2]

    def instanciar_driver():
        options = webdriver.ChromeOptions()
        # options = webdriver.FirefoxOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        return uc.Chrome(options=options, service = Service(executable_path=ChromeDriverManager().install()))
        # return webdriver.Firefox(options=options, service=Service(executable_path=f"{os.getcwd()}/geckodriver/geckodriver.exe"))

    def obtener_capitulos_webscrapping(cap_faltantes, novela_id):
        global contar_capitulos
        global lista_capitulos
        global ids_contenido_capitulo # Asegurarse de usar la global
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
                            # Actualizar UI
                            if contar_capitulos < len(lista_capitulos):
                                lista_capitulos[contar_capitulos].leading=ft.Icon(name=ft.Icons.CHECK, col=1, color=ft.Colors.GREEN_300)
                            contar_capitulos +=1
                            txt_number.value = str(contar_capitulos) # Convertir a string
                            ids_contenido_capitulo.append(str(cap)) # Corrección: usar cap en lugar de id
                            page.update()
                            break # Salir del bucle de reintentos si tiene éxito
                        except Exception as error:
                            intento += 1
                            print(f"Intento {intento} fallido para capítulo {cap}: {error}")
                            if intento == max_intentos:
                                open_banner(
                                    ft.Colors.RED_900, # Fondo más oscuro para error
                                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=40),
                                    [
                                        ft.Text(
                                            value=f"Error persistente al obtener capítulo {cap}",
                                            color=ft.Colors.WHITE, # Texto blanco
                                            size=14
                                        ),
                                    ]
                                )
                            time.sleep(2) # Esperar antes de reintentar
        finally:
            driver.quit()
        progress_ring.visible = False
        btn_procesar.disabled = True
        btn_epub.disabled = False
        btn_pdf.disabled = False
        page.update()
        # No es necesario navegar de nuevo, la vista se actualiza por el page.update()
        # navigate_to_novela_detail(novela_id)

    def create_sitio_button(sitio):
        # --- Botón con estilo mejorado para tema oscuro ---
        return ft.ElevatedButton(
            sitio['nombre'],
            on_click=lambda e, id=sitio['_id']: navigate_to_detail(id),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(10, 15, 10, 15) # Añadir padding para mejor toque
            ),
            # Añadir tooltip
            tooltip=f"Ver novelas de {sitio['nombre']}"
        )

    def create_novela_card(novela):
        # --- Tarjeta de novela con estilo mejorado para tema oscuro ---
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Image(
                        src=novela['imagen_url'],
                        fit=ft.ImageFit.COVER, # Mejor ajuste
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        border_radius=ft.border_radius.vertical(top=10), # Solo esquinas superiores
                        height=200, # Altura fija para consistencia
                        width=180, # Ancho fija para consistencia
                    ),
                    ft.Container( # Contenedor para el texto con padding
                        content=ft.Text(novela['nombre'], size=8, weight=ft.FontWeight.W_500, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.WHITE), # Texto blanco
                        padding=ft.Padding(5, 5, 5, 10), # Padding interno
                        expand=True # Para que el texto se expanda y se centre
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER), # Sin espacio entre imagen y texto, centrado
                padding=0, # Sin padding interno en el contenedor principal
                border_radius=ft.border_radius.all(10),
                ink=True, # Efecto de tinta al hacer clic
                on_click=lambda e, id=novela['_id']: navigate_to_novela_detail(id),
            ),
            elevation=3, # Sombra para profundidad
        )

    def create_home_view():
        show_loading()
        sitios = load_home_data()
        return ft.View(
            "/",
            [
                ft.AppBar(title=ft.Text("Sitios de Novelas"), bgcolor=ft.Colors.SURFACE), # Usar color del tema
                # --- GridView con mejor espaciado ---
                ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=180, # Ajustar tamaño máximo de tarjeta
                    spacing=15, # Espaciado horizontal
                    run_spacing=15, # Espaciado vertical
                    controls=[create_sitio_button(sitio) for sitio in sitios]
                )
            ],
            padding=ft.Padding(20, 10, 20, 20) # Padding general de la vista
        )

    def create_detail_view(sitio_id):
        show_loading()
        sitio, novelas = load_sitio_details(sitio_id)
        if not sitio:
            return ft.View(
                f"/sitio/{sitio_id}",
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
        return ft.View(
            f"/sitio/{sitio_id}",
            [
                ft.AppBar(
                    title=ft.Text(sitio['nombre'], size=16),
                    bgcolor=ft.Colors.SURFACE, # Usar color del tema
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda _: page.go("/")
                    )
                ),
                # --- Información del sitio con mejor presentación ---
                ft.Container(
                    content=ft.ResponsiveRow([
                        ft.Column([ft.Text(f"ID: {sitio_id}", size=14, color=ft.Colors.GREY_300)], col=4, horizontal_alignment=ft.CrossAxisAlignment.START),
                        ft.Column([ft.Text(f"URL: {sitio['url']}", size=14, color=ft.Colors.GREY_300)], col=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Text(f"Novelas: {len(novelas)}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)], col=4, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ]),
                    padding=ft.Padding(10, 10, 10, 10), # Padding interno
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), # Borde sutil
                    border_radius=ft.border_radius.all(8), # Bordes redondeados
                    margin=ft.Margin(0, 0, 0, 15) # Margen inferior
                ),
                # --- GridView de novelas con mejor espaciado y relación de aspecto ---
                ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=180,
                    spacing=10,
                    run_spacing=15,
                    child_aspect_ratio=0.65, # Relación de aspecto ajustada para tarjetas
                    controls=[create_novela_card(novela) for novela in novelas]
                )
            ],
            spacing=20,
            padding=ft.Padding(20, 10, 20, 20) # Padding general de la vista
        )

    def create_novel_detail_view(novela_id):
        global contar_capitulos
        global lista_capitulos
        global ids_contenido_capitulo # Asegurarse de usar la global
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
        # --- Lista de capítulos con ListTile para mejor presentación ---
        lista_capitulos=[
            ft.ListTile(
                leading=ft.Icon(
                    name=ft.Icons.CHECK if str(capitulo['_id']) in ids_contenido_capitulo else ft.Icons.PENDING,
                    color=ft.Colors.GREEN_300 if str(capitulo['_id']) in ids_contenido_capitulo else ft.Colors.GREY_500
                ),
                title=ft.Text(capitulo['nombre'], size=13, color=ft.Colors.GREY_300), # Texto más claro
                dense=True, # Hacer el ListTile más compacto
                # Añadir un subtítulo con la fecha si está disponible
                subtitle=ft.Text(f"Fecha: {capitulo.get('created_at', 'N/A').strftime('%Y-%m-%d') if isinstance(capitulo.get('created_at'), datetime) else 'N/A'}", size=11, color=ft.Colors.GREY_600) if capitulo.get('created_at') else None
            )
            for capitulo in capitulos
        ]

        btn_epub.on_click=lambda _: crearepub(novela, capitulos)
        btn_epub.disabled=False if len(capitulos) == contar_capitulos else True
        btn_pdf.on_click=lambda _: crearpdf(novela, capitulos)
        btn_pdf.disabled=False if len(capitulos) == contar_capitulos else True
        cap_faltantes = comparar_diccionarios([str(x['_id']) for x in capitulos], ids_contenido_capitulo)
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
        
        # --- Vista de detalles con mejor organización y estilo ---
        return ft.View(
            f"/novela/{novela_id}",
            [
                ft.AppBar(
                    title=ft.Text(novela['nombre'], size=16),
                    bgcolor=ft.Colors.SURFACE, # Usar color del tema
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda _: navigate_to_detail(novela['sitio_id'])
                    )
                ),
                # --- Sección principal con información de la novela ---
                ft.Container(
                    content=ft.ResponsiveRow([
                        # Columna de la imagen
                        ft.Column(
                            col={"sm": 12, "md": 3}, # Responsive: 12 en móvil, 3 en desktop
                            controls=[
                                ft.Image(
                                    src=novela['imagen_url'],
                                    fit=ft.ImageFit.FIT_WIDTH,
                                    repeat=ft.ImageRepeat.NO_REPEAT,
                                    border_radius=ft.border_radius.all(10),
                                    height=250 # Altura fija para consistencia
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER # Centrar imagen
                        ),
                        # Columna de los detalles
                        ft.Column(
                            col={"sm": 12, "md": 9}, # Responsive: 12 en móvil, 9 en desktop
                            controls=[
                                # Usar DataTable para una presentación más estructurada
                                ft.DataTable(
                                    columns=[
                                        ft.DataColumn(ft.Text("Campo", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)), # Texto blanco
                                        ft.DataColumn(ft.Text("Valor", size=13, color=ft.Colors.GREY_300)), # Texto más claro
                                    ],
                                    rows=[
                                        ft.DataRow(cells=[
                                            ft.DataCell(ft.Text(etiquetas[key], size=12, color=ft.Colors.GREY_300)), # Texto más claro
                                            ft.DataCell(ft.Text(f"{novela[key]}", size=12, selectable=True, color=ft.Colors.WHITE)) # Texto blanco y seleccionable
                                        ])
                                        for key in novela.keys() 
                                        if key not in ['imagen_url','sitio_id','created_at', 'updated_at', '_id'] # Excluir campos no deseados
                                    ],
                                    column_spacing=20, # Espacio entre columnas
                                    heading_row_height=30, # Altura de fila de encabezado
                                    data_row_min_height=30, # Altura mínima de filas de datos
                                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), # Borde sutil
                                    border_radius=ft.border_radius.all(8), # Bordes redondeados
                                    heading_row_color=ft.Colors.SURFACE, # Color de fondo del encabezado
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO # Scroll si el contenido es muy largo
                        ),
                    ]),
                    padding=ft.Padding(10, 10, 10, 10), # Padding interno
                    border_radius=ft.border_radius.all(8), # Bordes redondeados
                    margin=ft.Margin(0, 0, 0, 5) # Margen inferior
                ),
                
                # --- Sección de controles y lista de capítulos ---
                ft.Divider(height=5, thickness=0, color=ft.Colors.OUTLINE_VARIANT), # Divisor visual
                
                ft.ResponsiveRow([
                    # Columna de controles (lado izquierdo)
                    ft.Container(
                        col={"sm": 12, "md": 3}, # Responsive
                        content=ft.Column([
                            ft.Text("Capitulos Recopilados", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE), # Texto blanco
                            ft.Row([
                                txt_number,
                                ft.Text("/", size=16, color=ft.Colors.WHITE), # Texto blanco
                                ft.Text(str(len(capitulos)), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), # Texto blanco
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Divider(height=10, thickness=0), # Espacio pequeño
                            ft.Row([
                                btn_epub,
                            ], expand=True),
                            ft.Row([
                                btn_pdf,
                            ], expand=True),
                            ft.Row([
                                btn_procesar,
                            ], expand=True),
                            ft.Divider(height=15, thickness=2, color=ft.Colors.OUTLINE_VARIANT),
                            # --- Contenedor para el ProgressRing centrado ---
                            ft.Container(
                                content=ft.Row([
                                    progress_ring
                                ], expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                expand=True
                            ),
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER), # Espaciado y alineación
                        padding=ft.Padding(10, 10, 10, 10), # Padding interno
                        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), # Borde sutil
                        border_radius=ft.border_radius.all(8), # Bordes redondeados
                    ),
                    # Columna de lista de capítulos (lado derecho)
                    ft.Container(
                        col={"sm": 12, "md": 9}, # Responsive
                        content=ft.ListView(
                            expand=True,
                            controls=lista_capitulos,
                            adaptive=True,
                            divider_thickness=0.5, # Grosor del divisor entre elementos
                            spacing=2 # Espaciado entre elementos
                        ),
                        padding=ft.Padding(5, 5, 5, 5), # Padding interno
                        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), # Borde sutil
                        border_radius=ft.border_radius.all(8), # Bordes redondeados
                    ),
                ], expand=True),
            ],
            spacing=20,
            padding=ft.Padding(20, 10, 20, 20) # Padding general de la vista
        )

    def route_change(route):
        if AppState.loading:
            return
        page.views.clear()
        if page.route == "/":
            page.views.append(create_home_view())
        else:
            parts = page.route.split("/")
            if len(parts) > 2 and parts[1] == "sitio":
                page.views.append(create_detail_view(parts[2]))
            elif len(parts) > 2 and parts[1] == "novela": # Corrección: usar elif
                page.views.append(create_novel_detail_view(parts[2]))
        hide_loading()
        page.update()

    def navigate_to_detail(sitio_id):
        page.go(f"/sitio/{sitio_id}")

    def navigate_to_novela_detail(novel_id):
        page.go(f"/novela/{novel_id}")

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)