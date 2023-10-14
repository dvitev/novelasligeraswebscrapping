import datetime
import glob
import json
import os
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

path = os.getcwd()

valcharacter = ' 0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúäëïöü'
titulo = ''
tituloen = ''
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


def quitar_simbolos_especiales(title):
    titlenew = ''
    for j in range(len(title)):
        if title[j] in valcharacter:
            titlenew += title[j]
    return titlenew


def escribirtablecontents(titulo0, datos):
    df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
    df.to_csv(os.path.join(path, 'tableofcontents', titulo0 + '_tablecontents.csv'),
              sep=';',
              quotechar='"',
              quoting=csv.QUOTE_NONNUMERIC,
              index=False)


def escribircapitulotable(titulo, datos2):
    df2 = pd.DataFrame(data=datos2, columns=['nombrecap', 'texto'])
    df2.to_csv(os.path.join(path, 'chapters', titulo + '.csv'),
               sep=';',
               quotechar='"',
               quoting=csv.QUOTE_NONNUMERIC,
               index=False)


def inicio(ini):
    num = 100
    return (ini * num) + (num * (ini - 2))


def fin(ini):
    num = 200
    return (ini * num) - 1


def obtenernumpagurl(url):
    global descripcion
    global titulo
    global tituloen
    global autor
    global listaCapitulos
    global hostname
    global port
    descripcion = ''
    a = ''
    driver = requests.get(url)
    time.sleep(5)
    html = driver.content
    soup = bs(html, 'html.parser')
    info = soup.find_all(class_='info')
    tit = info[0].find_all('h1')
    print(tit[0].get_text())
    # tituloen = str(tit[0].get_text()).strip()
    # titulo = quitar_simbolos_especiales(ts.google(tituloen, to_language='es'))
    titulo = ts.google(str(tit[0].get_text()).strip(), to_language='es')
    print(titulo)
    small = str(info[0].find_all(class_='small')[0].find_all('span')[0].get_text()).split('：')[1]
    autor = ts.google(small, to_language='es')
    intro = ' '.join(info[0].find_all(class_='intro')[0].stripped_strings)
    descripcion = ts.google(intro, to_language='es')
    print(descripcion)
    if titulo.lower().replace(' ', '_').strip() + '_tablecontents.csv' not in os.listdir(
            os.path.join(path, 'tableofcontents')):
        lista_p = soup.find_all(class_='listmain')[0].find_all('a')
        # print(lista_p)
        for i in range(len(lista_p)):
            if 'javascript' not in lista_p[i].get('href'):
                tit_cap = ts.google(lista_p[i].get_text(), to_language='es')
                url_cap = lista_p[i].get('href')
                print(tit_cap, url_cap)
                listaCapitulos.append([tit_cap, url_cap])
        escribirtablecontents(titulo.lower().replace(' ', '_').strip(), listaCapitulos)
    else:
        print('Ya Existe tablecontents')


def obtenercapitulotable(limite, listacap):
    # global opciones
    datos2 = []
    # listacap = pd.read_csv(titulo.replace(' ', '_').strip() + '_tablecontents.csv', sep=';',
    #                        quotechar='"')
    limitecap = len(listacap['nombrecap'])
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

    if titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn + '.csv' not in os.listdir(
            os.path.join(path, 'chapters')):
        if x < limitecap:
            # print(x,y,inin,finn)
            for i in range(x, y + 1):
                if i < limitecap:
                    print('https://www.bqg70.com' + listacap['urlcap'][i])
                    driver = requests.get('https://www.bqg70.com' + listacap['urlcap'][i])
                    html = driver.content
                    soup = bs(html, 'html.parser')
                    content_chap = soup.find_all(id='chaptercontent')[0].get_text(separator='\n', strip=True).split(
                        '\n')[0:-3]
                    text_warp = ''
                    content_chap_es = ''
                    for cc in content_chap:
                        if len(text_warp) + len(cc) < 5000:
                            text_warp += cc + '\n'
                        else:
                            content_chap_es += ts.google(text_warp, to_language='es')
                            text_warp = ''
                    content_chap_es += ts.google(text_warp, to_language='es')
                    # print(content_chap_es)
                    datos2.append([listacap['nombrecap'][i], content_chap_es.replace('\n', ' <br> ')])
            escribircapitulotable(titulo.lower().replace(' ', '_').strip() + '_' + inin + '_' + finn, datos2)
        return 'True'
    else:
        return 'False'


