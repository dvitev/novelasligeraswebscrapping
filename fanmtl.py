import flet as ft
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from google_trans_new import google_translator
from langdetect import detect, DetectorFactory
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import translators as ts
import undetected_chromedriver as uc
import threading
from bson.objectid import ObjectId
import pandas as pd
import os
import re
import json
import logging
from urllib.parse import urljoin, urlparse

# Configuración inicial
DetectorFactory.seed = 0
MONGO_URI = 'mongodb://192.168.1.11:27017/'
DB_NAME = 'recopilarnovelas'
SITIO_ID = '67de23f6e131d527f2995103'

# Cliente MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coleccion_app_novela = db['app_novela']
coleccion_app_capitulo = db['app_capitulo']

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Colores para la UI
COLOR_ERROR = ft.Colors.RED_600

def obtener_novelas_existentes() -> Dict[str, str]:
    """Obtiene un diccionario de novelas existentes {nombre: id}"""
    return {
        novela['nombre']: str(novela['_id'])
        for novela in coleccion_app_novela.find(
            {'sitio_id': SITIO_ID},
            {'nombre': 1}
        )
    }


def obtener_novelas_url_existentes():
    """Obtiene un diccionario de novelas existentes {nombre: id}"""
    return set([
        novela['url']
        for novela in coleccion_app_novela.find(
            {'sitio_id': SITIO_ID},
            {'url': 1}
        )
    ])

def obtener_capitulos_existentes(novel_id: str) -> set:
    """Obtiene conjunto de nombres de capítulos existentes"""
    return {
        str(cap['nombre']).strip()
        for cap in coleccion_app_capitulo.find(
            {'novela_id': novel_id},
            {'nombre': 1}
        )
    }

def obtener_datos_novela(driver, url_novela):
    """
    Obtiene los datos de una novela individual basándose en la estructura HTML
    del documento adjunto (Pasted_Text_1753570645407.txt).
    """
    logger.info(f"Obteniendo datos de la novela: {url_novela}")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    datos_novela = {
        'titulo': 'N/A',
        'autor': 'N/A',
        'ilustrador': 'N/A',
        'estado': 'N/A',
        'alternativo': 'N/A',
        'descripcion': 'N/A',
        'generos': [],
        'imagen_url': 'N/A',
        'url': url_novela
    }

    try:
        # Título - Basado en el documento adjunto
        titulo_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article#novel h1.novel-title"))
        )
        datos_novela['titulo'] = titulo_element.text.strip()

        # Imagen - Basado en el documento adjunto
        try:
            img_element = driver.find_element(By.CSS_SELECTOR, ".fixed-img .cover img")
            datos_novela['imagen_url'] = img_element.get_attribute('src')
        except NoSuchElementException:
            logger.warning("Imagen de portada no encontrada.")

        # Autor e Ilustrador - Asumiendo una estructura similar o adaptada
        # El documento adjunto no muestra claramente estos campos en la sección de información,
        # pero podemos intentar buscarlos en un contenedor de información general.
        # Esta parte puede necesitar ajustes según la estructura real.
        try:
            info_div = driver.find_element(By.CSS_SELECTOR, ".novel-info") # Contenedor general de info
            # Intentar encontrar elementos específicos dentro de .novel-info
            # Esto es una suposición basada en estructuras comunes. 
            # Puede requerir inspección real de la página.
            autor_elements = info_div.find_elements(By.XPATH, ".//*[contains(text(), 'Author') or contains(text(), 'author')]/following-sibling::*")
            if autor_elements:
                # Toma el texto del primer elemento encontrado como autor
                datos_novela['autor'] = autor_elements[0].text.strip()
            # Similar para ilustrador si existe un marcador claro
            
        except NoSuchElementException:
            logger.info("Sección de información detallada no encontrada o incompleta.")

        # Estado - Asumiendo que sigue un patrón similar al código original
        # O buscando un elemento con texto "Status"
        try:
            estado_valor = driver.find_element(By.XPATH, '//*[@class="header-stats"]/span[2]/strong').text.strip()
            datos_novela['estado'] = estado_valor
        except NoSuchElementException:
            # Fallback: buscar un span con clase 'status' como en el código original
            try:
                estado_element_fallback = driver.find_element(By.CSS_SELECTOR, ".status")
                datos_novela['estado'] = estado_element_fallback.text.strip()
            except NoSuchElementException:
                logger.info("Estado no encontrado.")

        # Descripción/Sinopsis - Basado en el documento adjunto
        try:
            datos_novela['descripcion'] = soup.find('div', class_='summary').find('div', class_='content').text.strip()
        except NoSuchElementException:
            logger.info("Descripción no encontrada.")
            datos_novela['descripcion'] = "N/A"
            
        # Géneros - Asumiendo una estructura de categorías o géneros
        # El documento adjunto no muestra esto claramente, se asume una estructura común
        try:
            generos_elements = driver.find_elements(By.CSS_SELECTOR, ".categories a, .genres a")
            datos_novela['generos'] = [elem.text.strip() for elem in generos_elements if elem.text.strip()]
        except NoSuchElementException:
            logger.info("Géneros no encontrados.")

    except TimeoutException:
        logger.error(f"Tiempo de espera agotado al cargar la novela: {url_novela}")
    except Exception as e:
        logger.error(f"Error al obtener datos de la novela {url_novela}: {e}")

    return datos_novela

