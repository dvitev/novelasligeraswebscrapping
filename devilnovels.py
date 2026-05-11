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

load_dotenv()

MONGO_URI = 'mongodb://192.168.1.11:27017/'
DB_NAME = 'recopilarnovelas'
SITIO_ID = '699910bb09d676d0eee6c8e3'
INDICE_CONTINUACION = int(os.getenv('INDICE_CONTINUACION', 0))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("INICIALIZANDO DEVILNOVELS SCRAPER")
logger.info("=" * 60)
logger.info(f"MONGO_URI: {MONGO_URI}")
logger.info(f"DB_NAME: {DB_NAME}")
logger.info(f"SITIO_ID: {SITIO_ID}")
logger.info(f"INDICE_CONTINUACION: {INDICE_CONTINUACION}")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coleccion_app_novela = db['app_novela']
coleccion_app_capitulo = db['app_capitulo']

# Verificar conexión
try:
    client.admin.command('ping')
    logger.info("✅ Conexión a MongoDB exitosa")
except Exception as e:
    logger.error(f"❌ Error conectando a MongoDB: {e}")
    raise

SLUGS_EXCLUIDOS = {
    'wp-admin', 'wp-login', 'wp-content', 'feed', 'tag',
    'category', 'author', 'page', 'search', 'cart', 'checkout',
    'mi-cuenta', 'contacto', 'politica-de-privacidad', 'dmca',
    'copyright-policy', 'listado-de-novelas', 'privacidad',
    'registro', 'login', 'wp-json', 'xmlrpc', 'favicon',
}

class AppColors:
    BG_DARK = '#0F172A'
    BG_ELEVATED = '#1E293B'
    BG_HOVER = '#334155'
    PRIMARY = '#7C3AED'
    PRIMARY_LIGHT = '#8B5CF6'
    ACCENT_GREEN = '#10B981'
    ACCENT_RED = '#EF4444'
    ACCENT_BLUE = '#3B82F6'
    TEXT_PRIMARY = '#F1F5F9'
    TEXT_SECONDARY = '#94A3B8'
    BORDER = '#334155'

def obtener_novelas_existentes() -> Dict[str, str]:
    logger.debug("→ Consultando novelas existentes en MongoDB...")
    start = time.time()
    result = {
        novela['url']: str(novela['_id'])
        for novela in coleccion_app_novela.find({'sitio_id': SITIO_ID}, {'url': 1})
    }
    elapsed = time.time() - start
    logger.info(f"✅ {len(result)} novelas existentes en BD ({elapsed:.2f}s)")
    return result

def obtener_novelas_url_existentes():
    return set([
        novela['url']
        for novela in coleccion_app_novela.find({'sitio_id': SITIO_ID}, {'url': 1})
    ])

def obtener_capitulos_existentes(novel_id: str) -> set:
    start = time.time()
    result = {
        str(cap['url']).strip()
        for cap in coleccion_app_capitulo.find({'novela_id': novel_id}, {'url': 1})
    }
    elapsed = time.time() - start
    logger.debug(f"  → {len(result)} capítulos existentes para novela {novel_id[:8]}... ({elapsed:.2f}s)")
    return result

