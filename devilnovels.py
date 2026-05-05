import flet as ft
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
from bson.objectid import ObjectId
import pandas as pd
import os
import re
import json
import logging
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración inicial
MONGO_URI = 'mongodb://192.168.1.11:27017/'
DB_NAME = 'recopilarnovelas'
SITIO_ID = '699910bb09d676d0eee6c8e3'

# Leer la variable de entorno INDICE_CONTINUACION
INDICE_CONTINUACION = int(os.getenv('INDICE_CONTINUACION', 0))

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"Índice de continuación leído desde .env: {INDICE_CONTINUACION}")

# Cliente MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coleccion_app_novela = db['app_novela']
coleccion_app_capitulo = db['app_capitulo']

# Colores para la UI
COLOR_ERROR = ft.Colors.RED_600

# URLs / slugs a excluir de la lista de novelas
SLUGS_EXCLUIDOS = {
    'wp-admin', 'wp-login', 'wp-content', 'feed', 'tag',
    'category', 'author', 'page', 'search', 'cart', 'checkout',
    'mi-cuenta', 'contacto', 'politica-de-privacidad', 'dmca',
    'copyright-policy', 'listado-de-novelas', 'privacidad',
    'registro', 'login', 'wp-json', 'xmlrpc', 'favicon',
}


def obtener_novelas_existentes() -> Dict[str, str]:
    """Obtiene un diccionario de novelas existentes {url: id}"""
    return {
        novela['url']: str(novela['_id'])
        for novela in coleccion_app_novela.find(
            {'sitio_id': SITIO_ID},
            {'url': 1}
        )
    }


def obtener_novelas_url_existentes():
    """Obtiene un set de URLs de novelas existentes"""
    return set([
        novela['url']
        for novela in coleccion_app_novela.find(
            {'sitio_id': SITIO_ID},
            {'url': 1}
        )
    ])


def obtener_capitulos_existentes(novel_id: str) -> set:
    """Obtiene conjunto de URLs de capítulos existentes"""
    return {
        str(cap['url']).strip()
        for cap in coleccion_app_capitulo.find(
            {'novela_id': novel_id},
            {'url': 1}
        )
    }


