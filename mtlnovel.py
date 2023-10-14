import datetime
import os
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pandas as pd
import undetected_chromedriver as uc
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

valcharacter = ' 0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúäëïöü?'
titulo = ''
tituloen = ''
cantidadcaptitulo = 0
listaCapitulos = []
autor = ''
descripcion = ''
genero = []
ext = ''
page = ''
#novelname = 'https://www.readwn.com/e/extend/fy.php?page=%s&wjm=%s'

# opciones = Options()
# opciones.headless = True
servicio = Service(executable_path=ChromeDriverManager().install())


def quitar_simbolos_especiales(title):
    titlenew = ''
    for j in range(len(title)):
        if title[j] in valcharacter:
            titlenew += title[j]
    return titlenew


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
    titulo0 = titulo0.replace(' ', '_').strip()
    df = pd.DataFrame(data=datos, columns=['nombrecap', 'urlcap'])
    df.to_csv(titulo0 + '_tablecontents.csv', sep=';', quotechar='"',
              quoting=csv.QUOTE_NONNUMERIC, index=False)


def escribircapitulotable(titulo, datos2):
    titulo = titulo.replace(' ', '_').strip()
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
    descripcion = ''
    driver = webdriver.Chrome(service=servicio)
    time.sleep(3)
    driver.get(url)
    soup = bs(driver.page_source, 'html.parser')
    driver.close()
    tit = soup.find_all(class_='entry-title')
    tituloen = str(tit[0].get_text()).strip()
    titulo = quitar_simbolos_especiales(ts.server.google(tituloen, to_language='es'))
    titulo = ts.server.google(tituloen, to_language='es')
    print(titulo)
    aut = soup.find_all(id='author')
    autor = str(aut[0].get_text()).strip()
    print(autor)
    descrip = soup.find_all(class_='desc')
    descripcion = ts.server.google(descrip[0].get_text().strip(), to_language='es')
    print(descripcion)


def obtenercapitulotable(limite):
    # global opciones
    datos2 = []
    listacap = pd.read_csv(titulo.replace(' ', '_').strip() + '_tablecontents.csv', sep=';',
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
        if (titulo.replace(' ', '_') + '_' + inin + '_' + finn) in str(
                listaarchivos[i]):
            b = 1
    if b == 0:
        if x < limitecap:
            # print(x,y,inin,finn)
            for i in range(x, y + 1):
                if i < limitecap:
                    op = Options()
                    op.headless = True
                    print(listacap['urlcap'][i])
                    driver = uc.Chrome(use_subprocess=True, service=servicio)
                    # driver = webdriver.Chrome(service=servicio, options=op)
                    # driver.minimize_window()
                    driver.get(listacap['urlcap'][i])
                    time.sleep(12)
                    html = driver.page_source
                    soup = bs(html, 'html.parser')
                    driver.close()
                    tit_chap = soup.find_all(class_='name-chapter')
                    titulo_cap = ''
                    for tc in tit_chap:
                        titulo_cap += tc.get_text().strip()
                    titulo_cap = ts.google(titulo_cap, to_language='es')
                    print(titulo_cap)
                    content_chap = soup.find_all('p')
                    txt_trad = []
                    for j in range(len(content_chap)):
                        txt = ''
                        txt = str(content_chap[j].get_text()).strip().rstrip()
                        if txt != '':
                            txt_trad.append(ts.google(txt, to_language='es'))
                    datos2.append([titulo_cap, ' <br> '.join(txt_trad)])
                    print(' '.join(txt_trad[0:5]))
            escribircapitulotable(titulo.replace(' ', '_') + '_' + inin + '_' + finn, datos2)
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
        if (titulo.replace(' ', '_')) in listaarchivos2[i]:
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
                    path, (titulo.replace(' ', '_') + ext))
                os.rename(file_oldname, file_newname_newfile)
    else:
        print(titulo.replace(' ', '_') + ext)

    book = epub.EpubBook()
    # set metadata
    book.set_identifier('id123456')
    if os.path.isfile(os.path.join(path, (titulo.replace(' ', '_') + ext))):
        book.set_cover('cover.jpg',
                       open((os.path.join(path, (titulo.replace(' ', '_') + ext))), 'rb').read())
    book.set_title(titulo.upper())
    book.set_language('es')
    book.add_author(autor)

    dfs = []
    cs = ()
    bandera = True
    if titulo.replace(' ', '_') + '_complete.csv' not in listaarchivos:
        for i in range(total1):
            if titulo.replace(' ', '_') in str(listaarchivos[i]):
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
        dFrame['idioma'] = 'en'
        dFrame.to_csv((titulo.replace(' ', '_') + '_complete.csv'), sep=';', quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC, index=False)
    else:
        print('compilado existe')
        dFrame = pd.read_csv((titulo.replace(' ', '_') + '_complete.csv'), sep=';', quotechar='"')

    limitecap = len(dFrame['nombrecap'])

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
    epub.write_epub(titulo.replace(' ', '_').strip() + '.epub', book, {})
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
        'https://www.mtlnovel.com/what-if-i-cant-die/',
    ]

    for link in links:
        print(link)
        listaCapitulos = []
        obtenernumpagurl(str(link))
        # if titulo.replace(' ', '_') + '_complete.csv' not in os.listdir():
        #     listnovelcaps = pd.read_csv(titulo.replace(' ', '_') + '_tablecontents.csv', sep=';', quotechar='"')
        #     # print(listnovelcaps)
        #     for i in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
        #         if obtenercapitulotable(i + 1) == 'True':
        #             time.sleep(1)
        # crearepub()
    # titulo = ''
    # cantidadcaptitulo = 0
    # listaCapitulos = []
    # autor = ''
    # descripcion = ''
    # genero = []
    # ext = ''
    return False


band = True
while band == True:
    try:
        band = main()
    except Exception as e:
        print('\nhubo un error\n', e.args)
        time.sleep(3)
        band = True
