import datetime
import uuid
import os
from bs4 import BeautifulSoup as bs
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
from googletrans import Translator
from ebooklib import epub
import time
from urllib.parse import urlparse
from icrawler.builtin import GoogleImageCrawler
import os
import translators as ts
import asyncio
from zenrows import ZenRowsClient
import re
from fpdf import FPDF
import http.client
import json
from Proxy_List_Scrapper import Scrapper
import random

titulo = ''
tituloen = ''
titulo_datos = ''
tituloarchivo = ''
cantidadcaptitulo = 0
listaCapitulos = []
autor = ''
descripcion = ''
genero = []
ext = ''
page = ''
scrapper = Scrapper(category='GOOGLE', print_err_trace=False)
dataproxies = scrapper.getProxies()


class PDF(FPDF):
    # HTML2FPDF_CLASS = CustomHTML2FPDF
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")

    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        # Printing chapter name:
        self.cell(
            0,
            6,
            f"{label}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
            fill=True,
        )
        # Performing a line break:
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


async def traducir(texto):
    """
    Asynchronously translates the given text from English to Spanish using multiple translation services.

    Args:
        texto: The text to be translated.

    Returns:
        The translated text in Spanish.
    """
    contenido_p = ''

    while True:
        try:
            contenido_p = ts.translate_text(
                texto, translator='bing', from_language='en', to_language='es')
            break
        except Exception as e:
            print(e)
            try:
                contenido_p = ts.translate_text(
                    texto, translator='google', from_language='en', to_language='es')
                break
            except Exception as e:
                print(e)
                pass
            pass
    return contenido_p


def instanciar_driver():
    # return uc.Chrome()
    # index = random.randrange(0, dataproxies.len)
    # ipdata = dataproxies.proxies[index].ip
    # portdata = dataproxies.proxies[index].port
    ipdata = '127.0.0.1'
    portdata = '9150'
    print(
        f"{ipdata}:{portdata}")
    op = webdriver.FirefoxOptions()
    op.set_preference("network.proxy.type", 1)
    # op.set_preference(
    #     "network.proxy.http", f"{ipdata}")
    # op.set_preference("network.proxy.http_port",
    #                     portdata)
    op.set_preference('network.proxy.socks',
                        f"{ipdata}")
    op.set_preference('network.proxy.socks_port', portdata)
    op.set_preference('network.proxy.socks_remote_dns', False)
    # op.set_preference(
    #     "network.proxy.ssl", f"{ipdata}")
    # op.set_preference("network.proxy.ssl_port", portdata)
    # # Ejecutar en modo headless (sin ventana visible))
    # op.add_argument('--disable-gpu')  # Evitar errores en algunos sistemas
    # op.add_argument('--no-sandbox')  # Evitar errores en algunos sistemas
    # profile = webdriver.FirefoxProfile()
    # profile.set_preference('network.proxy.type', 1)
    # profile.set_preference('network.proxy.socks', '127.0.0.1')
    # profile.set_preference('network.proxy.socks_port', 9150)
    return webdriver.Firefox(options=op)