def obtener_datos_novela(driver, url_novela):
    """
    Obtiene los datos de una novela individual de devilnovels.com.
    La estructura del sitio es WordPress + tema personalizado hello-biz con
    plantilla 'plantillapaginanovela'. Los datos están en:
    - Título: h1.nv-title
    - Imagen: .nv-cover img
    - Sinopsis: #nvt-sinopsis .nv-synopsis
    - Stats: span.nv-stat-pill
    """
    logger.info(f"Obteniendo datos de la novela: {url_novela}")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    datos_novela = {
        'titulo': 'N/A',
        'autor': 'N/A',
        'estado': 'N/A',
        'descripcion': 'N/A',
        'generos': [],
        'imagen_url': 'N/A',
        'url': url_novela
    }

    try:
        # --- Título ---
        # Extraer del h1.nv-title (nueva estructura)
        try:
            title_el = soup.select_one('h1.nv-title')
            if title_el:
                datos_novela['titulo'] = title_el.get_text(strip=True)
            else:
                # Fallback: tag <title>
                title_tag = soup.find('title')
                if title_tag:
                    titulo = title_tag.text.strip()
                    titulo = re.sub(r'\s*[-–]\s*$', '', titulo).strip()
                    datos_novela['titulo'] = titulo
        except Exception:
            logger.warning("No se pudo extraer el título.")

        # --- Imagen ---
        # Buscar en .nv-cover img (nueva estructura)
        try:
            img_element = soup.select_one('.nv-cover img')
            if img_element:
                src = img_element.get('data-src') or img_element.get('src', '')
                # Obtener la imagen en tamaño completo (eliminar sufijo -NNNxNNN)
                src_full = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)
                datos_novela['imagen_url'] = src_full
            else:
                # Fallback: buscar img con clase wp-post-image
                img_element = soup.select_one('img.wp-post-image')
                if img_element:
                    src = img_element.get('data-src') or img_element.get('src', '')
                    src_full = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)
                    datos_novela['imagen_url'] = src_full
        except Exception:
            logger.warning("Imagen de portada no encontrada.")

        # --- Descripción ---
        # Buscar en #nvt-sinopsis .nv-synopsis (nueva estructura)
        try:
            synopsis_el = soup.select_one('#nvt-sinopsis .nv-synopsis')
            if synopsis_el:
                # Obtener solo los párrafos de texto, ignorar estilos y headings
                paragraphs = synopsis_el.find_all('p')
                descripcion_parts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # Saltar párrafos vacíos, nbsp, o que sean solo el título
                    if text and text != '\xa0' and text != datos_novela['titulo']:
                        descripcion_parts.append(text)
                descripcion = ' '.join(descripcion_parts)
                datos_novela['descripcion'] = descripcion if descripcion else 'N/A'
            else:
                datos_novela['descripcion'] = 'N/A'
        except Exception:
            logger.info("Descripción no encontrada.")

        # --- Géneros ---
        # Buscar enlaces de categoría en la página
        try:
            category_links = soup.select('a[rel="category tag"]')
            if category_links:
                datos_novela['generos'] = [a.text.strip() for a in category_links if a.text.strip()]
        except Exception:
            logger.info("Géneros no encontrados.")

        # --- Autor ---
        # Intentar buscar en la sinopsis o en el contenido de la página (Autor: xxx)
        try:
            search_areas = []
            synopsis_el = soup.select_one('#nvt-sinopsis .nv-synopsis')
            if synopsis_el:
                search_areas.append(synopsis_el.get_text())
            # También buscar en todo el texto de la página
            search_areas.append(soup.get_text())
            for text in search_areas:
                match = re.search(r'(?:Autor|Author|Escritor|Writer)\s*[:\-]\s*(.+?)(?:\n|<|$)', text, re.IGNORECASE)
                if match:
                    datos_novela['autor'] = match.group(1).strip()
                    break
        except Exception:
            logger.info("Autor no encontrado.")

        # --- Estado ---
        # Intentar determinar el estado desde el texto de la página
        try:
            page_text = soup.get_text()
            if re.search(r'\b(en\s+emisi[oó]n|ongoing|activ[ao]|en\s+curso)\b', page_text, re.IGNORECASE):
                datos_novela['estado'] = 'Ongoing'
            elif re.search(r'\b(completad[ao]|completed|finalizada?|terminad[ao])\b', page_text, re.IGNORECASE):
                datos_novela['estado'] = 'Completed'
        except Exception:
            logger.info("Estado no encontrado.")

    except Exception as e:
        logger.error(f"Error al obtener datos de la novela {url_novela}: {e}")

    return datos_novela


