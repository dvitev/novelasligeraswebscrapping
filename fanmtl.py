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
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()

if os.name != 'nt':
    temp_dir = "~/_tmp"
    os.makedirs(temp_dir) if not os.path.exists(temp_dir) else None
    os.environ["TMPDIR"] = temp_dir

MONGO_URI = 'mongodb://192.168.1.11:27017/'
DB_NAME = 'recopilarnovelas'
SITIO_ID = '67de23f6e131d527f2995103'
INDICE_CONTINUACION = int(os.getenv('INDICE_CONTINUACION', 0))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("INICIALIZANDO FANMTL SCRAPER")
logger.info("=" * 60)
logger.info(f"MONGO_URI: {MONGO_URI}")
logger.info(f"DB_NAME: {DB_NAME}")
logger.info(f"SITIO_ID: {SITIO_ID}")
logger.info(f"INDICE_CONTINUACION: {INDICE_CONTINUACION}")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coleccion_app_novela = db['app_novela']
coleccion_app_capitulo = db['app_capitulo']

try:
    client.admin.command('ping')
    logger.info("✅ Conexión a MongoDB exitosa")
except Exception as e:
    logger.error(f"❌ Error conectando a MongoDB: {e}")
    raise

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
        'titulo': 'N/A', 'autor': 'N/A', 'ilustrador': 'N/A',
        'estado': 'N/A', 'alternativo': 'N/A', 'descripcion': 'N/A',
        'generos': [], 'imagen_url': 'N/A', 'url': url_novela
    }
    try:
        logger.debug("    → Extrayendo título...")
        title_element = soup.select_one('article#novel h1.novel-title')
        if title_element:
            datos_novela['titulo'] = title_element.get_text(strip=True)
            logger.debug(f"      ✓ Título: {datos_novela['titulo'][:50]}...")
        else:
            logger.warning("      ⚠️ Título no encontrado")
        
        logger.debug("    → Extrayendo imagen...")
        img_element = soup.select_one('.fixed-img .cover img')
        if img_element:
            datos_novela['imagen_url'] = img_element.get('src', '')
            logger.debug(f"      ✓ Imagen: {datos_novela['imagen_url'][:60]}...")
        else:
            logger.warning("      ⚠️ Imagen de portada no encontrada")
        
        logger.debug("    → Extrayendo autor...")
        author_div = soup.select_one('.novel-info .author')
        if author_div:
            author_span = author_div.find('span', string=re.compile(r'Author:', re.IGNORECASE))
            if author_span and author_span.next_sibling:
                datos_novela['autor'] = author_span.next_sibling.strip()
            else:
                author_text = author_div.get_text(separator=' ', strip=True)
                match = re.search(r'Author:\s*(.+?)(?:\n|$)', author_text, re.IGNORECASE)
                if match:
                    datos_novela['autor'] = match.group(1).strip()
            logger.debug(f"      ✓ Autor: {datos_novela['autor']}")
        else:
            logger.debug("      ⚠️ Sección de autor no encontrada")
        
        logger.debug("    → Extrayendo estado...")
        status_element = soup.select_one('.header-stats span:nth-of-type(2) strong')
        if status_element:
            datos_novela['estado'] = status_element.get_text(strip=True)
            logger.debug(f"      ✓ Estado: {datos_novela['estado']}")
        else:
            status_fallback = soup.select_one('.status')
            if status_fallback:
                datos_novela['estado'] = status_fallback.get_text(strip=True)
                logger.debug(f"      ✓ Estado (fallback): {datos_novela['estado']}")
            else:
                logger.debug("      ⚠️ Estado no encontrado")
        
        logger.debug("    → Extrayendo sinopsis...")
        summary_div = soup.select_one('div.summary div.content')
        if summary_div:
            datos_novela['descripcion'] = summary_div.get_text(strip=True)
            logger.debug(f"      ✓ Sinopsis: {len(datos_novela['descripcion'])} caracteres")
        else:
            logger.warning("      ⚠️ Sin sinopsis encontrada")
            datos_novela['descripcion'] = "N/A"
        
        logger.debug("    → Extrayendo géneros/categorías...")
        categories_div = soup.select_one('.categories')
        if categories_div:
            generos_links = categories_div.select('ul li a.property-item')
            datos_novela['generos'] = [a.get_text(strip=True) for a in generos_links if a.get_text(strip=True)]
            if datos_novela['generos']:
                logger.debug(f"      ✓ Géneros: {', '.join(datos_novela['generos'])}")
            else:
                logger.debug("      ⚠️ Sin géneros encontrados")
        else:
            logger.debug("      ⚠️ Sección de categorías no encontrada")
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
        logger.debug("    → Verificando pestaña de capítulos...")
        try:
            tab_chapters = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-tab='chapters']"))
            )
            if "_on" not in tab_chapters.get_attribute("class"):
                tab_chapters.click()
                time.sleep(1)
                logger.debug("      ✓ Cambiado a pestaña de capítulos")
        except TimeoutException:
            logger.debug("      ✓ Pestaña de capítulos ya activa o no encontrada")

        logger.debug("    → Esperando contenedor de lista de capítulos...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#chpagedlist"))
        )
        logger.debug("      ✓ Contenedor #chpagedlist encontrado")
        
        pagina_actual = 1
        total_paginas_procesadas = 0
        max_paginas = 5000

        while total_paginas_procesadas < max_paginas:
            logger.debug(f"    → Procesando página {pagina_actual} (intento #{total_paginas_procesadas + 1})...")
            start_page = time.time()
            
            try:
                chpagedlist_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#chpagedlist"))
                )
            except TimeoutException:
                logger.error("    ❌ No se encontró #chpagedlist")
                break

            elementos_capitulos = chpagedlist_container.find_elements(By.CSS_SELECTOR, "ul.chapter-list li a")

            if not elementos_capitulos:
                logger.warning(f"    ⚠️ No se encontraron capítulos en página {pagina_actual}")
                break

            logger.debug(f"    → {len(elementos_capitulos)} capítulos en página {pagina_actual}")
            
            for elemento in elementos_capitulos:
                capitulo_info = {'titulo': 'N/A', 'url': 'N/A'}
                try:
                    strong_element = elemento.find_element(By.TAG_NAME, 'strong')
                    capitulo_info['titulo'] = strong_element.text.strip()
                    capitulo_info['url'] = urljoin(url_novela, elemento.get_attribute('href'))
                    if capitulo_info['url'] not in urls_vistas:
                        urls_vistas.add(capitulo_info['url'])
                        capitulos.append(capitulo_info)
                except Exception as e:
                    logger.debug(f"      ⚠️ Error procesando capítulo: {e}")
                    continue

            logger.debug(f"    ✓ Página {pagina_actual}: {len(capitulos)} capítulos acumulados")
            
            try:
                pagination_links = chpagedlist_container.find_elements(By.CSS_SELECTOR, ".pagination a[data-ajax='true'][data-ajax-update='#chpagedlist']")
                
                if not pagination_links:
                    logger.info("    → No hay más páginas de capítulos")
                    break
                
                next_page_link = None
                for link in pagination_links:
                    texto = link.text.strip()
                    if texto == '>':
                        next_page_link = link
                        logger.debug(f"      ✓ Enlace 'Siguiente' encontrado")
                        break
                    elif texto == '>>':
                        next_page_link = link
                        logger.debug(f"      ✓ Enlace 'Última' encontrado")
                        break
                
                if next_page_link:
                    logger.info(f"    → Navegando a página {pagina_actual + 1}...")
                    next_page_link.click()
                    
                    try:
                        WebDriverWait(driver, 10).until(
                            lambda d: d.find_element(By.CSS_SELECTOR, "#chpagedlist")
                        )
                        time.sleep(1.5)
                        total_paginas_procesadas += 1
                        pagina_actual += 1
                        logger.debug(f"      ✓ Página {pagina_actual} cargada ({time.time() - start_page:.2f}s)")
                    except TimeoutException:
                        logger.warning("    ⚠️ Timeout esperando actualización AJAX")
                        break
                else:
                    logger.info("    → No se encontró enlace siguiente")
                    break

            except NoSuchElementException:
                logger.info("    → Fin de paginación")
                break
            except Exception as e:
                logger.error(f"    ❌ Error en paginación: {e}")
                break

    except TimeoutException:
        logger.error(f"    ❌ Timeout en capítulos de {url_novela}")
    except Exception as e:
        logger.error(f"    ❌ Error en capítulos de {url_novela}: {e}")
    
    elapsed_total = time.time() - start_total
    logger.info(f"  ✅ Total capítulos: {len(capitulos)} en {elapsed_total:.2f}s")
    return capitulos