def obtener_datos_novela(driver, url_novela):
    logger.info(f"  📖 Extrayendo datos de novela: {url_novela}")
    start = time.time()
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    datos_novela = {
        'titulo': 'N/A', 'autor': 'N/A', 'estado': 'N/A',
        'descripcion': 'N/A', 'generos': [], 'imagen_url': 'N/A', 'url': url_novela
    }
    try:
        logger.debug("    → Extrayendo título...")
        title_el = soup.select_one('h1.nv-title')
        if title_el:
            datos_novela['titulo'] = title_el.get_text(strip=True)
            logger.debug(f"      ✓ Título: {datos_novela['titulo'][:50]}...")
        else:
            title_tag = soup.find('title')
            if title_tag:
                datos_novela['titulo'] = re.sub(r'\s*[-–]\s*$', '', title_tag.text.strip()).strip()
                logger.debug(f"      ✓ Título (fallback): {datos_novela['titulo'][:50]}...")
        
        logger.debug("    → Extrayendo imagen...")
        img_element = soup.select_one('.nv-cover img') or soup.select_one('img.wp-post-image')
        if img_element:
            src = img_element.get('data-src') or img_element.get('src', '')
            datos_novela['imagen_url'] = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)
            logger.debug(f"      ✓ Imagen: {datos_novela['imagen_url'][:60]}...")
        else:
            logger.warning("      ⚠️ Sin imagen encontrada")
        
        logger.debug("    → Extrayendo sinopsis...")
        synopsis_el = soup.select_one('#nvt-sinopsis .nv-synopsis')
        if synopsis_el:
            paragraphs = [p.get_text(strip=True) for p in synopsis_el.find_all('p') 
                         if p.get_text(strip=True) and p.get_text(strip=True) != '\xa0']
            datos_novela['descripcion'] = ' '.join(paragraphs) or 'N/A'
            logger.debug(f"      ✓ Sinopsis: {len(datos_novela['descripcion'])} caracteres")
        else:
            logger.warning("      ⚠️ Sin sinopsis encontrada")
        
        logger.debug("    → Extrayendo géneros...")
        category_links = soup.select('a[rel="category tag"]')
        datos_novela['generos'] = [a.text.strip() for a in category_links if a.text.strip()] if category_links else []
        if datos_novela['generos']:
            logger.debug(f"      ✓ Géneros: {', '.join(datos_novela['generos'])}")
        else:
            logger.debug("      ⚠️ Sin géneros encontrados")
        
        logger.debug("    → Extrayendo autor...")
        if synopsis_el:
            match = re.search(r'(?:Autor|Author|Escritor|Writer)\s*[:\-]\s*(.+?)(?:\n|$)', synopsis_el.get_text(), re.IGNORECASE)
            if match:
                datos_novela['autor'] = match.group(1).strip()
                logger.debug(f"      ✓ Autor: {datos_novela['autor']}")
            else:
                logger.debug("      ⚠️ Autor no encontrado")
        
        logger.debug("    → Extrayendo estado...")
        status_el = soup.select_one('.nv-status-inner')
        if status_el:
            status_text = status_el.get_text(strip=True).lower()
            if 'en emisión' in status_text or 'ongoing' in status_text:
                datos_novela['estado'] = 'Ongoing'
            elif 'finalizada' in status_text or 'completa' in status_text or 'completed' in status_text:
                datos_novela['estado'] = 'Completed'
            elif 'pausa' in status_text or 'pausada' in status_text:
                datos_novela['estado'] = 'Pausa'
            elif 'abandonado' in status_text or 'abandonada' in status_text:
                datos_novela['estado'] = 'Abandonado'
            logger.debug(f"      ✓ Estado: {datos_novela['estado']}")
        else:
            logger.debug("      ⚠️ Estado no encontrado")
    except Exception as e:
        logger.error(f"    ❌ Error extrayendo datos: {e}")
    elapsed = time.time() - start
    logger.info(f"  ✅ Datos extraídos en {elapsed:.2f}s")
    return datos_novela