def procesar_capitulos(driver, url_novela):
    """
    Procesa la lista de capítulos de una novela de devilnovels.com.
    Los capítulos se cargan vía AJAX usando la acción 'dv_load_chapters'.
    
    Variables JavaScript en la página:
    - CAT_ID: ID de categoría de la novela
    - TOTAL_CH: Total de capítulos
    - PER_PAGE: Capítulos por página (normalmente 100)
    
    AJAX endpoint: POST admin-ajax.php con action=dv_load_chapters&cat_id=X&page=N&search=
    Respuesta: {success: true, data: {chapters: [{id, title, link}, ...], total, pages}}
    """
    logger.info(f"Procesando capítulos de la novela: {url_novela}")
    capitulos = []
    urls_vistas = set()

    try:
        # Extraer CAT_ID y AJAX URL desde las variables JavaScript de la página
        page_source = driver.page_source
        cat_id_match = re.search(r'var\s+CAT_ID\s*=\s*(\d+)', page_source)
        
        if not cat_id_match:
            logger.error(f"No se pudo encontrar CAT_ID en la página: {url_novela}")
            return capitulos
        
        cat_id = cat_id_match.group(1)
        
        # Extraer AJAX URL
        ajax_url_match = re.search(r"var\s+AJ\s*=\s*['\"](.+?)['\"]", page_source)
        ajax_url = ajax_url_match.group(1) if ajax_url_match else 'https://devilnovels.com/wp-admin/admin-ajax.php'
        
        logger.info(f"CAT_ID: {cat_id}, AJAX URL: {ajax_url}")

        # Hacer la primera petición AJAX para obtener el total de páginas
        ajax_script = """
        var callback = arguments[arguments.length - 1];
        var params = new URLSearchParams({
            action: 'dv_load_chapters',
            cat_id: arguments[0],
            page: arguments[1],
            search: ''
        });
        fetch(arguments[2], {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: params.toString()
        }).then(function(r){ return r.json(); })
        .then(function(d){ callback(d); })
        .catch(function(e){ callback({success: false, error: e.message}); });
        """

        # Aumentar timeout para scripts asíncronos (60 segundos)
        driver.set_script_timeout(60)

        # Primera petición para obtener info de paginación
        data = driver.execute_async_script(ajax_script, cat_id, '1', ajax_url)
        
        if not data or not data.get('success'):
            logger.error(f"Error en la respuesta AJAX para la primera página: {data}")
            return capitulos
        
        total_pages = data['data'].get('pages', 1)
        total_ch = data['data'].get('total', 0)
        logger.info(f"Total de páginas de capítulos: {total_pages}, Total capítulos: {total_ch}")

        # Procesar la primera página
        for ch in data['data'].get('chapters', []):
            titulo = ch.get('title', '').strip()
            url = ch.get('link', '').strip()
            if titulo and url and url not in urls_vistas:
                urls_vistas.add(url)
                capitulos.append({
                    'titulo': titulo,
                    'url': url
                })
        
        logger.info(f"Página 1/{total_pages}: capítulos acumulados = {len(capitulos)}")

        # Procesar páginas restantes
        max_retries = 3
        for page_num in range(2, total_pages + 1):
            page_ok = False
            for attempt in range(1, max_retries + 1):
                try:
                    data = driver.execute_async_script(ajax_script, cat_id, str(page_num), ajax_url)
                    
                    if not data or not data.get('success'):
                        logger.warning(f"Respuesta AJAX inválida para la página {page_num} (intento {attempt}/{max_retries}).")
                        time.sleep(1 * attempt)
                        continue
                    
                    for ch in data['data'].get('chapters', []):
                        titulo = ch.get('title', '').strip()
                        url = ch.get('link', '').strip()
                        if titulo and url and url not in urls_vistas:
                            urls_vistas.add(url)
                            capitulos.append({
                                'titulo': titulo,
                                'url': url
                            })
                    
                    logger.info(f"Página {page_num}/{total_pages}: capítulos acumulados = {len(capitulos)}")
                    page_ok = True
                    break
                    
                except Exception as e:
                    logger.warning(f"Error al obtener la página {page_num} (intento {attempt}/{max_retries}): {e}")
                    time.sleep(1 * attempt)
            
            if not page_ok:
                logger.error(f"No se pudo obtener la página {page_num} después de {max_retries} intentos.")
            
            # Pequeña pausa entre peticiones AJAX
            time.sleep(0.5)

    except TimeoutException:
        logger.error(f"Tiempo de espera agotado al cargar los capítulos de: {url_novela}")
    except Exception as e:
        logger.error(f"Error al procesar capítulos de {url_novela}: {e}")

    logger.info(f"Total de capítulos encontrados: {len(capitulos)}")
    return capitulos