# --- Función corregida para procesar capítulos con paginación AJAX ---
def procesar_capitulos(driver, url_novela):
    """
    Procesa la lista de capítulos de una novela basándose en la estructura HTML
    del documento adjunto (Pasted_Text_1753570645407.txt).
    Ahora maneja correctamente la paginación AJAX basada en data-ajax-update.
    """
    logger.info(f"Procesando capítulos de la novela: {url_novela}")
    capitulos = []
    
    # Asegurarse de que estamos en la pestaña de capítulos
    try:
        # Verificar si hay un botón o enlace específico para la pestaña de capítulos
        # y hacer clic si es necesario. Basado en: <a ... data-tab="chapters" ...>
        try:
            tab_chapters = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-tab='chapters']"))
            )
            # Solo hacer clic si no está ya activo (comprobación básica)
            if "_on" not in tab_chapters.get_attribute("class"):
                tab_chapters.click()
                time.sleep(1) # Breve pausa después del clic
        except TimeoutException:
            logger.info("Pestaña de capítulos no encontrada o ya activa.")

        # Esperar a que el contenedor de la lista de capítulos esté presente
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#chpagedlist"))
        )

        # Inicializar variables para el bucle de paginación
        pagina_actual = 1
        total_paginas_procesadas = 0
        max_paginas = 5000 # Límite de seguridad para evitar bucles infinitos

        while total_paginas_procesadas < max_paginas:
            logger.debug(f"Procesando página de capítulos {pagina_actual} (Intento de scraping #{total_paginas_procesadas + 1})")
            
            # Esperar a que el contenedor de capítulos/paginación esté presente
            try:
                chpagedlist_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#chpagedlist"))
                )
            except TimeoutException:
                logger.error("No se encontró el contenedor #chpagedlist. Posible error de carga o estructura inesperada.")
                break # Salir del bucle si no se puede encontrar el contenedor

            # Encontrar todos los elementos de capítulo *dentro* del contenedor actualizado
            # Seleccionar capítulos basados en el HTML proporcionado: <li><a href=...>
            elementos_capitulos = chpagedlist_container.find_elements(By.CSS_SELECTOR, "ul.chapter-list li a")

            if not elementos_capitulos:
                 logger.warning(f"No se encontraron capítulos en la página actual (intentos de scraping: {total_paginas_procesadas + 1}).")
                 # Intento alternativo: buscar enlaces directos de capítulos si la estructura es distinta
                 # Esto es un fallback genérico, adaptar según sea necesario
                 elementos_capitulos = chpagedlist_container.find_elements(By.CSS_SELECTOR, "a[href*='_']") 
                 if elementos_capitulos:
                     logger.info("Se encontraron enlaces de capítulos con selector alternativo.")

            logger.info(f"Se encontraron {len(elementos_capitulos)} capítulos en la página actual.")
            for elemento in elementos_capitulos:
                capitulo_info = {'titulo': 'N/A', 'url': 'N/A'}
                try:
                    # El texto del enlace es el título del capítulo (etiqueta <strong>)
                    strong_element = elemento.find_element(By.TAG_NAME, 'strong')
                    capitulo_info['titulo'] = strong_element.text.strip()
                    # La URL del capítulo es el href del enlace
                    capitulo_info['url'] = urljoin(url_novela, elemento.get_attribute('href'))
                    capitulos.append(capitulo_info)
                except Exception as e:
                    logger.warning(f"No se encontró el título o la URL del capítulo: {e}. Elemento: {elemento.get_attribute('outerHTML')[:100]}...")
                    # Intentar con el texto del enlace si no hay <strong>
                    try:
                        capitulo_info['titulo'] = elemento.text.strip()
                        capitulo_info['url'] = urljoin(url_novela, elemento.get_attribute('href'))
                        if capitulo_info['titulo'] != 'N/A': # Asegurarse que tiene título
                            capitulos.append(capitulo_info)
                    except:
                         logger.warning(f"Error adicional al intentar obtener título/URL alternativo.")
                         continue # Pasar al siguiente elemento

            # --- Manejo de Paginación de Capítulos AJAX ---
            # Buscar enlaces de paginación *dentro* del contenedor actualizado
            try:
                # Buscar enlaces de paginación AJAX dentro del contenedor #chpagedlist
                # Estos enlaces tienen data-ajax="true" y data-ajax-update="#chpagedlist"
                pagination_links = chpagedlist_container.find_elements(By.CSS_SELECTOR, ".pagination a[data-ajax='true'][data-ajax-update='#chpagedlist']")
                
                if not pagination_links:
                    logger.info("No se encontraron más enlaces de paginación AJAX. Finalizando.")
                    break # No hay más páginas
                
                # Buscar el enlace de "Siguiente" (>) o "Última" (>>) o el número de página siguiente
                next_page_link = None
                for link in pagination_links:
                    texto = link.text.strip()
                    if texto == '>': # Siguiente página
                        next_page_link = link
                        logger.debug("Encontrado enlace 'Siguiente' (>), procesando...")
                        break
                    elif texto == '>>': # Última página (opcional, puede seguir el bucle)
                        next_page_link = link
                        logger.debug("Encontrado enlace 'Última' (>>), procesando...")
                        break
                    # Opcional: Intentar encontrar el número de página siguiente al actual
                    # elif texto.isdigit() and int(texto) > pagina_actual:
                    #     next_page_link = link
                    #     pagina_actual = int(texto)
                    #     break
                
                if next_page_link:
                    logger.info(f"Navegando a la siguiente página de capítulos...")
                    # Obtener el atributo href para información (aunque no se use para navegar directamente)
                    href = next_page_link.get_attribute('href')
                    logger.debug(f"URL de paginación AJAX: {href}")
                    
                    # Hacer clic en el enlace AJAX
                    next_page_link.click()
                    
                    # Esperar a que el contenido del contenedor #chpagedlist se actualice
                    # WebDriverWait espera a que un elemento cambie su estado (por ejemplo, staleness)
                    # o que un nuevo elemento aparezca. Aquí, esperamos que el contenedor se actualice.
                    try:
                        # Opción 1: Esperar a que el contenedor existente se vuelva obsoleto (stale)
                        # WebDriverWait(driver, 10).until(EC.staleness_of(chpagedlist_container))
                        # Opción 2: Esperar a que un nuevo contenedor con el mismo selector esté presente
                        # (Esto puede no funcionar bien si el mismo elemento se actualiza en su lugar)
                        # Opción 3: Esperar un tiempo fijo después del clic, que es menos robusto pero a veces necesario
                        # time.sleep(2) 
                        # Opción 4: Esperar a que desaparezca un elemento que sabemos que debería desaparecer
                        # o que aparezca un indicador de carga (si lo hubiera)
                        # Opción 5: Volver a localizar el contenedor #chpagedlist después del clic
                        WebDriverWait(driver, 10).until(
                            lambda d: d.find_element(By.CSS_SELECTOR, "#chpagedlist")
                        )
                        # Opción 6: Esperar a que haya más capítulos o que la paginación haya cambiado
                        
                        # Pequeña pausa adicional para asegurar la carga completa del contenido AJAX
                        time.sleep(1.5) 
                        
                        total_paginas_procesadas += 1
                        # Incrementar pagina_actual solo si se está usando la lógica de número de página
                        # pagina_actual += 1 
                        
                    except TimeoutException:
                        logger.warning("Tiempo de espera agotado esperando la actualización del contenedor de capítulos AJAX.")
                        # Opcional: Intentar continuar si hay nuevos capítulos visibles
                        # break # Si se quiere detener en caso de error de carga
                        
                else:
                    logger.info("No se encontró un enlace de página siguiente válido. Finalizando.")
                    break # No hay más páginas para hacer clic

            except NoSuchElementException:
                logger.info("No se encontró paginación de capítulos AJAX o se terminaron las páginas.")
                break # Salir del bucle si no hay paginación
            except Exception as e:
                logger.error(f"Error al manejar la paginación de capítulos AJAX: {e}")
                break # Salir del bucle en caso de error inesperado

    except TimeoutException:
        logger.error(f"Tiempo de espera agotado al cargar los capítulos de: {url_novela}")
    except Exception as e:
        logger.error(f"Error al procesar capítulos de {url_novela}: {e}")

    logger.info(f"Total de capítulos encontrados: {len(capitulos)}")
    return capitulos