def crearepub():
    global titulo
    global tituloen
    global autor
    global descripcion
    global ext
    listaarchivos = sorted(os.listdir())
    total1 = len(listaarchivos)
    # print(path)

    listaarchivos = sorted(os.listdir(path))
    total1 = len(listaarchivos)
    # print(path)
    file_newname_newfile = ''
    if titulo.lower().replace(' ', '_') not in os.listdir(os.path.join(path, 'images')):
        ext = '.jpg'
        google_crawler = GoogleImageCrawler()
        # filters = dict(size='small')
        google_crawler.crawl(keyword=titulo, max_num=1)
        time.sleep(5)
        listaarchivos2 = sorted(os.listdir(os.path.join(path, 'images')))
        for k in range(len(listaarchivos2)):
            if '000001' in listaarchivos2[k]:
                ext = listaarchivos2[k][-4:]
                # print(ext,listaarchivos2[k])
                file_oldname = os.path.join(path, 'images', ('000001' + ext))
                file_newname_newfile = os.path.join(path, 'images', titulo.lower().replace(' ', '_') + ext)
                os.rename(file_oldname, file_newname_newfile)
    else:
        file_newname_newfile = titulo.lower().replace(' ', '_') + ext
        print(titulo.lower().replace(' ', '_') + ext)

    book = epub.EpubBook()
    # set metadata
    book.set_identifier('id123456')
    if os.path.isfile(os.path.join(path, 'images', (titulo.lower().replace(' ', '_') + ext))):
        book.set_cover('cover.jpg',
                       open((os.path.join(path, 'images', (titulo.lower().replace(' ', '_') + ext))),
                            'rb').read())
    book.set_title(titulo)
    book.set_language('es')
    book.add_author(autor)

    dfs = []
    cs = ()
    if titulo.lower().replace(' ', '_') + '.epub' not in os.listdir(os.path.join(path, 'epub')):
        # chapters_csv = [match for match in os.listdir(os.path.join(path, 'chapters')) if
        #                 titulo.lower().replace(' ', '_') in match]
        chapters_csv = sorted(glob.glob(os.path.join(path, 'chapters', titulo.lower().replace(' ', '_') + '*')))
        for chap_csv in chapters_csv:
            dfs.append(pd.read_csv(os.path.join(path, 'chapters', chap_csv),
                                   sep=';',
                                   quotechar='"'))
        dFrame = pd.concat(dfs, ignore_index=True)
        dFrame.to_csv(os.path.join(path, 'completes', titulo.lower().replace(' ', '_') + '_complete.csv'),
                      sep=';',
                      quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC,
                      index=False)
        limitecap = len(dFrame['nombrecap'])
        c = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='es')
        c.content = u'<h1>%s</h1>' \
                    u'<p>%s</p>' \
                    u'<br>' \
                    u'<img src="%s" width="200" height="200">' % (titulo,
                                                                  descripcion,
                                                                  os.path.join(path, 'images', file_newname_newfile))
        # add chapter
        book.add_item(c)
        for i in range(limitecap):
            # print(dFrame['nombrecap'][i])
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
            c.content = u'<h1>%s</h1><p>%s</p>' % (str(dFrame['nombrecap'][i]), str(dFrame['texto'][i]))
            # add chapter
            book.add_item(c)
            cs += (c,)
        book.toc = (
            epub.Link('intro.xhtml', 'Introduction', 'intro'),
            (
                epub.Section('Introduction', 'intro.xhtml'),
                (cs)
            )
        )

        # add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # define CSS style
        style = 'BODY {color: white;}'
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

        # add CSS file
        book.add_item(nav_css)

        # basic spine
        sp = []
        sp.append('nav')
        for j in cs:
            sp.append(j)
        # print(sp)
        book.spine = sp
        # write to the file
        epub.write_epub(os.path.join(path, 'epub', titulo.lower().replace(' ', '_') + '.epub'), book, {})
        # print(dFrame)
        print('archivo epub de ', titulo, ' creado')
        titulo = ''
        autor = ''
        descripcion = ''


def main():
    global titulo
    global tituloen
    global autor
    global descripcion
    global listaCapitulos
    global genero
    links = [
        'https://www.bqg70.com/book/82808/',
        'https://www.bqg70.com/book/6303/',
        'https://www.bqg70.com/book/128983/',
    ]

    for link in links:
        print(link)
        listaCapitulos = []
        obtenernumpagurl(str(link))
        if titulo.lower().replace(' ', '_').strip() + '_complete.csv' not in os.listdir(
                os.path.join(path, 'completes')):
            listnovelcaps = pd.read_csv(
                os.path.join(path, 'tableofcontents', titulo.lower().replace(' ', '_') + '_tablecontents.csv'),
                sep=';',
                quotechar='"')
            # print(listnovelcaps)
            for i in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
                if obtenercapitulotable(i + 1, listnovelcaps) == 'True':
                    time.sleep(1)
        crearepub()

    return False


band = True

while band == True:
    try:
        band = main()
    except Exception as e:
        print('\nhubo un error\n', e.args)
        time.sleep(3)
        band = True
