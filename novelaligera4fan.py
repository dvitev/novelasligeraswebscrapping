import datetime
import json
import os
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import certifi
import undetected_chromedriver as uc
from selenium import webdriver
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


def Traduccion(text):
    translator = Translator()
    translation = translator.translate(text, dest='es', src='en')
    return translation.text


def Traduccionlist(text):
    translator = Translator()
    translations = translator.translate(text, dest='es', src='en')
    rtext = []
    for trans in translations:
        rtext.append(trans.text)
        # print(trans.text)
    return rtext


def comprobarurl(url):
    o = urlparse(url)
    # print(o)
    return str(o.scheme) + '://' + str(o.netloc)


def escribirtablecontents(titulo0, datos):
    titulo0 = titulo0.replace(' ', '_').replace(':', '').strip()
    df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
    df.to_csv(titulo0 + '_tablecontents.csv', sep=';', quotechar='"',
              quoting=csv.QUOTE_NONNUMERIC, index=False)


def arraytopandas(datos, colnames):
    return pd.DataFrame(data=datos, columns=colnames)


def escribircapitulotable(titulo, datos2):
    titulo = titulo.replace(' ', '_').replace(':', '').strip()
    df2 = pd.DataFrame(data=datos2, columns=['nombrecap', 'texto'])
    df2.to_csv(titulo + '.csv', sep=';', quotechar='"',
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
    genero = []
    op = uc.ChromeOptions()
    op.headless = True
    descripcion = ''
    a = ''
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    # driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    # driver = webdriver.Chrome(service=servicio, options=op)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    aut = soup.find_all(class_='post-content_item')
    for i in range(len(aut)):
        if 'Author' in aut[i].get_text():
            autor = aut[i].find_all('div')[1].get_text()
    # print(autor)
    descrip = soup.find_all(class_='summary__content')
    descripcion = descrip[0].get_text()
    # print(descripcion)


def obtenertablecontents(url):
    global listaCapitulos
    global page
    global novelname

    listaCapitulos = []
    op = uc.ChromeOptions()
    op.headless = True

    # datos = []
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    # driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    # driver = webdriver.Chrome(service=servicio, options=op)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    # dominio = comprobarurl(url)
    # urls = []
    listing_chapters_wrap = soup.find_all(class_='listing-chapters_wrap')
    a_list_chapter = listing_chapters_wrap[0].find_all('a')
    for i in range(len(a_list_chapter)-1, -1, -1):
        titulocap = quitar_simbolos_especiales(a_list_chapter[i].get_text().strip())
        urlcap = str(a_list_chapter[i].get('href'))
        listaCapitulos.append([titulocap, urlcap])
        # print(titulocap, urlcap)


def obtenercapitulotable(limite):
    # global opciones
    datos2 = []
    listacap = pd.read_csv(titulo + '_tablecontents.csv', sep=';', quotechar='"')
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

    listaarchivos = sorted(os.listdir())
    total1 = len(listaarchivos)
    path = os.getcwd()

    b = 0
    for i in range(total1):
        if (titulo + '_' + inin + '_' + finn) in str(listaarchivos[i]):
            b = 1
    if b == 0:
        if x < limitecap:
            # print(x,y,inin,finn)
            for i in range(x, y + 1):
                if i < limitecap:
                    op = Options()
                    op.headless = True
                    print(listacap['nombrecap'][i], listacap['urlcap'][i])
                    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
                    # driver = webdriver.Chrome(service=servicio, options=op)
                    # driver = webdriver.Chrome(service=servicio, options=op)
                    driver.minimize_window()
                    driver.get(listacap['urlcap'][i])
                    html = driver.page_source
                    soup = bs(html, 'html.parser')
                    driver.close()
                    cha_content = soup.find_all(class_='read-container')

                    datos2.append([listacap['nombrecap'][i], cha_content[0].get_text().strip()])
                    # print(' '.join(txt_trad[0:5]))
            escribircapitulotable(titulo + '_' + inin + '_' + finn, datos2)
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

    path = os.getcwd()
    path += '/images'
    listaarchivos2 = sorted(os.listdir(path))
    total2 = len(listaarchivos2)
    b = 0
    for i in range(total2):
        if titulo in listaarchivos2[i]:
            ext = listaarchivos2[i][-4:]
            b = 1
    if b == 0:
        google_crawler = GoogleImageCrawler()
        # filters = dict(size='small')
        google_crawler.crawl(keyword=tituloen, max_num=1)
        time.sleep(5)
        listaarchivos2 = sorted(os.listdir(path))
        for k in range(len(listaarchivos2)):
            if '000001' in listaarchivos2[k]:
                ext = listaarchivos2[k][-4:]
                # print(ext,listaarchivos2[k])
                file_oldname = os.path.join(path, ('000001' + ext))
                file_newname_newfile = os.path.join(
                    path, (titulo + ext))
                os.rename(file_oldname, file_newname_newfile)
    else:
        print(titulo + ext)

    book = epub.EpubBook()
    # set metadata
    book.set_identifier('id123456')
    if os.path.isfile(os.path.join(path, (titulo + ext))):
        book.set_cover('cover.jpg', open((os.path.join(path, (titulo + ext))), 'rb').read())
    book.set_title(titulo.replace('_',' ').upper())
    book.set_language('es')
    book.add_author(autor)

    dfs = []
    cs = ()
    bandera = True
    if titulo + '_complete.csv' not in listaarchivos:
        for i in range(total1):
            if titulo in str(listaarchivos[i]):
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
        dFrame['idioma'] = 'es'
        dFrame.to_csv((titulo + '_complete.csv'), sep=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC, index=False)
    else:
        print('compilado existe')
        dFrame = pd.read_csv((titulo + '_complete.csv'), sep=';', quotechar='"')
        print(dFrame.head())
    limitecap = len(dFrame['nombrecap'])
    print(limitecap)
    for m in range(limitecap):
        if 'es' not in dFrame['idioma'][m]:
            txten = ''
            txtes = ''
            txtar = str(dFrame['texto'][m]).split('.')
            print(dFrame['nombrecap'][m] + ' ==> Traduciendo ' + str(datetime.datetime.now()))
            for n in range(len(txtar)):
                if (len(txten) + len(txtar[n].strip())) < 3500:
                    txten += txtar[n].strip() + '. '
                else:
                    try:
                        txtes += ts.google(txten, from_language='en', to_language='es')
                    except:
                        txtes += Traduccion(txten)
                    txten = ''
                    txten += txtar[n].strip() + '. '
                if n == len(txtar) - 1:
                    try:
                        txtes += ts.google(txten, from_language='en', to_language='es')
                    except:
                        txtes += Traduccion(txten)
            dFrame['texto'][m] = txtes
            dFrame['idioma'][m] = 'es'
            print(dFrame['nombrecap'][m] + ' ==> Traducido ' + str(datetime.datetime.now()))
            dFrame.to_csv((titulo.replace(' ', '_').replace(':', '') + '_complete.csv'), sep=';', quotechar='"',
                          quoting=csv.QUOTE_NONNUMERIC, index=False)

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
        c = epub.EpubHtml(title=str(
            dFrame['nombrecap'][i]), file_name='chap_' + cp + '.xhtml', lang='es')

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
    epub.write_epub(titulo + '.epub', book, {})
    # print(dFrame)
    print('archivo epub de ', titulo, ' creado')
    titulo = ''
    autor = ''
    descripcion = ''


def quitar_simbolos_especiales(title):
    titlenew = ''
    for j in range(len(title)):
        if title[j] in valcharacter:
            titlenew += title[j]
    return titlenew


def obtener_listado_pagina():
    urlpagina = 'https://novelaligera4fan.com/'
    listanovelas = []
    op = uc.ChromeOptions()
    op.headless = True
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    driver.minimize_window()
    driver.get(urlpagina)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    item_summary = soup.find_all(class_='post-title')
    for i in range(len(item_summary)):
        title = str(item_summary[i].find('a').get_text().strip())
        urlnovela = item_summary[i].find('a').get('href')
        # print(item_summary[i].find('a').get('href'), item_summary[i].find('a').get_text().strip())

        listanovelas.append([quitar_simbolos_especiales(title), urlnovela])

    escribirtablecontents('lista_novelas_novelaligera4fan', listanovelas)
    print(listanovelas)


def main():
    global titulo
    global autor
    global descripcion
    global listaCapitulos
    global genero

    # obtener_listado_pagina()
    path = os.getcwd()
    print(path)
    datanovelas = pd.read_csv(path + '/lista_novelas_novelaligera4fan_tablecontents.csv', sep=';', quotechar='"')
    print(datanovelas.head())
    # input()
    for i in range(len(datanovelas)):
        print(datanovelas['nombrecap'][i], datanovelas['urlcap'][i])
        titulo = str(datanovelas['nombrecap'][i]).replace(' ', '_').strip()
        obtenernumpagurl(str(datanovelas['urlcap'][i]))
        urllist = []
        listaarchivos = sorted(os.listdir(path))
        band1 = True
        if (titulo + '.epub') in listaarchivos:
            band1 = False
        if band1:
            if (titulo + '_tablecontents.csv') not in listaarchivos:
                # print(datanovelas['urlcap'][i])
                obtenertablecontents(datanovelas['urlcap'][i])
                escribirtablecontents(titulo, listaCapitulos)
            listnovelcaps = pd.read_csv(titulo + '_tablecontents.csv', sep=';', quotechar='"')
            for j in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
                if obtenercapitulotable(j + 1) == 'True':
                    time.sleep(3)
            crearepub()
        titulo = ''
        listaCapitulos = []
        autor = ''
        descripcion = ''
        genero = []

    # links = []
    #
    # for link in links:
    #     print(link)
    #     listaCapitulos = []
    #     obtenernumpagurl(str(link))
    #     urllist = []
    #     path = os.getcwd()
    #     listaarchivos = sorted(os.listdir(path))
    #     band1 = True
    #     for list in listaarchivos:
    #         if str(titulo.replace(' ', '_').replace(':', '').strip() + '.epub') in str(list):
    #             band1 = False
    #             break
    #     if band1:
    #         if (titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv') not in listaarchivos:
    #             obtenertablecontents(str(link))
    #             print(titulo, len(listaCapitulos))
    #             escribirtablecontents(titulo, listaCapitulos)
    #         listnovelcaps = pd.read_csv(
    #             titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv', sep=';',
    #             quotechar='"')
    #         # print(listnovelcaps)
    #         for i in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
    #             if obtenercapitulotable(i + 1) == 'True':
    #                 time.sleep(3)
    #         crearepub()
    #     titulo = ''
    #     cantidadcaptitulo = 0
    #     listaCapitulos = []
    #     autor = ''
    #     descripcion = ''
    #     genero = []
    #     ext = ''
    return False


band = True
while band == True:
    try:
        band = main()
    except Exception as e:
        print('\nhubo un error\n', e.args)
        time.sleep(3)
        band = True
