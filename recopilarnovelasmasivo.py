import asyncio
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from google_trans_new import google_translator
from langdetect import detect, DetectorFactory
import translators as ts
from bs4 import BeautifulSoup as bs
from datetime import datetime
import csv
import time
import pandas as pd
from ebooklib import epub
from uuid import uuid4
import httpx
import aiofiles
import os
from tempfile import gettempdir
from urllib.parse import urlparse
from fpdf import FPDF
import logging
import requests
import os
from dotenv import load_dotenv


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NOVELAS_EXCLUIDAS_STR = os.getenv('NOVELAS_EXLUIDAS', '')
NOVELAS_EXLUIDAS = NOVELAS_EXCLUIDAS_STR.split(',') if NOVELAS_EXCLUIDAS_STR else []

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.1.11:27017")
DB_NAME = "recopilarnovelas"
COLLECTION_SITIOS = "app_sitio"
COLLECTION_NOVELAS = "app_novela"
COLLECTION_CAPITULOS = "app_capitulo"
COLLECTION_CONTENIDO_CAPITULOS = 'app_contenidocapitulo'

# Initialize MongoDB client (asynchronous)
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
    'google': 4500,
    'google_new': 4500,
    'bing': 4500,
}

# --- Additional Constants ---
DEFAULT_SLEEP_TIME = 2
PARAGRAPH_DELIMITER = "---PARAGRAPH_DELIMITER---"
TEMP_IMAGE_FILENAME = "imagen_descargada.jpg"
PINGO_FONT_PATH = os.path.join(os.getcwd(), 'recopilarnovelasdjango', 'static', 'fonts', 'Poppins-Regular.ttf')

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")
    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f"{label}", new_x="LMARGIN",
                new_y="NEXT", align="L", fill=True)
        self.ln(4)
    def chapter_body(self, texto):
        self.set_font('Poppins-Regular', size=12)
        self.write_html(texto)
        self.ln()
    def add_section(self, title):
        self.start_section(title)
    def print_chapter(self, title, texto):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(texto)

async def traducir(texto: str) -> str:
    """Traduce texto usando múltiples servicios de traducción"""
    translators = [
        ('google', lambda t: ts.translate_text(t, translator='google', to_language='es')),
        ('google_new', lambda t: google_translator().translate(t, lang_tgt='es')),
        ('bing', lambda t: ts.translate_text(t, translator='bing', to_language='es')),
    ]
    for name, func in translators:
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, texto)
        except Exception as e:
            logger.warning(f"Fallo en {name}: {e}")
            continue
    return texto

async def traducir_texto_largo(texto: str, delimitador: str = PARAGRAPH_DELIMITER) -> str:
    """
    Traduce texto largo dividiéndolo si excede el límite de caracteres del servicio.
    """
    limit = min(CHARACTER_LIMITS.values(), default=4500)

    if len(texto) <= limit:
        return await traducir(texto)
    else:
        partes = texto.split(delimitador)
        partes_traducidas = []
        parte_actual = ""

        for parte in partes:
            parte_con_delimitador = (delimitador if parte_actual else "") + parte
            if len(parte_actual + parte_con_delimitador) > limit and parte_actual:
                partes_traducidas.append(await traducir(parte_actual))
                parte_actual = parte
            else:
                parte_actual += parte_con_delimitador

        if parte_actual:
            partes_traducidas.append(await traducir(parte_actual))

        return "".join(partes_traducidas)

async def enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo):
    novel_data = {
        'novela_id': novela_id,
        'capitulo_id': capitulo_id,
        'texto': texto_capitulo,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    result = collection_contenido_capitulos.insert_one(novel_data)
    return str(result.inserted_id)

async def _extraer_y_guardar_contenido(soup, selector_css, novela_id, capitulo_id, traducir_flag=False, delimitador='--- párrafo_delimiter ---'):
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
                texto_traducido_completo = await traducir_texto_largo(texto_a_traducir, delimitador)
                texto_capitulo = f"<p>{texto_traducido_completo.replace(delimitador, '</p><p>')}</p>"
            else:
                texto_capitulo = ''.join([f"<p>{texto}</p>" for texto in textos_originales])
        else:
            texto_capitulo = "<p>(Sin contenido)</p>"

        _id = await enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo)
        logger.info(f"Creado, contenido con id:{_id} vinculado a la novela: {capitulo_id}")
        return _id
    else:
        logger.error(f"Error: No se encontró el contenido del capítulo con selector {selector_css}.")
        return None

