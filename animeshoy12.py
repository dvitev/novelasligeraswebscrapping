import json
import os
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import certifi
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
import csv
from googletrans import Translator
from ebooklib import epub
import time
from urllib.parse import urlparse
from icrawler.builtin import GoogleImageCrawler
import os
import translators as ts

titulo = ''
tituloen = ''
cantidadcaptitulo = 0
listaCapitulos = []
autor = ''
descripcion = ''
genero = ''
ext = ''


# opciones = Options()
# opciones.headless = True
# servicio = Service(ChromeDriverManager().install())


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


def escribirtablecontents(titulo0, datos):
    titulo0 = titulo0.replace(' ', '_').replace(':', '').strip()
    df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
    df.to_csv(titulo0 + '_tablecontents.csv', sep=';', quotechar='"',
              quoting=csv.QUOTE_NONNUMERIC, index=False)


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
    global tituloen
    global autor
    # global opciones
    global genero
    descripcion = ''
    a = ''
    # print(url)
    # driver = webdriver.Chrome(service=servicio, options=opciones)
    # driver.minimize_window()
    # driver.get(url)
    # html = driver.page_source
    html = requests.get(url)
    soup = bs(html.text, 'html.parser')
    # driver.close()
    # print(soup)
    tit = soup.find_all(class_='post-title')
    tituloen = str(tit[0].get_text()).strip().replace(' NOVELA ESPAÑOL', '')
    titulo = ts.google(tituloen, from_language='en', to_language='es')
    print(titulo)
    autor = 'N/A'
    descripp = 'Cuando abrí los ojos, estaba dentro de una novela. [El Nacimiento de un Héroe] [El Nacimiento de un Héroe] fue una novela centrada en las aventuras del personaje principal, Choi Han, junto con el nacimiento de los numerosos héroes del continente. Pero no piensen que he tomado el papel del mismo Choi Han, qué bonito sería, ¿verdad? Lamentablemente, me convertí en parte de esa novela como la Basura de la Familia del Conde. Y el problema en todo esto es el hecho de que este idiota en el que me he convertido no sabe en donde está parado y se termina metiendo con Choi Han, solo para ser golpeado hasta ser convertido en pulpa. "...Esto va de mal en peor". Pero aún así creo que valdrá la pena intentar hacer de esta mi nueva vida.'
    print(descripp)


def obtenertablecontents(url):
    global listaCapitulos
    global opciones
    datos = []
    html = requests.get(url)
    soup = bs(html.text, 'html.parser')
    soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))
    chapter = soup.find_all(class_='post-body')
    chapter_a = chapter[0].find_all('a')
    for i in range(len(chapter_a)):
        cap_tit = chapter_a[i].get_text()
        cap_url = chapter_a[i].get('href')
        if 'Capitulo' in cap_tit:
            print(cap_tit, cap_url)
            listaCapitulos.append(
                [cap_tit, str(cap_url)])


def obtenercapitulotable(limite):
    # global opciones
    datos2 = []
    listacap = pd.read_csv(titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv', sep=';',
                           quotechar='"')
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
        if (titulo.replace(' ', '_').replace(':', '') + '_' + inin + '_' + finn) in str(
                listaarchivos[i]):
            b = 1
    if b == 0:
        if x < limitecap:
            # print(x,y,inin,finn)
            for i in range(x, y + 1):
                if i < limitecap:

                    print(listacap['nombrecap'][i], listacap['urlcap'][i])
                    # driver = webdriver.Chrome(
                    #     service=servicio, options=opciones)
                    # driver.minimize_window()
                    # driver.get(listacap['urlcap'][i])
                    # html = driver.page_source
                    html = requests.get(listacap['urlcap'][i])
                    soup = bs(html.text, 'html.parser')
                    # driver.close()
                    cha_content = soup.find_all(class_='post-body')
                    cha_content_span = cha_content[0].find_all('span')
                    txt_trad = []
                    for j in range(len(cha_content_span)):
                        txt = str(cha_content_span[j].get_text()).strip().rstrip().replace(u'\xa0', ' ')
                        if txt != '':
                            if 'Anterior - Índice - Siguiente' not in txt:
                                txt_trad.append(txt)
                    datos2.append([listacap['nombrecap'][i], ' '.join(txt_trad)])
                    escribircapitulotable(titulo.replace(' ', '_').replace(':', '') + '_' + inin + '_' + finn, datos2)
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
        if (titulo.replace(' ', '_').replace(':', '')) in listaarchivos2[i]:
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
                    path, (titulo.replace(' ', '_').replace(':', '') + ext))
                os.rename(file_oldname, file_newname_newfile)
    else:
        print(titulo.replace(' ', '_').replace(':', '') + ext)

    book = epub.EpubBook()
    # set metadata
    book.set_identifier('id123456')
    if os.path.isfile(os.path.join(path, (titulo.replace(' ', '_').replace(':', '') + ext))):
        book.set_cover('cover.jpg',
                       open((os.path.join(path, (titulo.replace(' ', '_').replace(':', '') + ext))), 'rb').read())
    book.set_title(titulo.upper())
    book.set_language('es')
    book.add_author(autor)

    dfs = []
    cs = ()
    for i in range(total1):
        if titulo.replace(' ', '_').replace(':', '') in str(listaarchivos[i]):
            if 'tablecontents' not in str(listaarchivos[i]) and 'complete' not in str(
                    listaarchivos[i]) and '.jpg' not in str(listaarchivos[i]) and '.epub' not in str(listaarchivos[i]):
                print(listaarchivos[i])
                dfs.append(pd.read_csv(
                    listaarchivos[i], sep=';', quotechar='"'))
    dFrame = pd.concat(dfs, ignore_index=True)
    limitecap = len(dFrame['nombrecap'])
    dFrame.to_csv((titulo.replace(' ', '_').replace(':', '') + '_complete.csv'), sep=';', quotechar='"',
                  quoting=csv.QUOTE_NONNUMERIC,
                  index=False)
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
        # txt = Traduccion(str(dFrame['texto'][i]))
        # txt = ts.google(str(dFrame['texto'][i]),
        #                 from_language='en',
        #                 to_language='es',
        #                 if_ignore_limit_of_length=True,
        #                 limit_of_length=500000)
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
    epub.write_epub(titulo.replace(' ', '_').replace(':', '').strip() + '.epub', book, {})
    # print(dFrame)
    print('archivo epub de ', titulo, ' creado')
    titulo = ''
    autor = ''
    descripcion = ''


links = ['https://animeshoy12.blogspot.com/p/trash-of-counts-family-novela-espanol.html',
         'https://animeshoy12.blogspot.com/p/nano-machine-novela-espanol.html']
for link in links:
    print(link)
    listaCapitulos = []
    obtenernumpagurl(str(link))
    urllist = []
    path = os.getcwd()
    listaarchivos = sorted(os.listdir(path))
    band1 = True
    for list in listaarchivos:
        if str(titulo.replace(' ', '_').replace(':', '').strip() + '.epub') in str(list):
            band1 = False
            break
    if band1:
        if (titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv') not in listaarchivos:
            obtenertablecontents(link)
            print(titulo, len(listaCapitulos))
            escribirtablecontents(titulo, listaCapitulos)
        listnovelcaps = pd.read_csv(
            titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv', sep=';',
            quotechar='"')
        # print(listnovelcaps)
        for i in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
            if obtenercapitulotable(i + 1) == 'True':
                time.sleep(3)
                # break
        crearepub()
    titulo = ''
    cantidadcaptitulo = 0
    listaCapitulos = []
    autor = ''
    descripcion = ''
    genero = ''
    ext = ''