# --- Clase para el scraping automático de DevilNovels ---
class DevilnovelsScraperAutomatico:
    def __init__(self, driver, page_pubsub, existing_novels):
        """
        Inicializa el scraper automático de DevilNovels.

        Args:
            driver: Instancia del WebDriver de Selenium.
            page_pubsub: Objeto pubsub de Flet para enviar mensajes a la UI.
            existing_novels (dict): Diccionario de novelas existentes en la BD.
        """
        self.driver = driver
        self.page_pubsub = page_pubsub
        self.existing_novels = existing_novels
        self.base_url = "https://devilnovels.com"
        self.list_url = f"{self.base_url}/listado-de-novelas/"
        # Lista de géneros a excluir
        self.generos_excluidos = {'LGBT', 'Shoujo Ai', 'Shounen Ai', 'Yaoi', 'Yuri', 'BL', 'BG', 'GL'}

    def scrape_novels_from_listing(self):
        """
        Recopila las URLs de todas las novelas desde la página de listado.
        En devilnovels.com, la página 'listado-de-novelas' usa un shortcode con
        cards en .pvc-featured-pages-grid > .pvc-featured-page-item.
        Cada card tiene un enlace <a> con la URL de la novela.
        """
        novel_urls = []
        try:
            logger.info(f"Cargando página de listado: {self.list_url}")
            self.driver.get(self.list_url)
            time.sleep(3)

            # Esperar a que se cargue la grilla de novelas
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pvc-featured-pages-grid"))
            )

            # Scroll hacia abajo para cargar imágenes lazy-load
            driver_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_step = 500
            current_position = 0
            while current_position < driver_height:
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.3)
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Buscar todas las cards de novelas en la grilla
            novel_cards = soup.select('.pvc-featured-page-item')

            seen_urls = set()
            for card in novel_cards:
                # Cada card tiene uno o más enlaces, tomar el primero (imagen o título)
                link = card.select_one('a[href]')
                if not link:
                    continue

                href = link.get('href', '').strip().rstrip('/')
                if not href or href in seen_urls:
                    continue

                # Verificar que es una URL de devilnovels.com
                if 'devilnovels.com' not in href:
                    continue

                # Parsear para verificar la estructura
                parsed = urlparse(href + '/')
                path = parsed.path.strip('/')
                segments = [s for s in path.split('/') if s]
                if len(segments) != 1:
                    continue

                slug = segments[0]
                if slug in SLUGS_EXCLUIDOS or '.' in slug:
                    continue

                url_normalizada = f"https://devilnovels.com/{slug}/"
                seen_urls.add(href)
                novel_urls.append(url_normalizada)

            # Eliminar duplicados manteniendo orden
            novel_urls = list(dict.fromkeys(novel_urls))
            logger.info(f"Se encontraron {len(novel_urls)} URLs de novelas en la página de listado.")

        except TimeoutException:
            logger.error("Tiempo de espera agotado al cargar la página de listado de novelas.")
        except Exception as e:
            logger.error(f"Error al recopilar URLs de novelas: {e}")

        return novel_urls

    def scrape_all_novels_automatic(self):
        """
        Orquesta el proceso completo de scraping automático.
        """
        self.page_pubsub.send_all({
            "status": "Iniciando scraping automático de todas las novelas de DevilNovels...",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })

        # 1. Intentar cargar URLs desde CSV cache
        try:
            all_novel_urls = pd.read_csv('all_novel_devilnovels_urls.csv')['url'].tolist()
            logger.info(f"URLs cargadas desde cache CSV: {len(all_novel_urls)}")
            self.page_pubsub.send_all({
                "status": f"URLs cargadas desde cache: {len(all_novel_urls)} novelas.",
                "color": ft.Colors.BLUE_600,
                "progress": True
            })
        except Exception:
            all_novel_urls = []

        urls_novelas = obtener_novelas_url_existentes()

        if not all_novel_urls:
            # 2. Recopilar URLs desde la página de listado
            self.page_pubsub.send_all({
                "status": "Recopilando URLs de novelas desde la página de listado...",
                "color": ft.Colors.BLUE_600,
                "progress": True
            })
            all_novel_urls = self.scrape_novels_from_listing()

        # Guardar URLs en CSV
        if all_novel_urls:
            pd.DataFrame(all_novel_urls, columns=['url']).to_csv('all_novel_devilnovels_urls.csv', index=False)

        logger.info(f"Recopilación de URLs completada. Total de novelas encontradas: {len(all_novel_urls)}")
        self.page_pubsub.send_all({
            "status": f"Recopilación completada. Total: {len(all_novel_urls)} novelas. Iniciando procesamiento detallado...",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })

        # 3. Procesar cada novela individualmente
        total_novels = len(all_novel_urls)
        processed_count = 0

        # --- Procesar desde el índice de continuación ---
        logger.info(f"Comenzando procesamiento desde el índice {INDICE_CONTINUACION}")
        novelas_a_procesar = all_novel_urls[INDICE_CONTINUACION:]
        logger.info(f"Total de novelas a procesar a partir del índice {INDICE_CONTINUACION}: {len(novelas_a_procesar)}")

        start_global_index = INDICE_CONTINUACION

        for i, novel_url in enumerate(novelas_a_procesar):
            current_global_index = start_global_index + i
            processed_count = current_global_index + 1

            # if novel_url in urls_novelas:
            if novel_url  :
                logger.info(f"({processed_count}/{total_novels}) Procesando novela individual (índice global {current_global_index}): {novel_url}")
                self.page_pubsub.send_all({
                    "status": f"({processed_count}/{total_novels}) Procesando novela (índice {current_global_index}): {novel_url}",
                    "color": ft.Colors.BLUE_600,
                    "progress": True
                })

                self.driver.get(novel_url)
                time.sleep(3)  # Pausa mayor para WordPress/Elementor

                try:
                    # --- Obtener datos de la novela ---
                    datos_detalle = obtener_datos_novela(self.driver, novel_url)
                    generos_novela = set(datos_detalle['generos'])

                    if self.generos_excluidos.isdisjoint(generos_novela):
                        datos_capitulos = procesar_capitulos(self.driver, novel_url)

                        # --- Lógica de envío de datos a MongoDB ---
                        novel_name = datos_detalle['titulo'].upper()

                        if novel_url in self.existing_novels:
                            novel_id = self.existing_novels[novel_url]
                            urls_novelas.add(novel_url)
                            logger.info(f"Novela '{novel_name}' ya existe en la base de datos (ID: {novel_id}).")
                            self.page_pubsub.send_all({
                                "status": f"Novela '{novel_name[:50]}...' ya existe. Verificando capítulos...",
                                "color": ft.Colors.ORANGE_600,
                                "progress": True
                            })
                        else:
                            # Preparar documento para MongoDB
                            novel_document = {
                                "sitio_id": SITIO_ID,
                                "nombre": novel_name,
                                "sinopsis": datos_detalle.get('descripcion', 'N/A'),
                                "autor": datos_detalle.get('autor', 'N/A'),
                                "genero": ', '.join(datos_detalle.get('generos', [])),
                                "status": 'emision' if 'Ongoing' in datos_detalle.get('estado', '') else 'completo',
                                "url": datos_detalle.get('url', novel_url),
                                "imagen_url": datos_detalle.get('imagen_url', 'N/A'),
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }

                            result = coleccion_app_novela.insert_one(novel_document)
                            novel_id = str(result.inserted_id)
                            self.existing_novels[novel_url] = novel_id
                            logger.info(f"Nueva novela '{novel_name}' registrada en la base de datos (ID: {novel_id}).")
                            self.page_pubsub.send_all({
                                "status": f"Nueva novela '{novel_name[:50]}...' registrada. Procesando capítulos...",
                                "color": ft.Colors.GREEN_600,
                                "progress": True
                            })

                        # Procesar y guardar capítulos
                        existing_chapters_set = obtener_capitulos_existentes(novel_id)
                        chapters_to_insert = []

                        for idx, cap_info in enumerate(datos_capitulos):
                            nombre_capitulo = cap_info.get('titulo', '').strip()
                            url_capitulo = cap_info.get('url', '').strip()
                            if url_capitulo and url_capitulo not in existing_chapters_set:
                                chapters_to_insert.append({
                                    "novela_id": novel_id,
                                    "nombre": nombre_capitulo,
                                    "url": url_capitulo,
                                    "created_at": datetime.now() + timedelta(microseconds=idx),
                                    "updated_at": datetime.now() + timedelta(microseconds=idx)
                                })

                        if chapters_to_insert:
                            coleccion_app_capitulo.insert_many(chapters_to_insert)
                            logger.info(f"Insertados {len(chapters_to_insert)} nuevos capítulos para la novela ID {novel_id}.")
                            self.page_pubsub.send_all({
                                "status": f"Insertados {len(chapters_to_insert)} nuevos capítulos para '{novel_name[:30]}...'.",
                                "color": ft.Colors.GREEN_600,
                                "progress": True
                            })
                        else:
                            logger.info(f"No se encontraron nuevos capítulos para la novela ID {novel_id}.")
                            self.page_pubsub.send_all({
                                "status": f"No se encontraron nuevos capítulos para '{novel_name[:30]}...'.",
                                "color": ft.Colors.BLUE_600,
                                "progress": True
                            })
                    else:
                        logger.info(f"La novela '{datos_detalle['titulo']}' contiene un género excluido y será ignorada.")
                        print(f"La novela contiene uno de los siguientes géneros excluidos y será ignorada: {', '.join(self.generos_excluidos)}")

                    # Pequeña pausa para no sobrecargar el servidor
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error al procesar la novela {novel_url}: {e}")
                    self.page_pubsub.send_all({
                        "status": f"Error al procesar novela: {str(e)[:100]}",
                        "color": COLOR_ERROR,
                        "progress": True
                    })
                    # Continuar con la siguiente novela
            else:
                logger.info(f"({processed_count}/{total_novels}) Saltando novela ya existente: {novel_url}")
                self.page_pubsub.send_all({
                    "status": f"({processed_count}/{total_novels}) Saltando novela ya existente.",
                    "color": COLOR_ERROR,
                    "progress": True
                })

        logger.info("Proceso de scraping automático completado.")
        self.page_pubsub.send_all({
            "status": "Proceso de scraping automático completado exitosamente!",
            "color": ft.Colors.GREEN_600,
            "progress": False
        })


