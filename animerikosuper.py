import datetime
import json
import os
from lxml import etree

from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import certifi
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
from googletrans import Translator
from ebooklib import epub
import time
from urllib.parse import urlparse
from icrawler.builtin import GoogleImageCrawler
import os
import translators as ts

# valcharacter = [[48, 57], [65, 90], [97, 122], 32]
valcharacter = ' 0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúäëïöü'
titulo = ''
cantidadcaptitulo = 0
listaCapitulos = []
autor = ''
descripcion = ''
genero = []
ext = ''
page = ''
novelname = 'https://www.readwn.com/e/extend/fy.php?page=%s&wjm=%s'

# opciones = Options()
# opciones.headless = True
servicio = Service(executable_path=ChromeDriverManager().install())


def Traduccion(text):
    translator = Translator()
    translation = translator.translate(text, dest='es', src='en')
    return translation.text


def quitar_simbolos_especiales(title):
    titlenew = ''
    for j in range(len(title)):
        if title[j] in valcharacter:
            titlenew += title[j]
    return titlenew


def comprobarurl(url):
    o = urlparse(url)
    # print(o)
    return str(o.scheme) + '://' + str(o.netloc)


def escribirtablecontents(titulo0, datos):
    df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
    df.to_csv(titulo0 + '_tablecontents.csv', sep=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC, index=False)


def arraytopandas(datos, colnames):
    return pd.DataFrame(data=datos, columns=colnames)


def escribircapitulotable(titulo0, datos2):
    df2 = pd.DataFrame(data=datos2, columns=['nombrecap', 'texto'])
    df2.to_csv(titulo0 + '.csv', sep=';', quotechar='"',
               quoting=csv.QUOTE_NONNUMERIC, index=False)


def inicio(ini):
    num = 100
    return (ini * num) + (num * (ini - 2))


def fin(ini):
    num = 200
    return (ini * num) - 1


def obtenernumpagurl(url):
    global descripcion
    global titulo
    global autor
    global genero
    global listaCapitulos
    genero = []
    listaCapitulos = []
    op = uc.ChromeOptions()
    op.headless = True
    descripcion = ''
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op)
    driver.minimize_window()
    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    titulo = quitar_simbolos_especiales(soup.find_all(class_='entry-header')[0].get_text().replace('NOVELA', '')
                                        .replace('ESPAÑOL', '').strip()).strip()
    print(titulo.lower())
    list_chap = soup.find_all(class_='entry-content')[0].find_all('a')
    cont = 1
    for i in range(len(list_chap)):
        if 'animerikosuper.blogspot.com' in str(list_chap[i].get('href')) and str(list_chap[i].get('href')).endswith(
                '.html'):
            # print('Capitulo ' + str(cont), list_chap[i].get('href'))
            listaCapitulos.append(['Capitulo ' + str(cont), list_chap[i].get('href')])
            cont += 1
            # time.sleep(1)
    escribirtablecontents(titulo.lower().replace(' ', '_').strip(), listaCapitulos)