# --- Nueva clase para el scraping automático ---
class FanmtlScraperAutomatico:
    def __init__(self, driver, page_pubsub, existing_novels):
        """
        Inicializa el scraper automático de Fanmtl.

        Args:
            driver: Instancia del WebDriver de Selenium.
            page_pubsub: Objeto pubsub de Flet para enviar mensajes a la UI.
            existing_novels (dict): Diccionario de novelas existentes en la BD.
        """
        self.driver = driver
        self.page_pubsub = page_pubsub
        self.existing_novels = existing_novels
        self.base_url = "https://www.fanmtl.com" # Corregido: Quitado espacio al final
        self.list_url = f"{self.base_url}/list/all/all-onclick-0.html"
        self.current_page = 1
        # Lista de géneros a excluir
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
            logger.error("Tiempo de espera agotado al buscar la paginación.")
            return 1
        except Exception as e:
            logger.error(f"Error al obtener el total de páginas: {e}")
            return 1

    def scrape_novels_from_page(self):
        """
        Recopila la información básica de las novelas de la página actual.
        Retorna una lista de URLs de novelas.
        """
        novel_urls = []
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".novel-list.grid"))
            )
            
            novel_items = self.driver.find_elements(By.CSS_SELECTOR, ".novel-item")
            
            if not novel_items:
                logger.warning(f"No se encontraron novelas en la página {self.current_page}.")
                return novel_urls

            logger.info(f"Encontradas {len(novel_items)} novelas en la página {self.current_page}.")

            for item in novel_items:
                try:
                    title_element = item.find_element(By.CSS_SELECTOR, ".novel-title")
                    relative_url = title_element.find_element(By.XPATH, "./..").get_attribute('href')
                    full_url = f"{relative_url}" #{self.base_url}
                    novel_urls.append(full_url)
                    logger.debug(f"URL de novela encontrada: {full_url}")

                except Exception as e:
                    logger.error(f"Error al extraer URL de una novela en la página {self.current_page}: {e}")
                    continue

        except TimeoutException:
            logger.error(f"Tiempo de espera agotado al cargar la lista de novelas en la página {self.current_page}.")
        except Exception as e:
            logger.error(f"Error general al raspar la página {self.current_page}: {e}")
        return novel_urls

    def scrape_all_novels_automatic(self):
        """
        Orquesta el proceso completo de scraping automático.
        """
        self.page_pubsub.send_all({
            "status": "Iniciando scraping automático de todas las novelas...",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })
        
        # 1. Abrir la URL inicial
        logger.info(f"Abriendo la URL: {self.list_url}")
        self.page_pubsub.send_all({
            "status": f"Abriendo la URL: {self.list_url}",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })
        self.driver.get(self.list_url)

        # 2. Obtener el número total de páginas
        total_pages = self.get_total_pages()
        logger.info(f"Proceso de scraping iniciado para {total_pages} páginas.")
        self.page_pubsub.send_all({
            "status": f"Se encontraron {total_pages} páginas de novelas.",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })

        # Lista para almacenar todas las URLs de novelas
        try:
            all_novel_urls = pd.read_csv('all_novel_fanmtl_urls.csv')['url'].tolist()
        except:
            all_novel_urls = []
        
        urls_novelas = obtener_novelas_url_existentes()
        
        if not all_novel_urls:
            # 3. Bucle para recorrer las páginas de la lista
            for page in range(total_pages):
                self.current_page = page + 1
                logger.info(f"--- Procesando página {self.current_page} de {total_pages} ---")
                self.page_pubsub.send_all({
                    "status": f"Procesando página {self.current_page} de {total_pages}...",
                    "color": ft.Colors.BLUE_600,
                    "progress": True
                })
                
                # a. Recopilar URLs de novelas en la página actual
                urls_from_page = self.scrape_novels_from_page()
                all_novel_urls.extend(urls_from_page)
                
                # b. Si no es la última página, navegar a la siguiente
                if page + 1 < total_pages:
                    next_page_url = f"{self.base_url}/list/all/all-onclick-{page + 1}.html"
                    logger.info(f"Navegando a: {next_page_url}")
                    self.page_pubsub.send_all({
                        "status": f"Navegando a la página {page + 2}...",
                        "color": ft.Colors.BLUE_600,
                        "progress": True
                    })
                    self.driver.get(next_page_url)
                    time.sleep(2) # Espera para cargar la nueva página
                    
        pd.DataFrame(all_novel_urls, columns=['url']).to_csv('all_novel_fanmtl_urls.csv', index=False)
        logger.info(f"Recopilación de URLs completada. Total de novelas encontradas: {len(all_novel_urls)}")
        self.page_pubsub.send_all({
            "status": f"Recopilación de URLs completada. Total de novelas encontradas: {len(all_novel_urls)}. Iniciando procesamiento detallado...",
            "color": ft.Colors.BLUE_600,
            "progress": True
        })
        
        # 4. Ahora, recorrer cada URL de novela obtenida y aplicar las funciones originales
        total_novels = len(all_novel_urls)
        processed_count = 0
        for i, novel_url in enumerate(all_novel_urls):
            processed_count += 1
            if novel_url not in urls_novelas:
                logger.info(f"({processed_count}/{total_novels}) Procesando novela individual: {novel_url}")
                self.page_pubsub.send_all({
                    "status": f"({processed_count}/{total_novels}) Procesando novela: {novel_url}",
                    "color": ft.Colors.BLUE_600,
                    "progress": True
                })
                
                self.driver.get(novel_url)
                time.sleep(2) # Espera para que cargue la página
                
                try:
                    # --- Llamar a las funciones del código original ---
                    datos_detalle = obtener_datos_novela(self.driver, novel_url)
                    # La lista de géneros de tu novela
                    generos_novela = set(datos_detalle['generos'])
                    if self.generos_excluidos.isdisjoint(generos_novela):
                        datos_capitulos = procesar_capitulos(self.driver, novel_url) # Usar la función corregida
                        
                        # --- Lógica de envío de datos a MongoDB ---
                        novel_name = datos_detalle['titulo'].upper()
                        
                        if novel_name in self.existing_novels:
                            novel_id = self.existing_novels[novel_name]
                            urls_novelas.add(novel_url)
                            logger.info(f"Novela '{novel_name}' ya existe en la base de datos (ID: {novel_id}).")
                            self.page_pubsub.send_all({
                                "status": f"Novela '{novel_name[:50]}...' ya existe. Verificando capítulos...",
                                "color": ft.Colors.ORANGE_600,
                                "progress": True
                            })
                        else:
                            # Preparar documento para MongoDB usando la estructura del código de envío
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
                            self.existing_novels[novel_name] = novel_id
                            logger.info(f"Nueva novela '{novel_name}' registrada en la base de datos (ID: {novel_id}).")
                            self.page_pubsub.send_all({
                                "status": f"Nova novela '{novel_name[:50]}...' registrada. Procesando capítulos...",
                                "color": ft.Colors.GREEN_600,
                                "progress": True
                            })

                        # Procesar y guardar capítulos
                        existing_chapters_set = obtener_capitulos_existentes(novel_id)
                        chapters_to_insert = []
                        
                        for idx, cap_info in enumerate(datos_capitulos):
                            nombre_capitulo = cap_info.get('titulo', '').strip()
                            if nombre_capitulo and nombre_capitulo not in existing_chapters_set:
                                chapters_to_insert.append({
                                    "novela_id": novel_id,
                                    "nombre": nombre_capitulo,
                                    "url": cap_info.get('url', ''),
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
        
        logger.info("Proceso de scraping automático completado.")
        self.page_pubsub.send_all({
            "status": "Proceso de scraping automático completado exitosamente!",
            "color": ft.Colors.GREEN_600,
            "progress": False
        })

# --- Función principal de Flet ---
def main(page: ft.Page):
    page.title = "Fanmtl Scraper Automático"
    page.window_width = 600
    page.window_height = 400
    page.scroll = ft.ScrollMode.AUTO

    # Elementos de la UI
    url_input = ft.TextField(
        label="URL de la novela (opcional para scraping automático)",
        width=500,
        disabled=True
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
                # Se puede reutilizar la lógica de configuración del código original
                options = webdriver.ChromeOptions()
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
                # options.add_argument('--headless') # Puedes descomentar esta línea para ejecutar en modo headless
                
                # driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
                driver = uc.Chrome(options=options, service=Service(ChromeDriverManager().install()))
                driver_instance[0] = driver # Guardar referencia
                
                # Crear instancia del scraper automático
                scraper = FanmtlScraperAutomatico(driver, page.pubsub, existing_novels)
                
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
                ft.Text("Fanmtl Scraper Automático", size=20, weight=ft.FontWeight.BOLD),
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