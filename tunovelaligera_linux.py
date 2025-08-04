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
from webdriver_manager.chrome import ChromeDriverManager
import translators as ts
import undetected_chromedriver as uc
import threading
from bson.objectid import ObjectId
import re

# Configuración inicial
DetectorFactory.seed = 0
MONGO_URI = 'mongodb://192.168.1.11:27017/'
DB_NAME = 'recopilarnovelas'
SITIO_ID = '680ecb15e1ce8081ecb8b4d1'
chapters_to_insert = []

# Cliente MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coleccion_app_sitio = db['app_sitio']
coleccion_app_novela = db['app_novela']
coleccion_app_capitulo = db['app_capitulo']

# Paleta de colores
COLOR_PRIMARY = "#6200EE"
COLOR_SECONDARY = "#03DAC6"
COLOR_BACKGROUND = "#FFFFFF"
COLOR_ERROR = "#B00020"

def traducir(texto: str) -> str:
    """Traduce texto usando múltiples servicios de traducción"""
    translators = [
        ('bing', lambda t: ts.translate_text(t, translator='bing', to_language='es')),
        ('google', lambda t: ts.translate_text(t, translator='google', to_language='es')),
        ('google_new', lambda t: google_translator().translate(t, lang_tgt='es'))
    ]
    
    for name, func in translators:
        try:
            return func(texto)
        except Exception as e:
            print(f"Fallo en {name}: {e}")
            continue
    return texto

def obtener_novelas_existentes() -> Dict[str, str]:
    """Obtiene un diccionario de novelas existentes {nombre: id}"""
    return {
        novela['nombre']: str(novela['_id'])
        for novela in coleccion_app_novela.find(
            {'sitio_id': SITIO_ID},
            {'nombre': 1}
        )
    }

def obtener_capitulos_existentes(novel_id: str) -> set:
    """Obtiene conjunto de nombres de capítulos existentes"""
    return {
        str(cap['nombre']).strip()
        for cap in coleccion_app_capitulo.find(
            {'novela_id': novel_id},
            {'nombre': 1}
        )
    }


def procesar_toda_las_novelas(page: ft.Page):
    sitio = coleccion_app_sitio.find_one({'_id':ObjectId(SITIO_ID)})
    try:
        existing_novels = obtener_novelas_existentes()
        
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        
        driver = uc.Chrome(options=options, service=Service(ChromeDriverManager().install()))
        
        driver.get(f"{sitio['url']}novelas/?m_orderby=rating")
        
        time.sleep(1)
        mostrar_mas = True
        while mostrar_mas:
            driver.find_element(By.CSS_SELECTOR, "nav.navigation-ajax").find_element(By.TAG_NAME,"a").click()
            time.sleep(2)
            if len(driver.find_elements(By.CSS_SELECTOR, "nav.navigation-ajax[style*='display: none']")) > 0:
                mostrar_mas = False
            break
        listado = BeautifulSoup(driver.page_source, 'html.parser').find_all("div", class_="page-listing-item")
        for fila in listado:
            for item in fila.find_all("div",class_="item-summary"):
                url = item.find("h3", class_="h5").find("a").get("href")
                url = '/'.join(url.split('/')[0:-1])
                novel_data = obtener_datos_novela(driver, url)
                novel_name = novel_data['nombre']

                if novel_name in existing_novels:
                    novel_id = existing_novels[novel_name]
                else:
                    novel_id = str(coleccion_app_novela.insert_one(novel_data).inserted_id)
                    existing_novels[novel_name] = novel_id
                
                # existing_chapters = obtener_capitulos_existentes(novel_id)
                # procesar_capitulos(driver, novel_id, existing_chapters)
        
        driver.quit()
        
    except Exception as e:
        page.pubsub.send_all({
            "status": f"Error: {str(e)}",
            "color": COLOR_ERROR,
            "progress": False
        })