def procesar_capitulos(driver, url_novela):
    logger.info(f"  📚 Procesando capítulos de: {url_novela}")
    start_total = time.time()
    capitulos = []
    urls_vistas = set()
    try:
        page_source = driver.page_source
        logger.debug("    → Buscando CAT_ID en página...")
        cat_id_match = re.search(r'var\s+CAT_ID\s*=\s*(\d+)', page_source)
        if not cat_id_match:
            logger.error(f"    ❌ No se encontró CAT_ID en {url_novela}")
            return capitulos
        cat_id = cat_id_match.group(1)
        ajax_url_match = re.search(r"var\s+AJ\s*=\s*['\"](.+?)['\"]", page_source)
        ajax_url = ajax_url_match.group(1) if ajax_url_match else 'https://devilnovels.com/wp-admin/admin-ajax.php'
        logger.info(f"    → CAT_ID: {cat_id}, AJAX URL: {ajax_url}")
        
        ajax_script = """
        var callback = arguments[arguments.length - 1];
        var params = new URLSearchParams({
            action: 'dv_load_chapters', cat_id: arguments[0], page: arguments[1], search: ''
        });
        fetch(arguments[2], {
            method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: params.toString()
        }).then(function(r){ return r.json(); })
        .then(function(d){ callback(d); })
        .catch(function(e){ callback({success: false, error: e.message}); });
        """
        driver.set_script_timeout(60)
        
        logger.debug("    → Solicitando página 1...")
        start_page = time.time()
        data = driver.execute_async_script(ajax_script, cat_id, '1', ajax_url)
        elapsed = time.time() - start_page
        if not data or not data.get('success'):
            logger.error(f"    ❌ Error en respuesta AJAX (pág 1): {data}")
            return capitulos
        total_pages = data['data'].get('pages', 1)
        total_ch = data['data'].get('total', 0)
        logger.info(f"    → Total páginas: {total_pages}, Total capítulos: {total_ch} ({elapsed:.2f}s)")
        
        for ch in data['data'].get('chapters', []):
            titulo = ch.get('title', '').strip()
            url = ch.get('link', '').strip()
            if titulo and url and url not in urls_vistas:
                urls_vistas.add(url)
                capitulos.append({'titulo': titulo, 'url': url})
        logger.debug(f"    ✓ Página 1/{total_pages}: {len(capitulos)} capítulos")
        
        max_retries = 3
        for page_num in range(2, total_pages + 1):
            page_ok = False
            for attempt in range(1, max_retries + 1):
                try:
                    logger.debug(f"    → Solicitando página {page_num}/{total_pages} (intento {attempt})...")
                    start_page = time.time()
                    data = driver.execute_async_script(ajax_script, cat_id, str(page_num), ajax_url)
                    elapsed = time.time() - start_page
                    if not data or not data.get('success'):
                        logger.warning(f"      ⚠️ Respuesta inválida, reintentando...")
                        time.sleep(1 * attempt)
                        continue
                    for ch in data['data'].get('chapters', []):
                        titulo = ch.get('title', '').strip()
                        url = ch.get('link', '').strip()
                        if titulo and url and url not in urls_vistas:
                            urls_vistas.add(url)
                            capitulos.append({'titulo': titulo, 'url': url})
                    logger.debug(f"    ✓ Página {page_num}/{total_pages}: {len(capitulos)} acumulados ({elapsed:.2f}s)")
                    page_ok = True
                    break
                except Exception as e:
                    logger.warning(f"    ⚠️ Error página {page_num} (intento {attempt}): {e}")
                    time.sleep(1 * attempt)
            if not page_ok:
                logger.error(f"    ❌ No se pudo obtener página {page_num} después de {max_retries} intentos")
            time.sleep(0.5)
    except TimeoutException:
        logger.error(f"    ❌ Timeout en capítulos de {url_novela}")
    except Exception as e:
        logger.error(f"    ❌ Error en capítulos de {url_novela}: {e}")
    elapsed_total = time.time() - start_total
    logger.info(f"  ✅ Total capítulos: {len(capitulos)} en {elapsed_total:.2f}s")
    return capitulos

