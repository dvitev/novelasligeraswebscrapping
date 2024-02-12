import json
import os
import time
import datetime
import pandas as pd
import flet as ft
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
import translators as ts
from icrawler.builtin import GoogleImageCrawler
from ebooklib import epub
import uuid
import sys
import asyncio
import re

try:
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
except Exception as e:
    pass


async def main(page: ft.Page):
    """
    A description of the entire function, its parameters, and its return types.
    """
    page.title = "Novel Bin"
    tituloarchivo = ''
    titulo_datos = ''

    async def btn_rest_click(e):
        global df_contentchapters
        global df_infobox
        global resumen
        global tituloarchivo
        global titulo_datos
        global df_listchapters
        global resumen
        global rows_listchapters
        df_contentchapters=[]
        df_infobox=[]
        resumen=""
        tituloarchivo = ""
        titulo_datos=""
        df_listchapters=[]
        rows_listchapters=[]
        data_obtenida.controls=[]
        rows_listchapters = []
        btn_guardar_epub.visible = False
        btn_obtenercapitulos.visible = False
        await page.update_async()

    async def btn_guardar_epub_click(e):
        """
        This async function handles the click event for the 'Guardar Epub' button. 
        It checks for and creates 'epub' and 'images' directories if they don't exist, 
        renames image files, sets metadata for the EpubBook, adds content and chapters, 
        sets the table of contents, adds default NCX and Nav files, defines CSS style, 
        and writes the epub file. It also updates the page after the file is created.
        """
        global df_contentchapters
        global df_infobox
        global resumen
        global tituloarchivo
        global titulo_datos
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
        book.add_author(df_infobox['descripcion'][1])

        cs = ()

        c = epub.EpubHtml(title='Introduction',
                          file_name='intro.xhtml', lang='es')
        c.content = f"<h1>{titulo_datos}</h1><br><p>{resumen}</p>"
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
        btn_reset.visible = True
        await page.update_async()

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

    async def btn_obtenercapitulos_click(e):
        """
        This async function btn_obtenercapitulos_click handles the click event for obtaining chapters. It uses a global data frame df_listchapters and df_contentchapters, and a global variable tituloarchivo. It attempts to read a CSV file and sets capsprocesados accordingly. It then reads another CSV file to populate chaptercontent_list. The function then iterates over df_listchapters, processes the data, and updates df_contentchapters. It also sets visibility for btn_guardar_epub. Any exceptions are caught and printed, and the page is asynchronously updated.
        """
        global df_listchapters
        global df_contentchapters
        global tituloarchivo
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
            # servicio = Service(
            #     executable_path=ChromeDriverManager().install())
            # op = webdriver.ChromeOptions()
            # # Ejecutar en modo headless (sin ventana visible))
            # # Evitar errores en algunos sistemas
            # op.add_argument('--disable-gpu')
            # # Evitar errores en algunos sistemas
            # op.add_argument('--no-sandbox')
            # op.add_argument('--ignore-certificate-errors')
            # op.add_argument('--ssl-protocol=any')
            # op.headless = True
            index = 0
            while index < len(df_listchapters):
                if index < capsprocesados:
                    for i in range(0, capsprocesados):
                        datatable.rows[i].selected = True
                    index = capsprocesados
                    page.update_async()

                # driver = webdriver.Chrome(service=servicio, options=op)
                service = Service(verbose=True)

                driver = webdriver.Edge(service=service)
                # driver.minimize_window()
                capitulo.value = df_listchapters['nombre'][index]
                print(df_listchapters['nombre'][index])
                contenido_p_en = []
                driver.get(df_listchapters['urls'][index])
                driver.execute_script(
                    "window.scrollBy(0,document.body.scrollHeight/2);")
                time.sleep(2)
                soup = bs(driver.page_source, 'html.parser')
                # driver.close()
                driver.quit()
                contentcapter = soup.find('div', id='chr-content')
                contentcapter_p = contentcapter.find_all('p')

                for idx, p in enumerate(contentcapter_p):
                    if p.get_text() is not None or p.get_text().strip().rstrip() != "":
                        if len(str(p.get_text())) > 200:
                            textoaren = str(p.get_text()).split('. ')
                            textoar = []
                            for idx2, tar in enumerate(textoaren):
                                textoar.append(await traducir(tar))
                                print(f"{idx2+1} de {len(textoaren)} partes traducidas")
                            texto = '. '.join(textoar)
                        else:
                            texto = await traducir(str(p.get_text()))
                        print(texto)
                        contenido_p_en.append(texto)
                    linea.value = f"{idx+1} lineas traducidas de {len(contentcapter_p)}"
                    print(
                        f"{idx+1} lineas traducidas de {len(contentcapter_p)}")
                    await page.update_async()
                contenido_p_en = ''.join(
                    [f"<p>{x}</p>" for x in contenido_p_en])
                cap_nombre = await traducir(df_listchapters['nombre'][index])

                chaptercontent_list.append(
                    [cap_nombre, contenido_p_en])

                df_contentchapters = pd.DataFrame(
                    chaptercontent_list, columns=['nombre', 'contenido'])
                capitulo.value = ''
                linea.value = ''
                await guardar_csv()
                datatable.rows[index].selected = True
                await page.update_async()
                index += 1
            if df_contentchapters.empty:
                df_contentchapters = pd.DataFrame(
                    chaptercontent_list, columns=['nombre', 'contenido'])
            btn_guardar_epub.visible = True
        except Exception as e:
            print(e)
        await page.update_async()

    async def btn_obtenerdatos_click(e):
        """
        An asynchronous function to handle the click event of a button. It disables certain buttons, updates the page, sets global variables, checks for input validity, performs web scraping, and updates the page again with the obtained data. It also handles exceptions and updates the page accordingly.
        """
        btn_obtenerdatos.disabled = True
        btn_obtenercapitulos.visible = False
        btn_guardar_epub.visible = False
        await page.update_async()
        global df_infobox
        global titulo_datos
        global tituloarchivo
        global df_listchapters
        global resumen
        if not txt_name.value:
            txt_name.error_text = "El Campo no puede estar en blanco"
            await page.update_async()
        if "https://novel-bin.net/novel-bin/" not in txt_name.value:
            txt_name.error_text = f"La URL no es de {page.title}. Proporcione una URL de novela válida."
            await page.update_async()
        else:

            # xpath_titulo = '/html/body/div/main/div[2]/div[1]/div[1]/div[3]/h3'
            try:
                data_obtenida.controls = []

                # servicio = Service(
                #     executable_path=ChromeDriverManager().install())
                # op = webdriver.ChromeOptions()
                # # Ejecutar en modo headless (sin ventana visible))
                # # Evitar errores en algunos sistemas
                # op.add_argument('--disable-gpu')
                # # Evitar errores en algunos sistemas
                # op.add_argument('--no-sandbox')
                # op.add_argument('--ignore-certificate-errors')
                # op.add_argument('--ssl-protocol=any')
                # # op.headless = True
                # driver = webdriver.Chrome(service=servicio, options=op)
                service = Service(verbose=True)

                driver = webdriver.Edge(service=service)
                # driver.minimize_window()
                # Realizar la solicitud HTTP a la URL
                driver.get(txt_name.value)
                driver.maximize_window()
                time.sleep(1)
                driver.find_element(
                    By.XPATH, '/html/body/div/main/div[2]/div[1]/div[4]/ul/li[2]/a').click()
                time.sleep(1)
                driver.execute_script(
                    "window.scrollBy(0,document.body.scrollHeight);")
                time.sleep(2)
                html = driver.page_source
                soup = bs(html, 'html.parser')
                # driver.close()
                driver.quit()
                # Obtener el título de la página
                # dom = etree.HTML(str(soup))
                titulo_h1 = soup.find('h3', class_='title').get_text()
                print(titulo_h1)

                titulo_datos = ' '.join(
                    [x for x in titulo_h1.split() if x.lower() != 'raw' and x.lower() != 'novel'])
                tituloarchivo = ''.join(
                    [x for x in titulo_datos if x.isalpha() or x == ' ']).replace(' ', '_')
                data_obtenida.controls.append(
                    ft.Text(f"{titulo_datos}", size=25))

                infobox_ul = soup.find_all('ul', class_='info info-meta')[0]
                info_list = []
                for i in infobox_ul.find_all('li'):
                    texto = await traducir(re.sub(" +", " ", i.get_text().strip().rstrip().replace('\n', ' ')))
                    info_list.append(texto)
                    data_obtenida.controls.append(ft.Text(f"| {texto} |"))
                df_infobox = pd.DataFrame(
                    info_list, columns=['descripcion'])
                print(df_infobox)
                resumen_en = str(
                    soup.find('div', class_='desc-text').get_text().strip().rstrip())
                resumen = await traducir(resumen_en)
                data_obtenida.controls.append(ft.Text(f"{resumen}"))
                print(resumen)
                list_chapters_div = soup.find('div', id='list-chapter')
                chapters_list = []
                for ul in list_chapters_div.find_all('ul', class_='list-chapter'):
                    for a in ul.find_all('a'):
                        titulo_cap = str(
                            re.sub(" +", " ", a.get_text().strip().rstrip()))
                        url_cap = a.get('href').strip().rstrip()
                        print(titulo_cap, url_cap)
                        chapters_list.append([titulo_cap, url_cap])
                df_listchapters = pd.DataFrame(
                    chapters_list, columns=['nombre', 'urls'])
                # print(df_listchapters)
                for index, chap in df_listchapters.iterrows():
                    rows_listchapters.append(ft.DataRow(cells=[
                        ft.DataCell(
                            ft.Text(chap['nombre'])),
                        ft.DataCell(ft.Text(chap['urls'])),
                    ]))
                data_obtenida.controls.append(
                    datatable
                )
                data_obtenida.visible = True
                btn_obtenerdatos.disabled = False
                btn_obtenercapitulos.visible = True
                df_listchapters.to_csv(os.path.join(
                    os.getcwd(), 'chapters', tituloarchivo+'.csv'), index=None)
            except Exception as e:
                btn_obtenerdatos.disabled = False
                data_obtenida.controls = ft.Text("Error")
                print(e)

            await page.update_async()

    rows_listchapters = []
    chaptercontent_list = []
    txt_name = ft.TextField(
        label="Ingrese la Url de Novela de " + page.title,
        value='https://novel-bin.net/novel-bin/emperors-domination-nov1762445829')
    data_obtenida = ft.ListView(
        expand=True, spacing=10, visible=False, item_extent=50)
    btn_guardar_epub = ft.ElevatedButton(
        "Guardar Capitulos EPUB",
        visible=False,
        icon=ft.icons.SAVE,
        on_click=btn_guardar_epub_click
    )
    btn_obtenerdatos = ft.ElevatedButton(
        "Obtener Datos!", on_click=btn_obtenerdatos_click)
    btn_obtenercapitulos = ft.ElevatedButton(
        "Obtener Capitulos", on_click=btn_obtenercapitulos_click, visible=False)
    btn_reset = ft.ElevatedButton("Reset", visible=False, icon=ft.icons.RESET_TV, on_click=btn_rest_click)
    datatable = ft.DataTable(
        show_checkbox_column=True,
        border=ft.border.all(2),
        border_radius=ft.border_radius.all(10),
        vertical_lines=ft.border.BorderSide(1, ft.colors.BLACK),
        horizontal_lines=ft.border.BorderSide(1, ft.colors.BLACK),
        columns=[
            ft.DataColumn(ft.Text("Capitulos")),
            ft.DataColumn(ft.Text("Urls")),
        ],
        rows=rows_listchapters,
    )
    capitulo = ft.Text(value='')
    linea = ft.Text(value='')

    await page.add_async(
        txt_name,
        ft.Row(controls=[
            btn_obtenerdatos,
            btn_obtenercapitulos,
            btn_guardar_epub,
            btn_reset,
            ft.Column(controls=[
                capitulo, linea
            ])
        ]),
        data_obtenida
    )


ft.app(target=main)