# --- Función principal de Flet ---
def main(page: ft.Page):
    page.title = "DevilNovels Scraper Automático"
    page.window_width = 600
    page.window_height = 400
    page.scroll = ft.ScrollMode.AUTO

    # Elementos de la UI
    url_input = ft.TextField(
        label="URL de la novela (opcional para scraping automático)",
        width=500,
        disabled=False
    )

    status_text = ft.Text("", color=ft.Colors.BLUE_600)
    progress_ring = ft.ProgressRing(visible=False)

    # Variable para almacenar la instancia del driver
    driver_instance = [None]

    def start_scraping(e):
        """Inicia el proceso de scraping automático en un hilo separado."""
        def run_scraping():
            try:
                # Obtener novelas existentes antes de comenzar
                existing_novels = obtener_novelas_existentes()
                logger.info(f"Se encontraron {len(existing_novels)} novelas existentes en la base de datos.")

                # Configurar el driver
                geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', 'geckodriver.exe')
                options = webdriver.FirefoxOptions()
                options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
                # options.add_argument('--headless') # Descomentar para modo headless

                driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                driver_instance[0] = driver

                # Crear instancia del scraper automático
                scraper = DevilnovelsScraperAutomatico(driver, page.pubsub, existing_novels)

                # Ejecutar el scraping automático
                scraper.scrape_all_novels_automatic()

            except Exception as e:
                logger.error(f"Error en el proceso principal de scraping: {e}")
                page.pubsub.send_all({
                    "status": f"Error en el proceso principal: {str(e)}",
                    "color": COLOR_ERROR,
                    "progress": False
                })
            finally:
                # Cerrar el driver si fue creado
                if driver_instance[0]:
                    try:
                        driver_instance[0].quit()
                        logger.info("Navegador cerrado.")
                    except Exception as close_error:
                        logger.error(f"Error al cerrar el navegador: {close_error}")

        # Iniciar el scraping en un hilo para no bloquear la UI
        scraping_thread = threading.Thread(target=run_scraping, daemon=True)
        scraping_thread.start()

    def on_pubsub_message(msg):
        """Maneja los mensajes recibidos del pubsub."""
        if isinstance(msg, dict):
            status_text.value = msg.get("status", "")
            status_text.color = msg.get("color", ft.Colors.BLUE_600)
            progress_ring.visible = msg.get("progress", False)
            page.update()

    # Suscribirse a mensajes del pubsub
    page.pubsub.subscribe(on_pubsub_message)

    # Botón para iniciar el scraping automático
    start_button = ft.ElevatedButton("Iniciar Scraping Automático", on_click=start_scraping)

    # Agregar elementos a la página
    page.add(
        ft.Column(
            [
                ft.Text("DevilNovels Scraper Automático", size=20, weight=ft.FontWeight.BOLD),
                url_input,
                start_button,
                ft.Row([progress_ring, status_text]),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


# Para ejecutar la aplicación Flet
if __name__ == "__main__":
    ft.app(target=main)