class DevilnovelsScraper:
    def __init__(self, driver, page_pubsub, existing_novels):
        self.driver = driver
        self.page_pubsub = page_pubsub
        self.existing_novels = existing_novels
        self.base_url = "https://devilnovels.com"
        self.list_url = f"{self.base_url}/listado-de-novelas/"
        self.generos_excluidos = {'LGBT', 'Shoujo Ai', 'Shounen Ai', 'Yaoi', 'Yuri', 'BL', 'BG', 'GL'}

    def scrape_novels_from_listing(self):
        logger.info("=" * 60)
        logger.info("SCRAPEANDO LISTADO DESDE WEB")
        logger.info("=" * 60)
        novel_urls = []
        start_total = time.time()
        try:
            logger.info(f"→ Navegando a: {self.list_url}")
            start_nav = time.time()
            self.driver.get(self.list_url)
            logger.info(f"  ✓ Página cargada en {time.time() - start_nav:.2f}s")
            
            logger.info("→ Esperando grilla de novelas...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pvc-featured-pages-grid"))
            )
            logger.info("  ✓ Grilla encontrada")
            
            logger.info("→ Scroll al final para cargar contenido...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            logger.info("→ Parseando HTML con BeautifulSoup...")
            start_parse = time.time()
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            novel_cards = soup.select('.pvc-featured-page-item')
            logger.info(f"  ✓ {len(novel_cards)} cards encontradas en {time.time() - start_parse:.2f}s")
            
            seen_urls = set()
            for i, card in enumerate(novel_cards):
                link = card.select_one('a[href]')
                if not link:
                    logger.debug(f"  ⚠️ Card {i+1}: sin enlace")
                    continue
                href = link.get('href', '').strip().rstrip('/')
                if not href or href in seen_urls or 'devilnovels.com' not in href:
                    continue
                parsed = urlparse(href + '/')
                path = parsed.path.strip('/')
                segments = [s for s in path.split('/') if s]
                if len(segments) != 1:
                    logger.debug(f"  ⚠️ URL inválida: {href}")
                    continue
                slug = segments[0]
                if slug in SLUGS_EXCLUIDOS or '.' in slug:
                    logger.debug(f"  ⚠️ Slug excluido: {slug}")
                    continue
                url_normalizada = f"https://devilnovels.com/{slug}/"
                seen_urls.add(href)
                novel_urls.append(url_normalizada)
            
            novel_urls = list(dict.fromkeys(novel_urls))
            elapsed = time.time() - start_total
            logger.info(f"✅ {len(novel_urls)} URLs válidas en {elapsed:.2f}s")
        except TimeoutException:
            logger.error("❌ Timeout cargando listado")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        return novel_urls

    def scrape_all_novels_automatic(self, selected_urls=None):
        logger.info("=" * 60)
        logger.info("INICIANDO PROCESO DE SCRAPING AUTOMÁTICO")
        logger.info("=" * 60)
        start_total = time.time()
        
        self.page_pubsub.send_all({
            "status": "Iniciando scraping...", "color": AppColors.PRIMARY_LIGHT, "progress": True
        })
        try:
            logger.info("→ Obteniendo novelas existentes en BD...")
            existing_novels = obtener_novelas_existentes()
            
            if selected_urls:
                all_novel_urls = selected_urls
                logger.info(f"→ Procesando {len(all_novel_urls)} novelas SELECCIONADAS")
            else:
                try:
                    logger.info("→ Leyendo CSV...")
                    all_novel_urls = pd.read_csv('all_novel_devilnovels_urls.csv')['url'].tolist()
                    logger.info(f"  ✓ {len(all_novel_urls)} URLs en CSV")
                except Exception as e:
                    logger.warning(f"  ⚠️ CSV no encontrado o vacío: {e}")
                    all_novel_urls = []
                
                if not all_novel_urls:
                    logger.info("→ CSV vacío, scrapeando desde web...")
                    self.page_pubsub.send_all({
                        "status": "Scrapeando listado desde web...", "color": AppColors.PRIMARY_LIGHT, "progress": True
                    })
                    all_novel_urls = self.scrape_novels_from_listing()
                    if all_novel_urls:
                        logger.info(f"→ Guardando {len(all_novel_urls)} URLs en CSV...")
                        pd.DataFrame(all_novel_urls, columns=['url']).to_csv('all_novel_devilnovels_urls.csv', index=False)
                        logger.info("  ✓ CSV guardado")
            
            total_novels = len(all_novel_urls)
            processed_count = 0
            exitosas = 0
            saltadas_genero = 0
            errores = 0
            
            start_index = INDICE_CONTINUACION if not selected_urls else 0
            novelas_a_procesar = all_novel_urls[start_index:]
            logger.info(f"→ Procesando desde índice {start_index}: {len(novelas_a_procesar)} novelas")
            
            for i, novel_url in enumerate(novelas_a_procesar):
                current_index = start_index + i
                processed_count = current_index + 1
                novela_start = time.time()
                
                logger.info("-" * 60)
                logger.info(f"NOVELA {processed_count}/{total_novels} ({(processed_count/total_novels*100):.1f}%)")
                logger.info(f"→ URL: {novel_url}")
                
                self.page_pubsub.send_all({
                    "status": f"({processed_count}/{total_novels}) {novel_url}",
                    "color": AppColors.PRIMARY_LIGHT, "progress": True
                })
                
                logger.info("→ Navegando a página de novela...")
                self.driver.get(novel_url)
                time.sleep(2)
                
                try:
                    datos_detalle = obtener_datos_novela(self.driver, novel_url)
                    generos_novela = set(datos_detalle['generos'])
                    
                    logger.info(f"→ Verificando géneros excluidos...")
                    if self.generos_excluidos.isdisjoint(generos_novela):
                        logger.info("  ✓ Géneros OK")
                        
                        datos_capitulos = procesar_capitulos(self.driver, novel_url)
                        novel_name = datos_detalle['titulo'].upper()
                        
                        if novel_url in existing_novels:
                            novel_id = existing_novels[novel_url]
                            logger.info(f"→ Novela YA EXISTE (ID: {novel_id[:8]}...)")
                            self.page_pubsub.send_all({
                                "status": f"Novela existe: {novel_name[:40]}... - Actualizando capítulos",
                                "color": AppColors.ACCENT_BLUE, "progress": True
                            })
                        else:
                            logger.info("→ Novela NUEVA, insertando en BD...")
                            novel_document = {
                                "sitio_id": SITIO_ID, "nombre": novel_name,
                                "sinopsis": datos_detalle.get('descripcion', 'N/A'),
                                "autor": datos_detalle.get('autor', 'N/A'),
                                "genero": ', '.join(datos_detalle.get('generos', [])),
                                "status": 'emision' if 'Ongoing' in datos_detalle.get('estado', '') else 'completo',
                                "url": datos_detalle.get('url', novel_url),
                                "imagen_url": datos_detalle.get('imagen_url', 'N/A'),
                                "created_at": datetime.now(), "updated_at": datetime.now()
                            }
                            result = coleccion_app_novela.insert_one(novel_document)
                            novel_id = str(result.inserted_id)
                            existing_novels[novel_url] = novel_id
                            logger.info(f"  ✓ Novela insertada (ID: {novel_id})")
                            self.page_pubsub.send_all({
                                "status": f"Nueva novela: {novel_name[:40]}...",
                                "color": AppColors.ACCENT_GREEN, "progress": True
                            })
                        
                        logger.info("→ Verificando capítulos existentes...")
                        existing_chapters_set = obtener_capitulos_existentes(novel_id)
                        chapters_to_insert = []
                        
                        for idx, cap_info in enumerate(datos_capitulos):
                            nombre_capitulo = cap_info.get('titulo', '').strip()
                            url_capitulo = cap_info.get('url', '').strip()
                            if url_capitulo and url_capitulo not in existing_chapters_set:
                                chapters_to_insert.append({
                                    "novela_id": novel_id, "nombre": nombre_capitulo,
                                    "url": url_capitulo,
                                    "created_at": datetime.now() + timedelta(microseconds=idx),
                                    "updated_at": datetime.now() + timedelta(microseconds=idx)
                                })
                        
                        if chapters_to_insert:
                            logger.info(f"→ Insertando {len(chapters_to_insert)} capítulos nuevos...")
                            coleccion_app_capitulo.insert_many(chapters_to_insert)
                            logger.info(f"  ✓ {len(chapters_to_insert)} capítulos insertados")
                            self.page_pubsub.send_all({
                                "status": f"+{len(chapters_to_insert)} capítulos: {novel_name[:30]}...",
                                "color": AppColors.ACCENT_GREEN, "progress": True
                            })
                            exitosas += 1
                        else:
                            logger.info("→ Sin capítulos nuevos")
                            self.page_pubsub.send_all({
                                "status": f"Sin capítulos nuevos: {novel_name[:30]}...",
                                "color": AppColors.TEXT_SECONDARY, "progress": True
                            })
                            exitosas += 1
                        
                        time.sleep(0.5)
                    else:
                        logger.info(f"→ Géneros EXCLUIDOS detectados: {generos_novela}")
                        saltadas_genero += 1
                        self.page_pubsub.send_all({
                            "status": f"Género excluido: {datos_detalle['titulo']}",
                            "color": AppColors.ACCENT_RED, "progress": True
                        })
                    
                    elapsed = time.time() - novela_start
                    logger.info(f"✅ Novela {processed_count}/{total_novels} completada en {elapsed:.2f}s")
                    
                except Exception as e:
                    errores += 1
                    logger.error(f"❌ Error procesando novela: {e}")
                    self.page_pubsub.send_all({
                        "status": f"Error: {str(e)[:80]}",
                        "color": AppColors.ACCENT_RED, "progress": True
                    })
            
            elapsed_total = time.time() - start_total
            logger.info("=" * 60)
            logger.info("SCRAPING COMPLETADO")
            logger.info("=" * 60)
            logger.info(f"⏱️  Tiempo total: {elapsed_total:.2f}s ({elapsed_total/60:.2f} min)")
            logger.info(f"📊 Total novelas: {total_novels}")
            logger.info(f"✅ Exitosas: {exitosas}")
            logger.info(f"⚠️  Saltadas (género): {saltadas_genero}")
            logger.info(f"❌ Errores: {errores}")
            logger.info(f"📈 Promedio por novela: {elapsed_total/total_novels:.2f}s")
            
            self.page_pubsub.send_all({
                "status": "¡Completado exitosamente!",
                "color": AppColors.ACCENT_GREEN, "progress": False
            })
        except Exception as e:
            elapsed_total = time.time() - start_total
            logger.error("=" * 60)
            logger.error("ERROR CRÍTICO")
            logger.error("=" * 60)
            logger.error(f"⏱️  Tiempo transcurrido: {elapsed_total:.2f}s")
            logger.error(f"❌ Error principal: {str(e)}")
            self.page_pubsub.send_all({
                "status": f"Error principal: {str(e)}",
                "color": AppColors.ACCENT_RED, "progress": False
            })

def main(page: ft.Page):
    logger.info("=" * 60)
    logger.info("INICIALIZANDO UI FLET")
    logger.info("=" * 60)
    page.title = "📚 DevilNovels Scraper"
    page.window_width = 1200
    page.window_height = 800
    page.bgcolor = AppColors.BG_DARK
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    logger.info(f"→ Ventana: {page.window_width}x{page.window_height}")
    logger.info(f"→ Tema: DARK")
    logger.info(f"→ Padding: {page.padding}")

    driver_instance = [None]
    selected_novels = set()
    all_csv_urls = []
    scraped_urls = []
    logger.info("✅ UI inicializada")

    def create_header():
        return ft.Container(
            content=ft.Row([
                ft.Text("📚 DevilNovels Scraper", size=28, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Container(width=20),
                ft.Icon(ft.Icons.AUTO_FIX_HIGH, color=AppColors.PRIMARY_LIGHT, size=32)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            bgcolor=AppColors.BG_ELEVATED,
            border_radius=12,
            margin=ft.margin.only(bottom=20)
        )

    def create_status_panel():
        global status_text, progress_ring, progress_bar
        status_text = ft.Text("", size=14, color=AppColors.TEXT_SECONDARY, selectable=True)
        progress_ring = ft.ProgressRing(visible=False, color=AppColors.PRIMARY_LIGHT, stroke_width=4)
        progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY_LIGHT, bgcolor=AppColors.BORDER)
        return ft.Container(
            content=ft.Column([
                ft.Row([progress_ring, ft.Text("Estado:", size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY)], spacing=10),
                status_text,
                progress_bar
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=AppColors.BG_ELEVATED,
            border_radius=12,
            border=ft.border.all(1, AppColors.BORDER)
        )

    def load_csv_urls():
        try:
            return pd.read_csv('all_novel_devilnovels_urls.csv')['url'].tolist()
        except Exception:
            return []

    def create_novel_selection_view():
        nonlocal all_csv_urls
        all_csv_urls = load_csv_urls()
        novel_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        def toggle_novel(e, url):
            if url in selected_novels:
                selected_novels.remove(url)
                e.control.bgcolor = AppColors.BG_ELEVATED
            else:
                selected_novels.add(url)
                e.control.bgcolor = AppColors.PRIMARY + "30"
            e.control.update()
            count_text.value = f"{len(selected_novels)} seleccionadas"
            count_text.update()
        for url in all_csv_urls:
            title = url.replace('https://devilnovels.com/', '').replace('/', '').replace('-', ' ').title()
            card = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, size=24, color=AppColors.TEXT_SECONDARY),
                    ft.Column([
                        ft.Text(title[:60] + "..." if len(title) > 60 else title, size=13, color=AppColors.TEXT_PRIMARY),
                        ft.Text(url, size=11, color=AppColors.TEXT_SECONDARY)
                    ], spacing=2, expand=True)
                ], spacing=12),
                padding=ft.padding.all(12),
                bgcolor=AppColors.BG_ELEVATED,
                border_radius=8,
                border=ft.border.all(1, AppColors.BORDER),
                on_click=lambda e, u=url: toggle_novel(e, u),
                ink=True
            )
            novel_list.controls.append(card)
        count_text = ft.Text(f"0 seleccionadas", size=14, color=AppColors.PRIMARY_LIGHT, weight=ft.FontWeight.BOLD)
        return ft.Column([
            ft.Row([
                ft.Text(f"📋 Novelas en CSV: {len(all_csv_urls)}", size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                count_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            novel_list
        ], spacing=10)

    def create_tab_content():
        tabs = []
        def scrape_from_web(e):
            logger.info("=" * 60)
            logger.info("USUARIO: Actualizar CSV desde Web")
            logger.info("=" * 60)
            def run():
                try:
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', 'geckodriver.exe')
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = DevilnovelsScraper(driver, page.pubsub, {})
                    scraped_urls = scraper.scrape_novels_from_listing()
                    if scraped_urls:
                        logger.info(f"→ Guardando {len(scraped_urls)} URLs en CSV...")
                        pd.DataFrame(scraped_urls, columns=['url']).to_csv('all_novel_devilnovels_urls.csv', index=False)
                        logger.info("  ✓ CSV actualizado")
                        page.pubsub.send_all({
                            "status": f"✅ CSV actualizado: {len(scraped_urls)} novelas",
                            "color": AppColors.ACCENT_GREEN, "progress": False
                        })
                    else:
                        logger.warning("⚠️ No se encontraron novelas")
                        page.pubsub.send_all({
                            "status": "❌ No se encontraron novelas",
                            "color": AppColors.ACCENT_RED, "progress": False
                        })
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
                        logger.info("→ Cerrando Firefox...")
                        driver_instance[0].quit()
                        logger.info("  ✓ Firefox cerrado")
            threading.Thread(target=run, daemon=True).start()
        def scrape_all_csv(e):
            logger.info("=" * 60)
            logger.info("USUARIO: Scrapear TODAS las novelas del CSV")
            logger.info("=" * 60)
            def run():
                try:
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', 'geckodriver.exe')
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = DevilnovelsScraper(driver, page.pubsub, {})
                    scraper.scrape_all_novels_automatic()
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
                        logger.info("→ Cerrando Firefox...")
                        driver_instance[0].quit()
                        logger.info("  ✓ Firefox cerrado")
            threading.Thread(target=run, daemon=True).start()
        
        def scrape_selected(e):
            logger.info("=" * 60)
            logger.info(f"USUARIO: Scrapear {len(selected_novels)} novelas SELECCIONADAS")
            logger.info("=" * 60)
            def run():
                try:
                    if not selected_novels:
                        logger.warning("⚠️ No hay novelas seleccionadas")
                        page.pubsub.send_all({
                            "status": "⚠️ Selecciona al menos 1 novela",
                            "color": AppColors.ACCENT_RED, "progress": False
                        })
                        return
                    logger.info(f"→ Novelas seleccionadas: {len(selected_novels)}")
                    for i, url in enumerate(selected_novels):
                        logger.info(f"  {i+1}. {url}")
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', 'geckodriver.exe')
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = DevilnovelsScraper(driver, page.pubsub, {})
                    scraper.scrape_all_novels_automatic(selected_urls=list(selected_novels))
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
                        logger.info("→ Cerrando Firefox...")
                        driver_instance[0].quit()
                        logger.info("  ✓ Firefox cerrado")
            threading.Thread(target=run, daemon=True).start()
        def select_all(e):
            for card in novel_selection_view.controls[1].controls:
                if card.bgcolor != AppColors.PRIMARY + "30":
                    card.bgcolor = AppColors.PRIMARY + "30"
                    url = all_csv_urls[novel_selection_view.controls[1].controls.index(card)]
                    selected_novels.add(url)
            count_text.value = f"{len(selected_novels)} seleccionadas"
            page.update()
        def deselect_all(e):
            for card in novel_selection_view.controls[1].controls:
                card.bgcolor = AppColors.BG_ELEVATED
            selected_novels.clear()
            count_text.value = "0 seleccionadas"
            page.update()
        novel_selection_view = create_novel_selection_view()
        tab1 = ft.Container(
            content=ft.Column([
                ft.Text("🌐 Scrapear listado desde web", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Text("Obtiene todas las novelas desde devilnovels.com/listado-de-novelas/ y actualiza el CSV", 
                       size=13, color=AppColors.TEXT_SECONDARY),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "🔄 Actualizar CSV desde Web",
                    on_click=scrape_from_web,
                    icon=ft.Icons.REFRESH,
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.PRIMARY,
                        color=AppColors.TEXT_PRIMARY,
                        padding=ft.padding.all(16),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ], spacing=10),
            padding=ft.padding.all(20)
        )
        tab2 = ft.Container(
            content=ft.Column([
                ft.Text("📋 Scrapear todas las novelas del CSV", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Text(f"Procesa las {len(all_csv_urls)} novelas del archivo CSV", 
                       size=13, color=AppColors.TEXT_SECONDARY),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "▶️ Iniciar Scraping Completo",
                    on_click=scrape_all_csv,
                    icon=ft.Icons.PLAY_ARROW,
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.ACCENT_GREEN,
                        color=AppColors.TEXT_PRIMARY,
                        padding=ft.padding.all(16),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ], spacing=10),
            padding=ft.padding.all(20)
        )
        tab3 = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("✅ Seleccionar novelas específicas", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                    ft.Row([
                        ft.ElevatedButton("Seleccionar todas", on_click=select_all, icon=ft.Icons.SELECT_ALL, height=36),
                        ft.ElevatedButton("Deseleccionar todas", on_click=deselect_all, icon=ft.Icons.CLEAR_ALL, height=36)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text("Haz clic en las novelas para seleccionarlas", size=13, color=AppColors.TEXT_SECONDARY),
                ft.Container(height=10),
                novel_selection_view,
                ft.Container(height=10),
                ft.ElevatedButton(
                    f"▶️ Scrapear Seleccionadas ({len(selected_novels)})",
                    on_click=scrape_selected,
                    icon=ft.Icons.PLAY_ARROW,
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.ACCENT_BLUE,
                        color=AppColors.TEXT_PRIMARY,
                        padding=ft.padding.all(16),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ], spacing=10),
            padding=ft.padding.all(20)
        )
        return ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="🌐 Actualizar CSV", content=tab1, icon=ft.Icons.CLOUD_SYNC),
                ft.Tab(text="📋 Todas CSV", content=tab2, icon=ft.Icons.LIST_ALT),
                ft.Tab(text="✅ Selección", content=tab3, icon=ft.Icons.CHECK_BOX)
            ],
            expand=True
        )

    def on_pubsub_message(msg):
        if isinstance(msg, dict):
            status = msg.get("status", "")
            color = msg.get("color", AppColors.TEXT_SECONDARY)
            progress = msg.get("progress", False)
            status_text.value = status
            status_text.color = color
            progress_ring.visible = progress
            progress_bar.visible = progress
            page.update()
            # Log todos los mensajes de estado
            if "Error" in status or "❌" in status:
                logger.error(f"UI Status: {status}")
            elif "✅" in status or "Completado" in status:
                logger.info(f"UI Status: {status}")
            else:
                logger.debug(f"UI Status: {status}")

    page.pubsub.subscribe(on_pubsub_message)
    logger.info("✓ PubSub suscrito")

    page.add(
        create_header(),
        ft.Row([
            ft.Container(
                content=create_status_panel(),
                expand=2
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("ℹ️ Instrucciones", size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                    ft.Text("1. Actualiza el CSV desde la web", size=13, color=AppColors.TEXT_SECONDARY),
                    ft.Text("2. Scrapea todas o selecciona específicas", size=13, color=AppColors.TEXT_SECONDARY),
                    ft.Text("3. Los géneros excluidos se saltan automáticamente", size=13, color=AppColors.TEXT_SECONDARY),
                ], spacing=8),
                expand=1,
                padding=ft.padding.all(16),
                bgcolor=AppColors.BG_ELEVATED,
                border_radius=12,
                border=ft.border.all(1, AppColors.BORDER)
            )
        ], spacing=20),
        create_tab_content()
    )
    logger.info("✅ Componentes UI agregados")
    logger.info("=" * 60)
    logger.info("APLICACIÓN FLET LISTA")
    logger.info("=" * 60)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("DEVILNOVELS SCRAPER - INICIO DEL PROGRAMA")
    logger.info("=" * 60)
    ft.app(target=main)
