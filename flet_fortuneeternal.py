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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
import translators as ts
from icrawler.builtin import GoogleImageCrawler
from ebooklib import epub
import uuid
import sys
import asyncio

try:
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
except Exception as e:
    pass


async def main(page: ft.Page):
    page.title = "Fortune Eternal"
    tituloarchivo = ''
    titulo_datos = ''

    async def btn_guardar_epub_click(e):
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
            imgenportada = ''.join(
                [x for x in dirimgs if '000001' in x]).split('.')
            if imgenportada[0] != '':
                os.rename(os.path.join(path, 'images', '.'.join(imgenportada)), os.path.join(
                    path, 'images', tituloarchivo+'.'+imgenportada[1]))

        book = epub.EpubBook()
        # set metadata
        book.set_identifier(str(uuid.uuid4()))
        imgenportada = ''.join([x for x in dirimgs if tituloarchivo in x])
        if imgenportada != '':
            book.set_cover('cover.jpg',
                           open((os.path.join(path, 'images', imgenportada)), 'rb').read())

        book.set_title(titulo_datos)
        book.set_language('es')
        book.add_author(df_infobox['descripcion'][3])

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
        await page.update_async()

    async def guardar_csv():
        global df_contentchapters
        global tituloarchivo
        path = os.getcwd()
        dir = os.listdir(path=path)
        if 'completes' not in dir:
            os.mkdir(os.path.join(path, 'completes'))

        df_contentchapters.to_csv(os.path.join(
            path, 'completes', tituloarchivo+'.csv'), index=None)

    async def traducir(texto):
        # pooltranslators = ['argos', 'bing', 'google', 'yandex', 'baidu', 'tencent', 'youdao']
        # poolindex = 0
        contenido_p = ''

        while True:
            try:
                # print(pooltranslators[poolindex])
                contenido_p = ts.translate_text(
                    texto, from_language='ko', to_language='es')
                break
            except Exception as e:
                # print(pooltranslators[poolindex])
                print(e)
                # if poolindex == len(pooltranslators)-1:
                #     break
                # poolindex += 1
                pass
        return contenido_p

    async def btn_obtenercapitulos_click(e):
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
            chaptercontent_list = pd.read_csv(os.path.join(os.getcwd(),'completes',tituloarchivo + '.csv'), dtype={'nombre': str, 'contenido':str}).values.tolist()
        except Exception as e:
            chaptercontent_list = []
            pass
        try:
            servicio = Service(
                executable_path=ChromeDriverManager().install())
            op = webdriver.ChromeOptions()
            # Ejecutar en modo headless (sin ventana visible))
            # Evitar errores en algunos sistemas
            op.add_argument('--disable-gpu')
            # Evitar errores en algunos sistemas
            op.add_argument('--no-sandbox')
            op.add_argument('--ignore-certificate-errors')
            op.add_argument('--ssl-protocol=any')
            op.headless = True
            for index in range(len(df_listchapters)-capsprocesados, 0, -1):
                driver = webdriver.Chrome(service=servicio, options=op)
                # driver.minimize_window()
                capitulo.value = df_listchapters['nombre'][index-1]
                print(df_listchapters['nombre'][index-1])
                contenido_p_en = []
                driver.get(df_listchapters['urls'][index-1])
                time.sleep(5)
                soup = bs(driver.page_source, 'html.parser')
                driver.close()
                contentcapter = soup.find('div', class_='entry-content_wrap')
                contentcapter_p = contentcapter.find_all('p')
                # 'alibaba', 'baidu', 'mirai', 'modernMt', 'myMemory'
                # pooltranslators= [ 'bing', 'deepl', 'google', 'niutrans', ]

                for idx, p in enumerate(contentcapter_p):
                    if p.get_text() is not None:
                        texto = await traducir(str(p.get_text()))
                        # await asyncio.sleep(0.05)
                        print(texto)
                        contenido_p_en.append(texto)
                    linea.value = f"{idx+1} lineas traducidas de {len(contentcapter_p)}"
                    print(f"{idx+1} lineas traducidas de {len(contentcapter_p)}")
                    await page.update_async()
                contenido_p_en = ''.join(
                    [f"<p>{x}</p>" for x in contenido_p_en])

                chaptercontent_list.append(
                    [df_listchapters['nombre'][index-1], contenido_p_en])

                datatable.rows[len(df_listchapters['nombre']
                                   )-index].selected = True
                # df_listchapters.to_csv(os.path.join(os.getcwd(),'chapters',tituloarchivo+'.csv'),index=None)
                df_contentchapters = pd.DataFrame(
                    chaptercontent_list, columns=['nombre', 'contenido'])
                capitulo.value = ''
                linea.value = ''
                await guardar_csv()
                await page.update_async()
            # driver.close()
            # df_contentchapters = pd.DataFrame(
                # chaptercontent_list, columns=['nombre', 'contenido'])
            if df_contentchapters.empty:
                df_contentchapters = pd.DataFrame(
                    chaptercontent_list, columns=['nombre', 'contenido'])
            btn_guardar_epub.visible = True
        except Exception as e:
            print(e)
        await page.update_async()

    async def btn_obtenerdatos_click(e):
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
        if "https://www.fortuneeternal.com/novel/" not in txt_name.value:
            txt_name.error_text = "La URL no es de Fortune Eternal. Proporcione una URL de novela válida."
            await page.update_async()
        else:

            xpath_titulo = '/html/body/div[1]/div/div[3]/div/div[1]/div/div/div/div[2]/h1'
            try:
                data_obtenida.controls = []

                servicio = Service(
                    executable_path=ChromeDriverManager().install())
                op = webdriver.ChromeOptions()
                # Ejecutar en modo headless (sin ventana visible))
                # Evitar errores en algunos sistemas
                op.add_argument('--disable-gpu')
                # Evitar errores en algunos sistemas
                op.add_argument('--no-sandbox')
                op.add_argument('--ignore-certificate-errors')
                op.add_argument('--ssl-protocol=any')
                # op.headless = True
                driver = webdriver.Chrome(service=servicio, options=op)
                driver.minimize_window()
                # Realizar la solicitud HTTP a la URL
                driver.get(txt_name.value)

                time.sleep(5)

                html = driver.page_source
                soup = bs(html, 'html.parser')
                driver.close()
                # Obtener el título de la página
                dom = etree.HTML(str(soup))
                titulo_h1 = dom.xpath(xpath_titulo)[0].text
                print(titulo_h1)

                titulo_datos = ' '.join(
                    [x for x in titulo_h1.split() if x.lower() != 'raw' and x.lower() != 'novel'])
                tituloarchivo = ''.join(
                    [x for x in titulo_datos if x.isalpha() or x == ' ']).replace(' ', '_')
                data_obtenida.controls.append(
                    ft.Text(f"{titulo_datos}", size=25))

                infobox = soup.find_all('div', class_='post-content_item')
                info_list = []
                for i in infobox:
                    info_list.append([i.find(class_='summary-heading').get_text().strip(
                    ).rstrip(), i.find(class_='summary-content').get_text().strip().rstrip()])
                    data_obtenida.controls.append(ft.Text(
                        f"| {i.find(class_='summary-heading').get_text().strip().rstrip()} | {i.find(class_='summary-content').get_text().strip().rstrip()} |"))
                df_infobox = pd.DataFrame(
                    info_list, columns=['titulo', 'descripcion'])
                print(df_infobox)
                resumen_en = str(
                    soup.find('div', class_='summary__content').get_text().strip().rstrip())
                resumen = ts.translate_text(
                    resumen_en, translator='bing', to_language='es')
                data_obtenida.controls.append(ft.Text(f"{resumen}"))
                print(resumen)

                list_chapters_li = soup.find_all(
                    'li', class_='wp-manga-chapter')
                chapters_list = []
                # print(list_chapters_li)
                for index, l in enumerate(list_chapters_li):
                    chapters_list.append(
                        [f"Capítulo ({len(list_chapters_li)-index})", l.find('a')['href'].strip().rstrip()])
                    # print(f"Capítulo ({len(list_chapters_li)-(index+1)})", l.find('a')['href'].strip().rstrip())
                df_listchapters = pd.DataFrame(
                    chapters_list, columns=['nombre', 'urls'])
                # print(df_listchapters)
                for index in range(len(df_listchapters), 0, -1):
                    rows_listchapters.append(ft.DataRow(cells=[
                        ft.DataCell(
                            ft.Text(df_listchapters['nombre'][index-1])),
                        ft.DataCell(ft.Text(df_listchapters['urls'][index-1])),
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
        label="Ingrese la Url de Novela de Fortune Eternal",
        value='https://www.fortuneeternal.com/novel/black-corporation-joseon-raw-novel/')
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
            ft.Column(controls=[
                capitulo, linea
            ])
        ]),
        data_obtenida
    )


ft.app(target=main)