class FanmtlScraperAutomatico:
    def __init__(self, driver, page_pubsub, existing_novels):
        self.driver = driver
        self.page_pubsub = page_pubsub
        self.existing_novels = existing_novels
        self.base_url = "https://www.fanmtl.com"
        self.list_url = f"{self.base_url}/list/all/all-onclick-0.html"
        self.current_page = 1
        self.generos_excluidos = {'LGBT', 'Shoujo Ai', 'Shounen Ai', 'Yaoi', 'Yuri', 'BL', 'BG', 'GL'}

    def get_total_pages(self):
        """Obtiene el número total de páginas de la lista de novelas."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination-container .pagination li"))
            )
            
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, ".pagination-container .pagination li a")
            
            if not page_elements:
                logger.info("Solo se encontró una página o no hay enlaces de paginación.")
                return 1
            
            page_numbers = []
            for elem in page_elements:
                href = elem.get_attribute('href')
                if href:
                    match = re.search(r'onclick-(\d+)\.html', href)
                    if match:
                        page_num = int(match.group(1))
                        page_numbers.append(page_num)
            
            if page_numbers:
                total_pages = max(page_numbers) + 1
                logger.info(f"Total de páginas detectadas: {total_pages}")
                return total_pages
            else:
                logger.warning("No se pudieron extraer números de página. Se asume 1 página.")
                return 1
                
        except TimeoutException:
            logger.error("Timeout buscando paginación.")
            return 1
        except Exception as e:
            logger.error(f"Error obteniendo total de páginas: {e}")
            return 1

    def scrape_novels_from_page(self):
        """Recopila URLs de novelas de la página actual."""
        novel_urls = []
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.novel-list.grid"))
            )
            
            novel_items = self.driver.find_elements(By.CSS_SELECTOR, "ul.novel-list.grid li.novel-item")
            
            if not novel_items:
                logger.warning(f"No se encontraron novelas en la página {self.current_page}.")
                return novel_urls

            logger.info(f"Encontradas {len(novel_items)} novelas en la página {self.current_page}.")

            for item in novel_items:
                try:
                    title_element = item.find_element(By.CSS_SELECTOR, "h4.novel-title")
                    parent_link = title_element.find_element(By.XPATH, "./..")
                    full_url = parent_link.get_attribute('href')
                    if full_url:
                        novel_urls.append(full_url)
                except Exception as e:
                    logger.error(f"Error extrayendo URL de novela en página {self.current_page}: {e}")
                    continue

        except TimeoutException:
            logger.error(f"Timeout cargando lista de novelas en página {self.current_page}.")
        except Exception as e:
            logger.error(f"Error general scrapeando página {self.current_page}: {e}")
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
                    all_novel_urls = pd.read_csv('all_novel_fanmtl_urls.csv')['url'].tolist()
                    logger.info(f"  ✓ {len(all_novel_urls)} URLs en CSV")
                except Exception as e:
                    logger.warning(f"  ⚠️ CSV no encontrado o vacío: {e}")
                    all_novel_urls = []
                
                if not all_novel_urls:
                    logger.info("→ CSV vacío, scrapeando desde web...")
                    self.page_pubsub.send_all({
                        "status": "Scrapeando listado desde web...", "color": AppColors.PRIMARY_LIGHT, "progress": True
                    })
                    self.driver.get(self.list_url)
                    total_pages = self.get_total_pages()
                    logger.info(f"→ Total páginas: {total_pages}")
                    
                    for page in range(total_pages):
                        self.current_page = page + 1
                        logger.info(f"→ Procesando página {self.current_page} de {total_pages}...")
                        urls_from_page = self.scrape_novels_from_page()
                        all_novel_urls.extend(urls_from_page)
                        
                        if page + 1 < total_pages:
                            next_page_url = f"{self.base_url}/list/all/all-onclick-{page + 1}.html"
                            logger.info(f"→ Navegando a página {page + 2}...")
                            self.driver.get(next_page_url)
                            time.sleep(2)
                    
                    if all_novel_urls:
                        logger.info(f"→ Guardando {len(all_novel_urls)} URLs en CSV...")
                        pd.DataFrame(all_novel_urls, columns=['url']).to_csv('all_novel_fanmtl_urls.csv', index=False)
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
                                "status": f"Novela existe: {novel_name[:40]}... - Verificando capítulos",
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
    page.title = "📚 FanMTL Scraper"
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
    status_text = ft.Text("", size=14, color=AppColors.TEXT_SECONDARY, selectable=True)
    progress_ring = ft.ProgressRing(visible=False, color=AppColors.PRIMARY_LIGHT, stroke_width=4)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY_LIGHT, bgcolor=AppColors.BORDER)
    logger.info("✅ UI inicializada")

    def create_header():
        return ft.Container(
            content=ft.Row([
                ft.Text("📚 FanMTL Scraper", size=28, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Container(width=20),
                ft.Icon(ft.Icons.AUTO_FIX_HIGH, color=AppColors.PRIMARY_LIGHT, size=32)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            bgcolor=AppColors.BG_ELEVATED,
            border_radius=12,
            margin=ft.margin.only(bottom=20)
        )

    def create_status_panel():
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
            return pd.read_csv('all_novel_fanmtl_urls.csv')['url'].tolist()
        except Exception:
            return []

    # Estado de paginación
    pagina_actual = 1
    items_por_pagina = 20
    total_paginas = 1

    def create_novel_selection_view(pagina=1):
        nonlocal all_csv_urls, pagina_actual, total_paginas
        all_csv_urls = load_csv_urls()
        total_urls = len(all_csv_urls)
        total_paginas = max(1, (total_urls + items_por_pagina - 1) // items_por_pagina)
        pagina_actual = max(1, min(pagina, total_paginas))
        
        # Calcular índices para la página actual
        inicio = (pagina_actual - 1) * items_por_pagina
        fin = min(inicio + items_por_pagina, total_urls)
        urls_pagina = all_csv_urls[inicio:fin]
        
        novel_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO, height=400)
        count_text = ft.Text(f"0 seleccionadas (página {pagina_actual}/{total_paginas})", size=14, color=AppColors.PRIMARY_LIGHT, weight=ft.FontWeight.BOLD)
        
        def toggle_novel(e, url):
            if url in selected_novels:
                selected_novels.remove(url)
                e.control.bgcolor = AppColors.BG_ELEVATED
            else:
                selected_novels.add(url)
                e.control.bgcolor = AppColors.PRIMARY + "30"
            e.control.update()
            count_text.value = f"{len(selected_novels)} seleccionadas (página {pagina_actual}/{total_paginas})"
            count_text.update()
        
        for idx, url in enumerate(urls_pagina):
            global_idx = inicio + idx
            title = url.replace('https://www.fanmtl.com/', '').replace('/', '').replace('-', ' ').title()
            is_selected = url in selected_novels
            card = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_BOX if is_selected else ft.Icons.CHECK_BOX_OUTLINE_BLANK,
                        size=24,
                        color=AppColors.PRIMARY_LIGHT if is_selected else AppColors.TEXT_SECONDARY
                    ),
                    ft.Column([
                        ft.Text(f"{global_idx + 1}. {title[:60] + '...' if len(title) > 60 else title}", size=13, color=AppColors.TEXT_PRIMARY),
                        ft.Text(url, size=11, color=AppColors.TEXT_SECONDARY)
                    ], spacing=2, expand=True)
                ], spacing=12),
                padding=ft.padding.all(12),
                bgcolor=AppColors.PRIMARY + "30" if is_selected else AppColors.BG_ELEVATED,
                border_radius=8,
                border=ft.border.all(1, AppColors.BORDER),
                on_click=lambda e, u=url: toggle_novel(e, u),
                ink=True
            )
            novel_list.controls.append(card)
        
        return ft.Column([
            ft.Row([
                ft.Text(f"📋 Novelas en CSV: {total_urls}", size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                count_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            novel_list
        ], spacing=10), count_text

    def create_tab_content():
        novel_selection_view, count_text = create_novel_selection_view(pagina=1)
        
        # Controles de paginación
        txt_pagina_actual = ft.Text(f"1/{total_paginas}", size=14, color=AppColors.TEXT_SECONDARY)
        
        def ir_a_pagina(pagina):
            nonlocal pagina_actual
            pagina_actual = max(1, min(pagina, total_paginas))
            nuevo_view, nuevo_count_text = create_novel_selection_view(pagina=pagina_actual)
            novel_selection_view.controls = nuevo_view.controls
            count_text.value = nuevo_count_text.value
            txt_pagina_actual.value = f"{pagina_actual}/{total_paginas}"
            page.update()
        
        def pagina_anterior(e):
            ir_a_pagina(pagina_actual - 1)
        
        def pagina_siguiente(e):
            ir_a_pagina(pagina_actual + 1)
        
        def select_all(e):
            # Seleccionar todas las URLs (no solo la página actual)
            selected_novels.update(all_csv_urls)
            # Actualizar UI de la página actual
            for card in novel_selection_view.controls[1].controls:
                if hasattr(card, 'bgcolor'):
                    card.bgcolor = AppColors.PRIMARY + "30"
                    if hasattr(card.content, 'controls') and len(card.content.controls) > 0:
                        if hasattr(card.content.controls[0], 'name'):
                            card.content.controls[0].name = ft.Icons.CHECK_BOX
                            card.content.controls[0].color = AppColors.PRIMARY_LIGHT
            count_text.value = f"{len(selected_novels)} seleccionadas (página {pagina_actual}/{total_paginas})"
            page.update()
        
        def deselect_all(e):
            # Deseleccionar todas las URLs
            selected_novels.clear()
            # Actualizar UI de la página actual
            for card in novel_selection_view.controls[1].controls:
                if hasattr(card, 'bgcolor'):
                    card.bgcolor = AppColors.BG_ELEVATED
                    if hasattr(card.content, 'controls') and len(card.content.controls) > 0:
                        if hasattr(card.content.controls[0], 'name'):
                            card.content.controls[0].name = ft.Icons.CHECK_BOX_OUTLINE_BLANK
                            card.content.controls[0].color = AppColors.TEXT_SECONDARY
            count_text.value = f"0 seleccionadas (página {pagina_actual}/{total_paginas})"
            page.update()
        
        def scrape_from_web(e):
            logger.info("=" * 60)
            logger.info("USUARIO: Actualizar CSV desde Web")
            logger.info("=" * 60)
            def run():
                try:
                    geckodriver_filename = 'geckodriver.exe' if os.name == 'nt' else 'geckodriver'
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', geckodriver_filename)
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    if os.name != 'nt':
                        options.binary_location = '/usr/bin/firefox'
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = FanmtlScraperAutomatico(driver, page.pubsub, {})
                    driver.get(scraper.list_url)
                    total_pages = scraper.get_total_pages()
                    all_urls = []
                    for page_num in range(total_pages):
                        scraper.current_page = page_num + 1
                        logger.info(f"→ Procesando página {scraper.current_page}...")
                        urls_from_page = scraper.scrape_novels_from_page()
                        all_urls.extend(urls_from_page)
                        if page_num + 1 < total_pages:
                            next_url = f"{scraper.base_url}/list/all/all-onclick-{page_num + 1}.html"
                            driver.get(next_url)
                            time.sleep(2)
                    if all_urls:
                        pd.DataFrame(all_urls, columns=['url']).to_csv('all_novel_fanmtl_urls.csv', index=False)
                        logger.info(f"  ✓ CSV actualizado con {len(all_urls)} URLs")
                        page.pubsub.send_all({
                            "status": f"✅ CSV actualizado: {len(all_urls)} novelas",
                            "color": AppColors.ACCENT_GREEN, "progress": False
                        })
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
                        driver_instance[0].quit()
                        logger.info("  ✓ Firefox cerrado")
            threading.Thread(target=run, daemon=True).start()
        def scrape_all_csv(e):
            logger.info("=" * 60)
            logger.info("USUARIO: Scrapear TODAS las novelas del CSV")
            logger.info("=" * 60)
            def run():
                try:
                    geckodriver_filename = 'geckodriver.exe' if os.name == 'nt' else 'geckodriver'
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', geckodriver_filename)
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = FanmtlScraperAutomatico(driver, page.pubsub, {})
                    scraper.scrape_all_novels_automatic()
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
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
                    geckodriver_filename = 'geckodriver.exe' if os.name == 'nt' else 'geckodriver'
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', geckodriver_filename)
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = FanmtlScraperAutomatico(driver, page.pubsub, {})
                    scraper.scrape_all_novels_automatic(selected_urls=list(selected_novels))
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
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
                    geckodriver_filename = 'geckodriver.exe' if os.name == 'nt' else 'geckodriver'
                    geckodriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geckodriver', geckodriver_filename)
                    logger.info(f"→ GeckoDriver: {geckodriver_path}")
                    options = webdriver.FirefoxOptions()
                    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    logger.info("→ Iniciando Firefox...")
                    driver = webdriver.Firefox(options=options, service=Service(geckodriver_path))
                    driver_instance[0] = driver
                    logger.info("  ✓ Firefox iniciado")
                    scraper = FanmtlScraperAutomatico(driver, page.pubsub, {})
                    scraper.scrape_all_novels_automatic(selected_urls=list(selected_novels))
                except Exception as ex:
                    logger.error(f"❌ Error: {str(ex)}")
                    page.pubsub.send_all({
                        "status": f"Error: {str(ex)}",
                        "color": AppColors.ACCENT_RED, "progress": False
                    })
                finally:
                    if driver_instance[0]:
                        driver_instance[0].quit()
                        logger.info("  ✓ Firefox cerrado")
            threading.Thread(target=run, daemon=True).start()
        
        tab1 = ft.Container(
            content=ft.Column([
                ft.Text("🌐 Scrapear listado desde web", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                ft.Text("Obtiene todas las novelas desde fanmtl.com y actualiza el CSV", 
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
                ft.Row([
                    ft.IconButton(
                        ft.Icons.CHEVRON_LEFT_ROUNDED,
                        on_click=pagina_anterior,
                        icon_color=AppColors.PRIMARY_LIGHT,
                        tooltip="Página anterior",
                        disabled=pagina_actual <= 1
                    ),
                    txt_pagina_actual,
                    ft.IconButton(
                        ft.Icons.CHEVRON_RIGHT_ROUNDED,
                        on_click=pagina_siguiente,
                        icon_color=AppColors.PRIMARY_LIGHT,
                        tooltip="Página siguiente",
                        disabled=pagina_actual >= total_paginas
                    ),
                    ft.Container(width=20),
                    ft.Text("Ir a:", size=14, color=AppColors.TEXT_SECONDARY),
                    ft.TextField(
                        value=str(pagina_actual),
                        width=60,
                        height=40,
                        text_size=14,
                        text_align=ft.TextAlign.CENTER,
                        border_color=AppColors.BORDER,
                        focused_border_color=AppColors.PRIMARY_LIGHT,
                        input_filter=ft.NumbersOnlyInputFilter(),
                        on_submit=lambda e: ir_a_pagina(int(e.control.value) if e.control.value.isdigit() else pagina_actual)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "▶️ Scrapear Seleccionadas",
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
    logger.info("FANMTL SCRAPER - INICIO DEL PROGRAMA")
    logger.info("=" * 60)
    ft.app(target=main)