def obtenercapitulotable(limite):
    global listaCapitulos
    datos2 = []
    limitecap = len(listaCapitulos)
    x = inicio(limite)
    y = fin(limite)

    if y >= limitecap:
        y = limitecap

    if len(str(x + 1)) == 1:
        inin = ('0' * (len(str(limitecap)) - 1)) + str(x + 1)
    elif len(str(x + 1)) == 2:
        inin = ('0' * (len(str(limitecap)) - 2)) + str(x + 1)
    elif len(str(x + 1)) == 3:
        inin = ('0' * (len(str(limitecap)) - 3)) + str(x + 1)
    elif len(str(x + 1)) == 4:
        inin = ('0' * (len(str(limitecap)) - 4)) + str(x + 1)
    elif len(str(x + 1)) == 5:
        inin = ('0' * (len(str(limitecap)) - 5)) + str(x + 1)

    if len(str(y + 1)) == 1:
        finn = ('0' * (len(str(limitecap)) - 1)) + str(y + 1)
    if len(str(y + 1)) == 2:
        finn = ('0' * (len(str(limitecap)) - 2)) + str(y + 1)
    if len(str(y + 1)) == 3:
        finn = ('0' * (len(str(limitecap)) - 3)) + str(y + 1)
    if len(str(y + 1)) == 4:
        finn = ('0' * (len(str(limitecap)) - 4)) + str(y + 1)
    if len(str(y + 1)) == 5:
        finn = ('0' * (len(str(limitecap)) - 5)) + str(y + 1)
    # print(x,y,inin,finn)

    listaarchivos = sorted(os.listdir())
    total1 = len(listaarchivos)

    b = 0
    for i in range(total1):
        if (titulo.lower().replace(' ', '_').strip() + '_' + inin + '_' + finn) in str(listaarchivos[i]):
            b = 1
    if b == 0:
        if x < limitecap:
            # print(x, y, inin, finn)
            for i in range(x, y + 1):
                if i < limitecap:
                    op = Options()
                    op.headless = True
                    print(listaCapitulos[i][0], listaCapitulos[i][1])
                    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op)
                    driver.minimize_window()
                    driver.get(listaCapitulos[i][1])
                    html = driver.page_source
                    soup = bs(html, 'html.parser')
                    driver.close()
                    cha_content = soup.find_all(id='post-body')[0].find_all('span')
                    textar = []
                    # print(cha_content)
                    for cc in cha_content:
                        if 'Índice' not in cc.get_text():
                            textar.append(cc.get_text().strip())
                            print(cc.get_text().strip())
                    time.sleep(3)
                    datos2.append([listaCapitulos[i][0], '<br>'.join(textar)])
            escribircapitulotable(titulo.lower().replace(' ', '_').strip() + '_' + inin + '_' + finn, datos2)
        return 'True'
    else:
        return 'False'