async def manejar_driver_capitulos(driver, novela_id, capitulo_id):
    novela_doc = collection_novelas.find_one({'_id': ObjectId(novela_id)})
    if not novela_doc:
        logger.error("Error: Novela no encontrada.")
        return

    sitio_id = novela_doc.get('sitio_id')

    # FANMTL.com
    if FANMTL_SITIO_ID == sitio_id:
        await asyncio.sleep(DEFAULT_SLEEP_TIME)
        soup = bs(driver.page_source, 'html.parser')
        error = soup.find('p', _class='error')
        if not error:
            _id = await _extraer_y_guardar_contenido(soup, 'chapter-content', novela_id, capitulo_id, traducir_flag=True, delimitador=PARAGRAPH_DELIMITER)
        

    # tunovelaligera.com
    elif TUNOVELA_LIGERA_SITIO_ID == sitio_id:
        await asyncio.sleep(DEFAULT_SLEEP_TIME)
        soup = bs(driver.page_source, 'html.parser')
        _id = await _extraer_y_guardar_contenido(soup, 'entry-content_wrap', novela_id, capitulo_id, traducir_flag=False, delimitador=PARAGRAPH_DELIMITER)

    else:
        logger.warning("Validar sitio para manejar driver no es FANMTL.com o tunovelaligera.com")

async def descargar_imagen(url):
    temp_dir = gettempdir()
    parsed_url = urlparse(url)
    nombre_archivo = os.path.basename(parsed_url.path)
    if not nombre_archivo:
        nombre_archivo = TEMP_IMAGE_FILENAME
    ruta_destino = os.path.join(temp_dir, nombre_archivo)

    try:
        async with httpx.AsyncClient() as client:
            respuesta = await client.get(url, timeout=30)
            respuesta.raise_for_status()

        async with aiofiles.open(ruta_destino, 'wb') as archivo:
            async for chunk in respuesta.aiter_bytes():
                await archivo.write(chunk)

        logger.info(f"Imagen descargada en: {ruta_destino}")
        return ruta_destino
    except httpx.RequestError as e:
        logger.error(f"Error de red al descargar: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al descargar: {str(e)}")
        return None

def sanitizar_nombre(nombre):
    """Elimina caracteres no válidos para nombres de archivo"""
    return "".join(c for c in nombre if c.isalnum() or c in (' ', '_', '-')).rstrip()

async def crearepub(novela, capitulos):
    try:
        nombre_archivo = sanitizar_nombre(novela['nombre']) + '.epub'
        os.makedirs('./epub', exist_ok=True)
        ruta_completa = f"./epub/{nombre_archivo}"

        # --- REMOVIDA LA CONDICIÓN: Se genera siempre ---
        cursor = collection_contenido_capitulos.find({'novela_id': str(novela['_id'])}).sort('created_at', 1)
        contenido_capitulos_novela = {}
        for doc in cursor:
            contenido_capitulos_novela[str(doc['capitulo_id'])] = doc['texto']

        portada = await descargar_imagen(novela['imagen_url'])
        if not portada or not os.path.exists(portada):
            raise Exception("Error al obtener la portada")

        async with aiofiles.open(portada, 'rb') as img_file:
            image_data = await img_file.read()
            base64_cover = base64.b64encode(image_data).decode('utf-8')

        book = epub.EpubBook()
        book.set_identifier(str(novela['_id']))
        book.set_title(novela['nombre'])
        book.set_language('es')
        book.add_author(novela['autor'])

        async with aiofiles.open(portada, 'rb') as f:
            book.set_cover('cover.jpg', await f.read())

        nombre_traducido = await traducir(novela['nombre']) or novela['nombre']
        sinopsis_traducida = await traducir(novela['sinopsis']) or novela['sinopsis']

        intro_html = f"""
        <h1>{nombre_traducido}</h1>
        <img src="image/jpeg;base64,{base64_cover}"
            style="width: 300px; height: auto; margin: 0 auto; display: block;">
        <h2>Detalles de la Novela</h2>
        <table style="width:100%; border-collapse: collapse;">
        <tr><td style="font-weight:bold;">Novela ID</td><td>{novela.get('_id', 'N/A')}</td></tr>
        <tr><td style="font-weight:bold;">Nombre Novela</td><td>{nombre_traducido}</td></tr>
        <tr><td style="font-weight:bold; vertical-align:top;">Sinopsis Novela</td><td>{sinopsis_traducida}</td></tr>
        <tr><td style="font-weight:bold;">Autor Novela</td><td>{novela.get('autor', 'N/A')}</td></tr>
        <tr><td style="font-weight:bold;">Géneros Novela</td><td>{novela.get('genero', 'N/A')}</td></tr>
        <tr><td style="font-weight:bold;">Status Novela</td><td>{novela.get('status', 'N/A')}</td></tr>
        <tr><td style="font-weight:bold;">Url Novela</td><td><a href="{novela.get('url', '#')}">{novela.get('url', 'N/A')}</a></td></tr>
        <tr><td style="font-weight:bold;">Url Imagen Novela</td><td><a href="{novela.get('imagen_url', '#')}">Ver Imagen</a></td></tr>
        <tr><td style="font-weight:bold;">Fecha Creación en Base de Datos</td><td>{novela.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('created_at'), datetime) else novela.get('created_at', 'N/A')}</td></tr>
        <tr><td style="font-weight:bold;">Fecha Modificación en Base de Datos</td><td>{novela.get('updated_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('updated_at'), datetime) else novela.get('updated_at', 'N/A')}</td></tr>
        </table>
        """

        intro = epub.EpubHtml(title='Introducción', file_name='intro.xhtml', lang='es')
        intro.content = intro_html
        book.add_item(intro)

        chapters = [intro]
        zfill_length = len(str(len(capitulos)))
        for idx, capitulo in enumerate(capitulos, 1):
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
            logger.info(f"{nombre_capitulo}")

        notas = epub.EpubHtml(title='Notas', file_name='notas.xhtml', lang='es')
        notas.content = "<h1>Notas</h1><p>Notas adicionales...</p>"
        book.add_item(notas)

        book.toc = (
            epub.Link('intro.xhtml', 'Introducción', 'intro'),
            (epub.Section('Capítulos'), chapters[1:]),
            (epub.Section('Apéndices'), [notas])
        )
        book.spine = chapters + [notas]

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        style = """
        body { font-family: serif; }
        h1 { font-size: 1.8em; }
        h2 { font-size: 1.4em; }
        table { border: 1px solid #ccc; margin-top: 1em; }
        td { border: 1px solid #ccc; padding: 5px; }
        """
        css = epub.EpubItem(uid="style_css", file_name="style/style.css", content=style)
        book.add_item(css)

        # Guardar el EPUB en la ruta seleccionada
        epub.write_epub(ruta_completa, book, {})

        logger.info(f"EPUB guardado en: {ruta_completa}")

        if portada and os.path.exists(portada):
            try:
                os.remove(portada)
                logger.info("Archivo temporal de portada eliminado.")
            except OSError as oe:
                logger.warning(f"No se pudo eliminar el archivo temporal: {oe}")
    except Exception as e:
        logger.error(f"Error en crearepub: {str(e)}")