async def requestantibot(url):
    # client = ZenRowsClient("f39778c23487d8f83165a6742e6e9c90a3607d10")
    # # params = {"js_render": "true", "premium_proxy": "true"}
    # print(url)
    # response = client.get(url)
    # return str(response.text)
    conn = http.client.HTTPSConnection("api.scrape-it.cloud")
    payload = json.dumps({
    "url": f"{url}"
    })
    headers = {
    'x-api-key': '08bfae02-5911-4c19-9ae6-924ab5c5f35d',
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/scrape", payload, headers)
    res = conn.getresponse()
    print(res)
    data = res.read()
    datautf8 = json.load(data.decode("utf-8"))
    return datautf8['scrapingResult']['content']


async def guardar_csv():
    """
    Asynchronously saves the df_contentchapters DataFrame to a CSV file in the 'completes' directory.
    """
    global df_contentchapters
    global tituloarchivo
    path = os.getcwd()
    dir = os.listdir(path=path)
    if 'completes' not in dir:
        os.mkdir(os.path.join(path, 'completes'))

    df_contentchapters.to_csv(os.path.join(
        path, 'completes', tituloarchivo+'.csv'), index=None)


async def obtenernumpagurl(url):
    global descripcion
    global titulo
    global tituloen
    global autor
    global titulo_datos, tituloarchivo
    global df_listchapters
    descripcion = ''
    a = ''
    # resshm = await requestantibot(url)
    with open('html\Isekai Nonbiri Nouka – SHMTranslations.html','r', encoding='utf-8') as f:
        resshm = f.read()
    soup = bs(resshm, 'html.parser')
    # driver.close()
    tit = soup.find(id='isekai-nonbiri-nouka')
    # print(tit.get_text())
    tituloen = str(tit.get_text()).strip().rstrip()
    titulo_datos = ''.join([x for x in tituloen if x.isalpha() or x == ' '])
    tituloarchivo = titulo_datos.replace(' ', '_')
    print(tituloarchivo)
    autor = 'Kinosuke Naito'
    descrip = soup.find(class_='wp-element-caption')
    descripcion = await traducir(descrip.get_text())
    print(descripcion)
    lista_div = soup.find_all('div',
                              class_='wp-block-ub-content-toggle-accordion-content-wrap')
    chapters_list = []
    for div in lista_div:
        lista_a = div.find_all('a')
        for a in lista_a:
            if 'shmtranslations.com' in a.get('href') and 'quiz' not in a.get('href'):
                titulo_cap = str(
                    re.sub(" +", " ", a.get_text().strip().rstrip()))
                url_cap = a.get('href').strip().rstrip()
                print(titulo_cap, url_cap)
                chapters_list.append([titulo_cap, url_cap])
    df_listchapters = pd.DataFrame(
        chapters_list, columns=['nombre', 'urls'])
    df_listchapters.to_csv(os.path.join(
        os.getcwd(), 'chapters', tituloarchivo+'.csv'), index=None)


async def obtenercapitulotable():
    global descripcion
    global titulo
    global tituloen
    global autor
    global titulo_datos, tituloarchivo
    global df_listchapters
    global df_contentchapters

    df_contentchapters = pd.DataFrame()
    try:
        capsprocesados = len(pd.read_csv(os.path.join(
            os.getcwd(), 'completes', tituloarchivo+'.csv')))
    except Exception as e:
        capsprocesados = 0
        pass
    try:
        chaptercontent_list = pd.read_csv(os.path.join(os.getcwd(
        ), 'completes', tituloarchivo + '.csv'), dtype={'nombre': str, 'contenido': str}).values.tolist()
    except Exception as e:
        chaptercontent_list = []
        pass

    try:
        index = 0
        while index < len(df_listchapters):
            if capsprocesados < len(df_listchapters):
                if index < capsprocesados:
                    index = capsprocesados

            print(df_listchapters['nombre'][index])
            contenido_p_en = []
            # resnovelbin = await requestantibot(str(df_listchapters['urls'][index]))
            while True:
                try:
                    driver = instanciar_driver()
                    driver.get(str(df_listchapters['urls'][index]))
                    time.sleep(10)
                    soup = bs(driver.page_source, 'html.parser')
                    driver.quit()
                    contentcapter = soup.find(class_='entry-content')
                    if contentcapter is not None:
                        break
                except Exception as e:
                    print(e)
                    pass
            
            contentcapter_p = contentcapter.find_all('p')

            for idx, p in enumerate(contentcapter_p):
                if p.get_text() is not None or p.get_text().strip().rstrip() != "":
                    texto = await traducir(str(p.get_text()).strip().rstrip())
                    print(texto)
                    contenido_p_en.append(texto)
                print(
                    f"{idx+1} lineas traducidas de {len(contentcapter_p)}")
            contenido_p_en = ''.join(
                [f"<p>{x}</p>" for x in contenido_p_en])
            cap_nombre = await traducir(df_listchapters['nombre'][index])

            chaptercontent_list.append(
                [cap_nombre, contenido_p_en])

            df_contentchapters = pd.DataFrame(
                chaptercontent_list, columns=['nombre', 'contenido'])
            await guardar_csv()
            index += 1
        if df_contentchapters.empty:
            df_contentchapters = pd.DataFrame(
                chaptercontent_list, columns=['nombre', 'contenido'])
    except Exception as e:
        print(e)


async def crearepub():
    """
    This async function handles the click event for the 'Guardar Epub' button. 
    It checks for and creates 'epub' and 'images' directories if they don't exist, 
    renames image files, sets metadata for the EpubBook, adds content and chapters, 
    sets the table of contents, adds default NCX and Nav files, defines CSS style, 
    and writes the epub file. It also updates the page after the file is created.
    """
    global df_contentchapters
    global descripcion
    global tituloarchivo
    global titulo_datos
    global autor
    path = os.getcwd()
    dir = os.listdir()
    if 'epub' not in dir:
        os.mkdir(os.path.join(path, 'epub'))
    if 'images' not in dir:
        os.mkdir(os.path.join(path, 'images'))
    dirimgs = os.listdir(os.path.join(path, 'images'))
    if ''.join([x for x in dirimgs if tituloarchivo in x]) == '':
        google_crawler = GoogleImageCrawler()
        # filters = dict(size='small')
        google_crawler.crawl(keyword=titulo_datos, max_num=1)
        time.sleep(5)
        dirimgs = os.listdir(os.path.join(path, 'images'))
        imgenportada = ''.join(
            [x for x in dirimgs if '000001' in x]).split('.')
        # if imgenportada[0] != '':
        try:
            os.rename(os.path.join(path, 'images', '.'.join(imgenportada)), os.path.join(
                path, 'images', tituloarchivo+'.'+imgenportada[1]))
        except:
            pass

    book = epub.EpubBook()
    # set metadata
    book.set_identifier(str(uuid.uuid4()))
    imgenportada = ''.join([x for x in dirimgs if tituloarchivo in x])
    if imgenportada != '':
        book.set_cover('cover.jpg',
                       open((os.path.join(path, 'images', imgenportada)), 'rb').read())

    book.set_title(titulo_datos)
    book.set_language('es')
    book.add_author(f"{autor}")

    cs = ()

    c = epub.EpubHtml(title='Introduction',
                      file_name='intro.xhtml', lang='es')
    c.content = f"<h1>{titulo_datos}</h1><br><p>{descripcion}</p>"
    # add chapter
    book.add_item(c)
    for index, chapter in df_contentchapters.iterrows():
        cp = str(index+1).zfill(len(str(len(df_contentchapters))))
        c = epub.EpubHtml(title=str(
            chapter['nombre']), file_name='chap_' + cp + '.xhtml', lang='es')
        c.content = f"<h1>{str(chapter['nombre'])}</h1><br>{chapter['contenido']}"
        # add chapter
        book.add_item(c)
        cs += (c,)

    book.toc = (
        epub.Link('intro.xhtml', 'Introduction', 'intro'),
        (
            epub.Section('Introduction', 'intro.xhtml'),
            cs
        )
    )

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(
        uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    sp = ['nav']
    for j in cs:
        sp.append(j)
    # print(sp)
    book.spine = sp
    # write to the file
    epub.write_epub(os.path.join(
        path, 'epub', tituloarchivo+'.epub'), book, {})
    # print(dFrame)
    print('archivo epub de ', tituloarchivo, ' creado')


async def btn_guardar_pdf_click(url):
    global df_contentchapters
    global descripcion
    global tituloarchivo
    global titulo_datos
    global autor
    path = os.getcwd()
    dir = os.listdir()
    if 'pdf' not in dir:
        os.mkdir(os.path.join(path, 'pdf'))
    if 'images' not in dir:
        os.mkdir(os.path.join(path, 'images'))
    dirimgs = os.listdir(os.path.join(path, 'images'))
    if ''.join([x for x in dirimgs if tituloarchivo in x]) == '':
        google_crawler = GoogleImageCrawler()
        # filters = dict(size='small')
        google_crawler.crawl(keyword=titulo_datos, max_num=1)
        time.sleep(5)
        dirimgs = os.listdir(os.path.join(path, 'images'))
        imgenportada = ''.join(
            [x for x in dirimgs if '000001' in x]).split('.')
        # if imgenportada[0] != '':
        try:
            os.rename(os.path.join(path, 'images', '.'.join(imgenportada)), os.path.join(
                path, 'images', tituloarchivo+'.'+imgenportada[1]))
        except:
            pass
    else:
        imgenportada = ''.join([x for x in dirimgs if tituloarchivo in x])

    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_font(fname='ttf/Poppins-Regular.ttf')
    pdf.set_font('Poppins-Regular', size=12)

    pdf.set_title(f"{titulo_datos}")
    pdf.set_author(f"{autor}")
    pdf.set_creator('David Eliceo Vite Vergara')
    pdf.add_page()
    pdf.chapter_title(f"{titulo_datos}")
    pdf.image(name=os.path.join(path, 'images',
                imgenportada), x=pdf.epw/3, w=75)
    pdf.write_html(text="<h5>Resumen:</h5>")
    pdf.write_html(text=f"<p>{descripcion}.</p>")
    pdf.write(text=f"Url de Novela: {url}")

    for index, chapter in df_contentchapters.iterrows():
        pdf.print_chapter(f"{chapter['nombre']}",
                            f"{chapter['contenido']}")
        print(f"Añadido {chapter['nombre']} al PDF")
    pdf.output(f"{os.path.join(path,'pdf',tituloarchivo)}.pdf")
    print('archivo pdf de ', tituloarchivo, ' creado')
    


async def main():
    links = [
        'https://www.shmtranslations.com/ongoing/isekai-nonbiri-nouka/',
    ]
    for link in links:
        print(link)
        await obtenernumpagurl(str(link))
        await obtenercapitulotable()
        await crearepub()
        await btn_guardar_pdf_click(str(link))

    return False

if __name__ == "__main__":
    asyncio.run(main())

# band = True

# while band == True:
#     try:
#         band = main()
#     except Exception as e:
#         print('\nhubo un error\n', e.args)
#         time.sleep(3)
#         band = True