def crearepub():
    global titulo
    global autor
    global descripcion
    global ext
    listaarchivos = sorted(os.listdir())
    total1 = len(listaarchivos)
    # print(path)
    path = os.path.join(os.getcwd(), 'images')
    if 'images' not in os.listdir():
        os.mkdir(path)

    listaarchivos2 = sorted(os.listdir(path))
    total2 = len(listaarchivos2)
    b = 0
    for i in range(total2):
        if titulo.lower().replace(' ', '_').strip() in listaarchivos2[i]:
            ext = listaarchivos2[i][-4:]
            b = 1
    if b == 0:
        google_crawler = GoogleImageCrawler()
        # filters = dict(size='small')
        google_crawler.crawl(keyword=titulo.lower().replace(' ', '_').strip(), max_num=1)
        time.sleep(5)
        listaarchivos2 = sorted(os.listdir(path))
        for k in range(len(listaarchivos2)):
            if '000001' in listaarchivos2[k]:
                ext = listaarchivos2[k][-4:]
                # print(ext,listaarchivos2[k])
                file_oldname = os.path.join(path, ('000001' + ext))
                file_newname_newfile = os.path.join(
                    path, (titulo.lower().replace(' ', '_').strip() + ext))
                os.rename(file_oldname, file_newname_newfile)
    else:
        print(titulo.lower().replace(' ', '_').strip() + ext)

    book = epub.EpubBook()
    # set metadata
    book.set_identifier('id123456')
    if os.path.isfile(os.path.join(path, (titulo.lower().replace(' ', '_').strip() + ext))):
        book.set_cover('cover.jpg',
                       open((os.path.join(path, (titulo.lower().replace(' ', '_').strip() + ext))), 'rb').read())
    book.set_title(titulo)
    book.set_language('es')
    book.add_author(autor)

    dfs = []
    cs = ()
    bandera = True
    if titulo.lower().replace(' ', '_').strip() + '_complete.csv' not in listaarchivos:
        for i in range(total1):
            if titulo.lower().replace(' ', '_').strip() in str(listaarchivos[i]):
                if 'tablecontents' not in str(listaarchivos[i]) and 'complete' not in str(listaarchivos[i]) \
                        and '.jpg' not in str(listaarchivos[i]) and '.epub' not in str(listaarchivos[i]):
                    print(listaarchivos[i])
                    dfs.append(pd.read_csv(
                        listaarchivos[i], sep=';', quotechar='"'))
    else:
        bandera = False
    if bandera:
        print('compilado no existe')
        dFrame = pd.concat(dfs, ignore_index=True)
        dFrame.to_csv((titulo.lower().replace(' ', '_').strip() + '_complete.csv'), sep=';', quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC, index=False)
    else:
        print('compilado existe')
        dFrame = pd.read_csv((titulo.lower().replace(' ', '_').strip() + '_complete.csv'), sep=';', quotechar='"')
        # print(dFrame.head())
    limitecap = len(dFrame['nombrecap'])
    print(limitecap)

    c = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='es')
    c.content = u'<h1>%s</h1><p>%s</p>' % (titulo, descripcion)
    # add chapter
    book.add_item(c)
    for i in range(limitecap):
        cp = ''
        if len(str(i)) == 1:
            cp = ('0' * (len(str(limitecap)) - 1)) + str(i + 1)
        elif len(str(i)) == 2:
            cp = ('0' * (len(str(limitecap)) - 2)) + str(i + 1)
        elif len(str(i)) == 3:
            cp = ('0' * (len(str(limitecap)) - 3)) + str(i + 1)
        elif len(str(i)) == 4:
            cp = ('0' * (len(str(limitecap)) - 4)) + str(i + 1)
        elif len(str(i)) == 5:
            cp = ('0' * (len(str(limitecap)) - 5)) + str(i + 1)
        print(i, str(dFrame['nombrecap'][i]))
        c = epub.EpubHtml(title=str(dFrame['nombrecap'][i]), file_name='chap_' + cp + '.xhtml', lang='es')

        c.content = u'<h1>%s</h1><p>%s</p>' % (
            str(dFrame['nombrecap'][i]), str(dFrame['texto'][i]))
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
    epub.write_epub(titulo.lower().replace(' ', '_').strip() + '.epub', book, {})
    # print(dFrame)
    print('archivo epub de ', titulo.lower().replace(' ', '_').strip(), ' creado')
    titulo = ''
    autor = ''
    descripcion = ''


def obtenerlistadonovelas(url):
    global datanovelas
    op = Options()
    op.headless = True
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    pageList = soup.find_all(id='PageList2')[0].find_all(class_='widget-content')[0].find_all('a')
    listnovels = []
    for pl in pageList:
        listnovels.append([pl.get_text(), pl.get('href')])
        # print(pl.get_text(), pl.get('href'))
    datanovelas = pd.DataFrame(data=listnovels, columns=['nombrenovel', 'url'])
    datanovelas.to_csv('animerikosuper_listnovels.csv', sep=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC,
                       index=False)


def main():
    global titulo
    global autor
    global descripcion
    global listaCapitulos
    global genero
    global datanovelas
    link = 'https://animerikosuper.blogspot.com/'
    obtenerlistadonovelas(link)
    # datanovelas = pd.read_csv('animerikosuper_listnovels.csv', sep=';', quotechar='"')
    for i in range(len(datanovelas)):
        print(datanovelas['url'][i])
        obtenernumpagurl(str(datanovelas['url'][i]))
        # print(len(listaCapitulos))
        if titulo.lower().replace(' ', '_').strip() + '_complete.csv' not in sorted(os.listdir()):
            for j in range(int(len(listaCapitulos) / 200) + 1):
                if obtenercapitulotable(j + 1) == 'True':
                    time.sleep(1)
        crearepub()
        titulo = ''
        listaCapitulos = []
        autor = ''
        descripcion = ''
        genero = []
        time.sleep(5)
    return False


band = True
while band == True:
    try:
        band = main()
    except Exception as e:
        print('\nhubo un error\n', e.args)
        time.sleep(3)
        band = True