async def crearpdf(novela, capitulos):
    try:
        nombre_archivo = sanitizar_nombre(novela['nombre']) + '.pdf'
        os.makedirs('./pdf', exist_ok=True)
        ruta_completa = f"./pdf/{nombre_archivo}"

        # --- REMOVIDA LA CONDICIÓN: Se genera siempre ---
        cursor = collection_contenido_capitulos.find({'novela_id': str(novela['_id'])}).sort('created_at', 1)
        contenido_capitulos_novela = {}
        for doc in cursor:
            contenido_capitulos_novela[str(doc['capitulo_id'])] = doc['texto']

        portada = await descargar_imagen(novela['imagen_url'])
        if not portada or not os.path.exists(portada):
            raise Exception("Error al obtener la portada")

        with open(portada, 'rb') as img_file:
            base64_cover = base64.b64encode(img_file.read()).decode('utf-8')

        nombre_traducido = await traducir(novela['nombre']) or novela['nombre']
        sinopsis_traducida = await traducir(novela['sinopsis']) or novela['sinopsis']

        pdf = PDF(orientation='P', unit='mm', format='A4')
        pdf.add_font('Poppins-Regular', '', PINGO_FONT_PATH, uni=True)
        pdf.set_font('Poppins-Regular', size=12)
        pdf.set_title(nombre_traducido)
        pdf.set_author(novela['autor'])
        pdf.set_creator('David Eliceo Vite Vergara')
        pdf.alias_nb_pages()

        pdf.add_page()
        pdf.chapter_title(nombre_traducido)
        pdf.image(name=portada, x=pdf.epw / 3, w=75)
        pdf.write_html(text="<h5>Resumen:</h5>")
        pdf.write_html(text=f"<p>{sinopsis_traducida}</p>")
        pdf.write(text=f"Url de Novela: {novela['url']}")

        for idx, capitulo in enumerate(capitulos, 1):
            capitulo_id = str(capitulo['_id'])
            nombre_capitulo = capitulo['nombre']
            contenido = contenido_capitulos_novela.get(capitulo_id, '')

            pdf.print_chapter(f"{nombre_capitulo}", f"{contenido}")
            logger.info(f"{nombre_capitulo}")

        try:
            with open(ruta_completa, 'wb') as filepdf:
                pdf.output(filepdf)

            logger.info(f"PDF guardado en: {ruta_completa}")
        except PermissionError as pe:
            logger.error(f"Error de permisos al guardar PDF: {pe}")
        except Exception as ex:
            logger.error(f"Error al guardar PDF: {str(ex)}")
        finally:
            if portada and os.path.exists(portada):
                try:
                    os.remove(portada)
                    logger.info("Archivo temporal de portada eliminado.")
                except OSError as oe:
                    logger.warning(f"No se pudo eliminar el archivo temporal: {oe}")
    except Exception as e:
        logger.error(f"Error en crearpdf: {str(e)}")

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
    try:
        # Corrección: Usar argumentos separados para sort y projection correctamente
        return [str(contenido['capitulo_id']) for contenido in collection_contenido_capitulos.find({'novela_id': novela_id}, {'capitulo_id': 1, '_id': 0}).sort('created_at', 1)]
    except Exception as e:
        logger.error(f"Error loading ids contenido capitulos novela details: {e}")
        return [] # Devolver una lista vacía en caso de error