def obtener_datos_novela(driver: webdriver.Chrome, url: str) -> dict:
    """Extrae datos de la novela desde la URL"""
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    info = soup.find('div', class_='profile-manga')
    
    post_status = info.find('div', class_='post-status').find_all('div', class_='post-content_item')
    status = 'emision'
    for item in post_status:
        if item.find('div', class_='summary-heading').text.upper().strip() == 'ESTADO':
            status = 'emision' if item.find('div', class_='summary-content').text.upper().strip() == 'ONGOING' else 'completo'
    
    return {
        "sitio_id": SITIO_ID,
        "nombre": info.find('div', class_='post-title').find('h1').text.strip().upper(),
        "sinopsis": ' '.join([x.text.strip() for x in soup.find('div', class_='description-summary').find_all('p')]),
        "autor": info.find('div', class_='author-content').text.strip() if info.find('div', class_='author-content') else '',
        "genero": ', '.join(
            cat.text.strip() 
            for cat in info.find('div', class_='genres-content').find_all('a')
        ),
        "status": status,
        "url": url,
        "imagen_url": f"{soup.find('div', class_='summary_image').find('a').img['src']}",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

def procesar_capitulos(url_input: str, driver: webdriver.Chrome, novel_id: str, existing_chapters: set):
    """Procesa y guarda los capítulos no existentes"""
    global chapters_to_insert
    chapters_to_insert = []
    # Obtener HTML inicial
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Manejo más robusto de la paginación
    paginator = soup.find('ul', id=re.compile(r'lcp_paginator'))
    total_pagination = 0
    
    if paginator:
        page_links = paginator.find_all('li')
        if page_links:
            last_page = page_links[-1]
            if last_page.text.strip().isdigit():
                total_pagination = int(last_page.text.strip())
            elif len(page_links) > 1 and page_links[-2].text.strip().isdigit():
                total_pagination = int(page_links[-2].text.strip())
    
    # Procesar la primera página
    process_page_chapters(soup, existing_chapters, novel_id)
    
    
    # Procesar páginas adicionales si existen
    if total_pagination > 1:
        for pagina in range(2, total_pagination + 1):
            try:
                
                # # Encontrar y hacer clic en el enlace de paginación
                # paginator = driver.find_element(By.CSS_SELECTOR, f"ul[id^='lcp_paginator'] li a[href*='page0={pagina}']")
                # paginator.click()
                driver.get(f"{url_input}?lcp_page0={pagina}")
                time.sleep(10)  # Esperar a que cargue la nueva página
                
                # Procesar la nueva página
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                process_page_chapters(soup, existing_chapters, novel_id)
                
            except Exception as e:
                print(f"Error al procesar página {pagina}: {str(e)}")
                break
    
    # Insertar capítulos si los hay
    if chapters_to_insert:
        chapters_to_insert=chapters_to_insert[::-1]
        fecha = datetime.now()
        for idx,cap in enumerate(chapters_to_insert):
            cap['created_at'] = fecha
            cap['updated_at'] = fecha
            chapters_to_insert[idx] = cap
            fecha += timedelta(seconds=1)
        coleccion_app_capitulo.insert_many(chapters_to_insert)
    
    # page = 2
    
    # for pag in range(page, total_pagination):
    #     soup = BeautifulSoup(driver.page_source, 'html.parser')
    #     chapters = soup.find('div', class_='description-summary').find('ul', class_=re.compile(r'^lcp_catlist\w+')).find('ul', id=re.compile(r'^lcp_instance\w+')).find_all('a')
        
    #     for chapter in chapters:
    #         nombre = chapter.text.strip()
    #         if nombre not in existing_chapters:
    #             chapters_to_insert.append({
    #                 "novela_id": novel_id,
    #                 "nombre": nombre,
    #                 "url": f"{chapter.get('href')}",
    #                 "created_at": datetime.now(),
    #                 "updated_at": datetime.now()
    #             })
        
    #     li_elements = driver.find_element(By.CLASS_NAME, re.compile(r'^lcp_catlist\w+')).find_element(By.ID, re.compile(r'^lcp_paginator_\w+')).find_elements(By.TAG_NAME, 'li')
    #     for li in li_elements:
    #         if str(li.text).isdigit():
    #             if int(li.text)==pag:
    #                 li.find_element(By.TAG_NAME,'a').click()
    #                 break
    #     time.sleep(2)
    
    # if chapters_to_insert:
    #     coleccion_app_capitulo.insert_many(chapters_to_insert)


def process_page_chapters(soup, existing_chapters, novel_id):
    global chapters_to_insert
    # Versión más flexible para encontrar capítulos
    chapters_container = soup.find('div', class_='description-summary')
    if not chapters_container:
        return
    
    # Buscar listas de capítulos con diferentes patrones
    chapters_list = chapters_container.find('ul', class_=re.compile(r'lcp_catlist'))
    try:
        chapters_list = chapters_list.find('ul', id=re.compile(r'lcp_instance'))
    except Exception as error:
        print(error)
    
    if chapters_list:
        chapters = chapters_list.find_all('a', href=True)
        for chapter in chapters:
            nombre = chapter.text.strip()
            if nombre and nombre not in existing_chapters:
                chapters_to_insert.append({
                    "novela_id": novel_id,
                    "nombre": nombre,
                    "url": chapter.get('href', '').strip()
                })


def main(page: ft.Page):
    page.title = "TuNovelaLigera Novel Scraper"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_BACKGROUND
    page.padding = 20
    page.spacing = 20
    page.window_width = 600
    page.window_height = 400
    page.window_resizable = False

    # UI Components
    url_input = ft.TextField(
        label="URL de la novela",
        hint_text="Ingrese la URL de tunovelaliegra.com",
        border_color=COLOR_PRIMARY,
        focused_border_color=COLOR_SECONDARY,
        width=500
    )
    
    status_text = ft.Text(
        "",
        color=COLOR_ERROR,
        visible=False,
        size=14
    )
    
    progress_ring = ft.ProgressRing(
        visible=False,
        width=24,
        height=24,
        color=COLOR_PRIMARY
    )
    
    def start_scraping(e):
        def run_scraping():
            url = url_input.value.strip()
            
            if not url.startswith("https://tunovelaligera.com/"):
                page.pubsub.send_all({
                    "status": "URL inválida. Debe comenzar con https://tunovelaligera.com/",
                    "color": COLOR_ERROR,
                    "progress": False
                })
                return
            
            try:
                page.pubsub.send_all({
                    "status": "Iniciando proceso...",
                    "color": ft.Colors.BLUE_600,
                    "progress": True
                })
                
                existing_novels = obtener_novelas_existentes()
                
                options = webdriver.ChromeOptions()
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
                # options.add_argument('--headless')
                
                driver = uc.Chrome(options=options, service=Service(ChromeDriverManager().install()))
                
                novel_data = obtener_datos_novela(driver, url)
                novel_name = novel_data['nombre']
                
                if novel_name in existing_novels:
                    novel_id = existing_novels[novel_name]
                    page.pubsub.send_all({
                        "status": "Novela existente encontrada. Verificando capítulos...",
                        "color": ft.Colors.BLUE_600,
                        "progress": True
                    })
                else:
                    novel_id = str(coleccion_app_novela.insert_one(novel_data).inserted_id)
                    existing_novels[novel_name] = novel_id
                    page.pubsub.send_all({
                        "status": "Nueva novela registrada. Procesando capítulos...",
                        "color": ft.Colors.BLUE_600,
                        "progress": True
                    })
                
                existing_chapters = obtener_capitulos_existentes(novel_id)
                procesar_capitulos(url_input.value, driver, novel_id, existing_chapters)
                
                page.pubsub.send_all({
                    "status": "Proceso completado exitosamente!",
                    "color": ft.Colors.GREEN_600,
                    "progress": False
                })
                driver.quit()
                
            except Exception as e:
                page.pubsub.send_all({
                    "status": f"Error: {str(e)}",
                    "color": COLOR_ERROR,
                    "progress": False
                })
        
        # Configurar actualizaciones de UI
        def on_message(msg):
            status_text.value = msg["status"]
            status_text.color = msg["color"]
            progress_ring.visible = msg["progress"]
            page.update()
            
        page.pubsub.subscribe(on_message)
        threading.Thread(target=run_scraping, daemon=True).start()

    start_button = ft.ElevatedButton(
        "Iniciar Scraping",
        bgcolor=COLOR_PRIMARY,
        color=COLOR_BACKGROUND,
        on_click=start_scraping
    )
    
    massive_start_button = ft.ElevatedButton(
        "Iniciar Scraping de Todas las Novelas",
        bgcolor=ft.Colors.GREEN_500,
        color=ft.Colors.BLACK,
        visible=False,
        on_click=lambda e, page=page: procesar_toda_las_novelas(page)
    )
    
    # Layout
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Column([
                        url_input,
                        ft.Row([start_button, massive_start_button, progress_ring], alignment=ft.MainAxisAlignment.CENTER),
                        status_text
                    ]),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

if __name__ == "__main__":
    ft.app(target=main)


































# import os
# import glob
# from bs4 import BeautifulSoup as bs
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# import csv
# from googletrans import Translator
# # binary = FirefoxBinary(r'C:\Program Files\Mozilla Firefox\firefox.exe')
# from webdriver_manager.firefox import GeckoDriverManager
# from ebooklib import epub
# import time
# from urllib.parse import urlparse
# from icrawler.builtin import GoogleImageCrawler
# import translators as ts
# import undetected_chromedriver as uc

# valcharacter = ' 0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúäëïöü'
# item = 0
# titulo = ''
# tituloen = ''
# cantidadcaptitulo = 0
# listaCapitulos = []
# autor = ''
# descripcion = ''
# opciones = Options()
# opciones.headless = True
# # servicio=Service('/home/dvitev/chromedriver_linux64/chromedriver')
# # servicio = Service(ChromeDriverManager().install())
# path = os.getcwd()


# # servicio = Service('usr/bin/chromium-browser')
# # Servicio = Service('usr/bin/chromedriver')

# def quitar_simbolos_especiales(title):
#     titlenew = ''
#     for j in range(len(title)):
#         if title[j] in valcharacter:
#             titlenew += title[j]
#     return titlenew


# def escribirtablecontents(titulo0, datos):
#     df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
#     df.to_csv(os.path.join(path, 'tableofcontents', titulo0 + '_tablecontents.csv'),
#               sep=';',
#               quotechar='"',
#               quoting=csv.QUOTE_NONNUMERIC,
#               index=False)


# def escribircapitulotable(titulo, datos2):
#     df2 = pd.DataFrame(data=datos2, columns=['nombrecap', 'texto'])
#     df2.to_csv(os.path.join(path, 'chapters', titulo + '.csv'),
#                sep=';',
#                quotechar='"',
#                quoting=csv.QUOTE_NONNUMERIC,
#                index=False)


# def inicio(ini):
#     num = 100
#     return (ini * num) + (num * (ini - 2))


# def fin(ini):
#     num = 200
#     return (ini * num) - 1


# def obtenernumpagurl(url):
#     global item
#     global descripcion
#     global titulo
#     global autor
#     global opciones
#     descripcion = ''
#     a = ''
#     # print(url)
#     op = webdriver.ChromeOptions()
#     op.headless = True
#     # driver = uc.Chrome(use_subprocess=True, service=servicio)
#     driver = webdriver.Chrome(options=op)
#     driver.minimize_window()
#     driver.get(url)
#     html = driver.page_source
#     soup = bs(html, 'html.parser')
#     driver.close()
#     tit = soup.find_all(class_='titulo-novela')
#     titulo = quitar_simbolos_especiales(str(tit[0].string).strip())
#     print(titulo)
#     aut = soup.find_all(class_='author-content')
#     autor = aut[0].string
#     descrip = soup.find_all(class_='summary__content')
#     descripp = descrip[0].find_all('p')
#     for i in range(len(descripp)):
#         if str(descripp[i].string) == 'None':
#             break
#         elif 'javascript' in descripp[i].string:
#             break
#         else:
#             descripcion += descripp[i].string
#     lcp_paginator = soup.find_all(class_='lcp_paginator')
#     try:
#         lcp_paginator_li = lcp_paginator[0].find_all('li')
#         # print(lcp_paginator_li[-2].string)
#         return lcp_paginator_li[-2].string
#     except:
#         return 1


# def obtenertablecontents(url):
#     global listaCapitulos
#     global opciones
#     datos = []
#     op = webdriver.ChromeOptions()
#     op.headless = True
#     # driver = uc.Chrome(use_subprocess=True, service=servicio)
#     driver = webdriver.Chrome(options=op)
#     driver.minimize_window()
#     driver.get(url)
#     html = driver.page_source
#     soup = bs(html, 'html.parser')
#     driver.close()
#     lcp_catlist = soup.find_all(class_='lcp_catlist')
#     lcp_catlist_a = lcp_catlist[0].find_all('a')
#     for i in range((len(lcp_catlist_a) - 1), -1, -1):
#         listaCapitulos.append([lcp_catlist_a[i].string, str(lcp_catlist_a[i].get('href'))])


# def obtenercapitulotable(limite, listacap):
#     global opciones
#     datos2 = []
#     limitecap = len(listacap['nombrecap'])
#     x = inicio(limite)
#     y = fin(limite)

#     if y >= limitecap:
#         y = limitecap

#     if len(str(x + 1)) == 1:
#         inin = ('0' * (len(str(limitecap)) - 1)) + str(x + 1)
#     elif len(str(x + 1)) == 2:
#         inin = ('0' * (len(str(limitecap)) - 2)) + str(x + 1)
#     elif len(str(x + 1)) == 3:
#         inin = ('0' * (len(str(limitecap)) - 3)) + str(x + 1)
#     elif len(str(x + 1)) == 4:
#         inin = ('0' * (len(str(limitecap)) - 4)) + str(x + 1)
#     elif len(str(x + 1)) == 5:
#         inin = ('0' * (len(str(limitecap)) - 5)) + str(x + 1)

#     if len(str(y + 1)) == 1:
#         finn = ('0' * (len(str(limitecap)) - 1)) + str(y + 1)
#     if len(str(y + 1)) == 2:
#         finn = ('0' * (len(str(limitecap)) - 2)) + str(y + 1)
#     if len(str(y + 1)) == 3:
#         finn = ('0' * (len(str(limitecap)) - 3)) + str(y + 1)
#     if len(str(y + 1)) == 4:
#         finn = ('0' * (len(str(limitecap)) - 4)) + str(y + 1)
#     if len(str(y + 1)) == 5:
#         finn = ('0' * (len(str(limitecap)) - 5)) + str(y + 1)
#     # print(x,y,inin,finn)
#     print((titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn + '.csv'))

#     if (titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn + '.csv') not in os.listdir(
#             os.path.join(path, 'chapters')):
#         if x < limitecap:
#             # print(x,y,inin,finn)
#             for i in range(x, y + 1):
#                 if i < limitecap:
#                     txt = ''
#                     print(listacap['nombrecap'][i], listacap['urlcap'][i])
#                     op = webdriver.ChromeOptions()
#                     op.headless = True
#                     # driver = uc.Chrome(use_subprocess=True, service=servicio)
#                     driver = webdriver.Chrome(options=op)
#                     driver.minimize_window()
#                     driver.get(listacap['urlcap'][i])
#                     html = driver.page_source
#                     soup = bs(html, 'html.parser')
#                     driver.close()
#                     p_chapter_c = soup.find_all('p')
#                     # print(len(p_chapter_c))
#                     for j in range(len(p_chapter_c)):
#                         if str(p_chapter_c[j].get_text()).strip() != 'None':
#                             if 'tunovelaligera' not in str(p_chapter_c[j].get_text()).strip():
#                                 if 'Notifications' not in str(p_chapter_c[j].get_text()).strip():
#                                     if 'TNL' not in str(p_chapter_c[j].get_text()).strip():
#                                         txt += str(p_chapter_c[j].get_text()).strip() + ' <br> '
#                         # print(str(p_chapter_c[i].string).strip())
#                     # print(txt)
#                     datos2.append([listacap['nombrecap'][i], txt])
#             escribircapitulotable(titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn, datos2)
#         return 'True'
#     else:
#         return 'False'


# def crearepub():
#     global titulo
#     global autor
#     global descripcion
#     global ext
#     listaarchivos = sorted(os.listdir(path))
#     total1 = len(listaarchivos)
#     # print(path)
#     file_newname_newfile = ''
#     if titulo.lower().replace(' ', '_') not in os.listdir(os.path.join(path, 'images')):
#         ext = '.jpg'
#         google_crawler = GoogleImageCrawler()
#         # filters = dict(size='small')
#         google_crawler.crawl(keyword=titulo, max_num=1)
#         time.sleep(5)
#         listaarchivos2 = sorted(os.listdir(os.path.join(path, 'images')))
#         for k in range(len(listaarchivos2)):
#             if '000001' in listaarchivos2[k]:
#                 ext = listaarchivos2[k][-4:]
#                 # print(ext,listaarchivos2[k])
#                 file_oldname = os.path.join(path, 'images', ('000001' + ext))
#                 file_newname_newfile = os.path.join(path, 'images', titulo.lower().replace(' ', '_') + ext)
#                 os.rename(file_oldname, file_newname_newfile)
#     else:
#         file_newname_newfile = titulo.lower().replace(' ', '_') + ext
#         print(titulo.lower().replace(' ', '_') + ext)

#     book = epub.EpubBook()
#     # set metadata
#     book.set_identifier('id123456')
#     if os.path.isfile(os.path.join(path, 'images', (titulo.lower().replace(' ', '_') + ext))):
#         book.set_cover('cover.jpg',
#                        open((os.path.join(path, 'images', (titulo.lower().replace(' ', '_') + ext))),
#                             'rb').read())
#     book.set_title(titulo)
#     book.set_language('es')
#     book.add_author(autor)

#     dfs = []
#     cs = ()
#     if titulo.lower().replace(' ', '_') + '.epub' not in os.listdir(os.path.join(path, 'epub')):
#         # chapters_csv = [match for match in os.listdir(os.path.join(path, 'chapters')) if
#         #                 titulo.lower().replace(' ', '_') in match]
#         chapters_csv = sorted(glob.glob(os.path.join(path, 'chapters', titulo.lower().replace(' ', '_') + '*')))
#         for chap_csv in chapters_csv:
#             dfs.append(pd.read_csv(os.path.join(path, 'chapters', chap_csv),
#                                    sep=';',
#                                    quotechar='"'))
#         dFrame = pd.concat(dfs, ignore_index=True)
#         dFrame.to_csv(os.path.join(path, 'completes', titulo.lower().replace(' ', '_') + '_complete.csv'),
#                       sep=';',
#                       quotechar='"',
#                       quoting=csv.QUOTE_NONNUMERIC,
#                       index=False)
#         limitecap = len(dFrame['nombrecap'])
#         c = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='es')
#         c.content = u'<h1>%s</h1>' \
#                     u'<p>%s</p>' \
#                     u'<br>' \
#                     u'<img src="%s" width="200" height="200">' % (titulo,
#                                                                   descripcion,
#                                                                   os.path.join(path, 'images', file_newname_newfile))
#         # add chapter
#         book.add_item(c)
#         for i in range(limitecap):
#             # print(dFrame['nombrecap'][i])
#             cp = ''
#             if len(str(i)) == 1:
#                 cp = ('0' * (len(str(limitecap)) - 1)) + str(i + 1)
#             elif len(str(i)) == 2:
#                 cp = ('0' * (len(str(limitecap)) - 2)) + str(i + 1)
#             elif len(str(i)) == 3:
#                 cp = ('0' * (len(str(limitecap)) - 3)) + str(i + 1)
#             elif len(str(i)) == 4:
#                 cp = ('0' * (len(str(limitecap)) - 4)) + str(i + 1)
#             elif len(str(i)) == 5:
#                 cp = ('0' * (len(str(limitecap)) - 5)) + str(i + 1)
#             print(i, str(dFrame['nombrecap'][i]))
#             c = epub.EpubHtml(title=str(dFrame['nombrecap'][i]), file_name='chap_' + cp + '.xhtml', lang='es')
#             c.content = u'<h1>%s</h1><p>%s</p>' % (str(dFrame['nombrecap'][i]), str(dFrame['texto'][i]))
#             # add chapter
#             book.add_item(c)
#             cs += (c,)
#         book.toc = (
#             epub.Link('intro.xhtml', 'Introduction', 'intro'),
#             (
#                 epub.Section('Introduction', 'intro.xhtml'),
#                 (cs)
#             )
#         )

#         # add default NCX and Nav file
#         book.add_item(epub.EpubNcx())
#         book.add_item(epub.EpubNav())

#         # define CSS style
#         style = 'BODY {color: white;}'
#         nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

#         # add CSS file
#         book.add_item(nav_css)

#         # basic spine
#         sp = []
#         sp.append('nav')
#         for j in cs:
#             sp.append(j)
#         # print(sp)
#         book.spine = sp
#         # write to the file
#         epub.write_epub(os.path.join(path, 'epub', titulo.lower().replace(' ', '_') + '.epub'), book, {})
#         # print(dFrame)
#         print('archivo epub de ', titulo, ' creado')
#         titulo = ''
#         autor = ''
#         descripcion = ''


# # links = ['https://tunovelaligera.com/novelas/emperors-domination-tnl/']
# links = [
#          # 'https://tunovelaligera.com/novelas/omniscient-readers-viewpoint/',
#          # 'https://tunovelaligera.com/novelas/i-shall-seal-the-heavens-cielos/',
#          # 'https://tunovelaligera.com/novelas/return-of-the-former-hero-tnl/',
#          # 'https://tunovelaligera.com/novelas/only-i-am-a-necromancer/',
#          # 'https://tunovelaligera.com/novelas/seoul-stations-necromancer/',
#          # 'https://tunovelaligera.com/novelas/una-estrella-renace-el-regreso-de-la-reina-alexa/',
#          # 'https://tunovelaligera.com/novelas/el-renacimiento-de-la-reina-del-apocalipsis-ponte-de-rodillas-joven-emperador/',
#          # 'https://tunovelaligera.com/novelas/responde-me-diosa-orgullosa/',
#          # 'https://tunovelaligera.com/novelas/la-maestra-de-los-elixires/',
#          # 'https://tunovelaligera.com/novelas/back-then-i-adored-you/',
#          # 'https://tunovelaligera.com/novelas/insanely-pampered-wife-divine-doctor-fifth-young-miss-tnla-3a/',
#          # 'https://tunovelaligera.com/novelas/trial-marriage-husband-need-to-work-hard/',
#          # 'https://tunovelaligera.com/novelas/ghost-emperor-wild-wife-dandy-eldest-miss-tnla/',
#          # 'https://tunovelaligera.com/novelas/a-billion-stars-cant-amount-to-you-mia/',
#          # 'https://tunovelaligera.com/novelas/the-99th-divorce-tnla/',
#          # 'https://tunovelaligera.com/novelas/evil-emperors-wild-consort-tnla/',
#          # 'https://tunovelaligera.com/novelas/the-demonic-king-chases-his-wife-the-rebellious-good-for-nothing-miss/',
#          # 'https://tunovelaligera.com/novelas/my-cold-and-elegant-ceo-wife-tns/',
#          # 'https://tunovelaligera.com/novelas/venerated-venomous-consort/',
#          # 'https://tunovelaligera.com/novelas/adorable-treasured-fox-divine-doctor-mother-overturning-the-heavens/',
#          # 'https://tunovelaligera.com/novelas/el-doctor-granjero-piadoso-un-marido-arrogante-que-no-se-puede-permitirse-ofender/',
#          # 'https://tunovelaligera.com/novelas/robando-tu-corazon/',
#          # 'https://tunovelaligera.com/novelas/cultivo-de-espiritus/',
#          # 'https://tunovelaligera.com/novelas/reverend-insanity-tnla-2/',
#          # 'https://tunovelaligera.com/novelas/the-good-for-nothing-seventh-young-lady/',
#          # 'https://tunovelaligera.com/novelas/wdqk-tnl/',
#          # 'https://tunovelaligera.com/novelas/the-death-mage/',
#          # 'https://tunovelaligera.com/novelas/gourmet-of-another-world-tnla-1/',
#          # 'https://tunovelaligera.com/novelas/reincarnation-of-the-strongest-sword-god-mia/',
#          # 'https://tunovelaligera.com/novelas/everyone-else-is-a-returnee/',
#          # 'https://tunovelaligera.com/novelas/death-march-tnl/',
#          # 'https://tunovelaligera.com/novelas/omniscient-readers-viewpoint/',
#          # 'https://tunovelaligera.com/novelas/superstars-of-tomorrow-tnla-2s/',
#          # 'https://tunovelaligera.com/novelas/genius-doctor-black-belly-miss-tnla/',
#          # 'https://tunovelaligera.com/novelas/el-divino-emperador-de-la-muerte/',
#          # 'https://tunovelaligera.com/novelas/cultivation-chat-group-tnla/',
#          # 'https://tunovelaligera.com/novelas/reincarnated-as-a-dragons-tnl/',
#          # 'https://tunovelaligera.com/novelas/the-legendary-mechanic-tnla/',
#          # 'https://tunovelaligera.com/novelas/kog-tnla/',
#          # 'https://tunovelaligera.com/novelas/ex-hero-candidates/',
#          # 'https://tunovelaligera.com/novelas/divine-doctor-daughter-of-the-first-wife/',
#          # 'https://tunovelaligera.com/novelas/poison-genius-consort/',
#          # 'https://tunovelaligera.com/novelas/prodigiously-amazing-weaponsmith-tnla/',
#          # 'https://tunovelaligera.com/novelas/omnipotent-sage/',
#          # 'https://tunovelaligera.com/novelas/the-record-of-unusual-creatures/',
#          # 'https://tunovelaligera.com/novelas/pmg-tnl/',
#          # 'https://tunovelaligera.com/novelas/nine-star-hegemon-body-art/',
#          # 'https://tunovelaligera.com/novelas/tempest-of-the-stellar-war-tnla-a/',
#          # 'https://tunovelaligera.com/novelas/doomsday-wonderland/',
#          # 'https://tunovelaligera.com/novelas/ultimate-scheming-system-tn/',
#          # 'https://tunovelaligera.com/novelas/versatile-mage/', 'https://tunovelaligera.com/novelas/nine-sun-god-king/',
#          # 'https://tunovelaligera.com/novelas/mga/',
#          # 'https://tunovelaligera.com/novelas/la-encantadora-de-la-medicina-con-el-nino-desafiante-del-cielo-y-el-padre-del-vientre-negro/',
#          # 'https://tunovelaligera.com/novelas/the-sage-who-transcended-samsara/',
#          # 'https://tunovelaligera.com/novelas/my-master-disconnected-yet-again/',
#          # 'https://tunovelaligera.com/novelas/la-consorte-venenosa-del-malvado-emperador/',
#          # 'https://tunovelaligera.com/novelas/the-monk-that-wanted-to-renounce-asceticism/',
#          # 'https://tunovelaligera.com/novelas/aun-asi-esperame/',
#          # 'https://tunovelaligera.com/novelas/mi-padre-es-el-principe-azul-de-la-galaxia-ta/',
#          # 'https://tunovelaligera.com/novelas/absolute-great-teacher/',
#          # 'https://tunovelaligera.com/novelas/everybody-is-kung-fu-fighting-while-i-started-a-farm/',
#          # 'https://tunovelaligera.com/novelas/bank-of-the-universe/',
#          # 'https://tunovelaligera.com/novelas/dual-cultivation-tns/',
#          # 'https://tunovelaligera.com/novelas/swallowed-star-tnla',
#          # 'https://tunovelaligera.com/novelas/emperors-domination-tnl/',
#          # 'https://tunovelaligera.com/novelas/bringing-the-farm-to-live-in-another-world/',
#          # 'https://tunovelaligera.com/novelas/my-disciple-died-yet-again/',
#          # 'https://tunovelaligera.com/novelas/sonomono-nochi-ni-tnl/',
#          # 'https://tunovelaligera.com/novelas/monarca-del-tiempo/',
#          # 'https://tunovelaligera.com/novelas/rebirth-of-the-urban-immortal-cultivator/',
#          # 'https://tunovelaligera.com/novelas/de-hecho-soy-un-gran-cultivador/',
#          # 'https://tunovelaligera.com/novelas/against-the-gods-tnl/',
#          # 'https://tunovelaligera.com/novelas/xian-ni-tnl/',
#          # 'https://tunovelaligera.com/novelas/god-and-devil-world-tnl/',
#          # 'https://tunovelaligera.com/novelas/martial-peak/',
#          # 'https://tunovelaligera.com/novelas/i-have-a-mansion-in-the-post-apocalyptic-world/',
#          # 'https://tunovelaligera.com/novelas/super-gene-tnla/',
#          # 'https://tunovelaligera.com/novelas/tsuki-ga-michibiku-isekai-douchuu-tnl/',
#     ]
# for link in links:
#     print(link)
#     listaCapitulos = []
#     numpag = int(obtenernumpagurl(str(link)))
#     urllist = []
#     if titulo.lower().replace(' ', '_') + '.epub' not in os.listdir(path + '/epub'):
#         if (titulo.lower().replace(' ', '_') + '_tablecontents.csv') not in os.listdir(
#                 os.path.join(path, 'tableofcontents')):
#             for i in range(numpag, 0, -1):
#                 obtenertablecontents(str(link) + '?lcp_page0=' + str(i))
#             # print(titulo, len(listaCapitulos))
#             escribirtablecontents(titulo.lower().replace(' ', '_'), listaCapitulos)
#             listacapnovel = pd.DataFrame(data=listaCapitulos, columns=['nombrecap', 'urlcap'])
#             print(listacapnovel)
#         else:
#             listacapnovel = pd.read_csv(os.path.join(
#                 path, 'tableofcontents', titulo.lower().replace(' ', '_') + '_tablecontents.csv'),
#                 sep=';',
#                 quotechar='"')
#             print(listacapnovel)
#         for i in range(int(len(listacapnovel['nombrecap']) / 200) + 1):
#             if obtenercapitulotable(i + 1, listacapnovel) == 'True':
#                 time.sleep(3)
#         crearepub()
#     item = 0
#     titulo = ''
#     cantidadcaptitulo = 0
#     listaCapitulos = []
#     autor = ''
#     descripcion = ''