def comparar_diccionarios(dic1, dic2):
    return [x for x in dic1 if x not in dic2]

def instanciar_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    return webdriver.Firefox(options=options, service=Service(executable_path=f"{os.getcwd()}/geckodriver/geckodriver.exe"))

async def obtener_capitulos_webscrapping(cap_faltantes, novela_id):
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
                        await manejar_driver_capitulos(driver, novela_id, str(cap))
                        break # Salir del bucle de reintentos si tiene éxito
                    except  requests.exceptions.RequestException as re:
                        intento += 1
                        logger.warning(f"Intento {intento} fallido para capítulo {cap} (Error de red): {re}")
                        if intento == max_intentos:
                            logger.error(f"Error persistente de red al obtener capítulo {cap}")
                        time.sleep(2) # Esperar antes de reintentar
                    except Exception as error:
                        intento += 1
                        logger.error(f"Intento {intento} fallido para capítulo {cap} (Error desconocido): {error}")
                        if intento == max_intentos:
                            logger.error(f"Error persistente al obtener capítulo {cap}")
                        time.sleep(2) # Esperar antes de reintentar
    finally:
        driver.quit()
        logger.info("WebDriver cerrado.")

async def procesar_novelas_sitio(sitio_id_obj):
    sitio_id = str(sitio_id_obj)

    if sitio_id != FANMTL_SITIO_ID:
        logger.info(f"Sitio {sitio_id} no coincide con FANMTL_SITIO_ID. Saltando.")
        return

    logger.info(f"Iniciando procesamiento para sitio_id: {sitio_id}")

    total_novelas = collection_novelas.count_documents({'sitio_id': sitio_id})
    logger.info(f"Total novelas encontradas para procesar: {total_novelas}")

    cursor = collection_novelas.find({'sitio_id': sitio_id}, {'_id': 1, 'nombre': 1}).sort('_id', 1)
    novelas_list = []
    for novela in cursor:
        novelas_list.append({'_id': novela['_id'], 'nombre': novela['nombre']})

    for novela_doc in novelas_list:
        novela_id = str(novela_doc['_id'])
        nombre_novela = novela_doc['nombre']
        logger.info(f"Procesando novela: {novela_id} - {nombre_novela}")

        if novela_id not in NOVELAS_EXLUIDAS:
            try:
                novela_completa, capitulos_lista = load_novela_details(novela_id)
                if not novela_completa:
                    logger.error(f"No se encontró la novela completa para ID {novela_id}. Saltando.")
                    continue

                capitulos_dictionary = load_ids_urls_capitulos_novela(novela_id)
                contenido_capitulos_ids = load_ids_contenido_capitulos_novela(novela_id)

                if not capitulos_dictionary:
                    logger.warning(f"No se encontraron capítulos para la novela {novela_id}. Saltando.")
                    continue

                capitulos_faltantes_ids = comparar_diccionarios(
                    list(capitulos_dictionary.keys()),
                    contenido_capitulos_ids
                )

                if capitulos_faltantes_ids:
                    logger.info(f"Encontrados {len(capitulos_faltantes_ids)} capítulos faltantes para '{nombre_novela}'.")
                    await obtener_capitulos_webscrapping(capitulos_faltantes_ids, novela_id)
                    logger.info(f"Iniciando generación de archivos para '{nombre_novela}'.")
                    await crearepub(novela_completa, capitulos_lista)
                    await crearpdf(novela_completa, capitulos_lista)
                    logger.info(f"Generación de archivos completada para '{nombre_novela}'.")
                else:
                    logger.info(f"No hay capítulos faltantes para '{nombre_novela}'.")
                
                

            except Exception as e:
                logger.error(f"Error procesando novela {novela_id} ('{nombre_novela}'): {e}")
                continue

    logger.info(f"Finalizado procesamiento para sitio_id: {sitio_id}")

async def main():
    for sitio in collection_sitios.find():
        sitio_id = sitio.get('_id')
        if sitio_id:
            await procesar_novelas_sitio(sitio_id)
        else:
            logger.warning("Documento de sitio encontrado sin '_id'. Saltando.")

if __name__ == "__main__":
    asyncio.run(main())