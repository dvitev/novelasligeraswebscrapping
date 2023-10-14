import os
import glob
from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
from googletrans import Translator
# binary = FirefoxBinary(r'C:\Program Files\Mozilla Firefox\firefox.exe')
from webdriver_manager.firefox import GeckoDriverManager
from ebooklib import epub
import time
from urllib.parse import urlparse
from icrawler.builtin import GoogleImageCrawler
import translators as ts
import undetected_chromedriver as uc

valcharacter = ' 0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúäëïöü'
item = 0
titulo = ''
tituloen = ''
cantidadcaptitulo = 0
listaCapitulos = []
autor = ''
descripcion = ''
opciones = Options()
opciones.headless = True
# servicio=Service('/home/dvitev/chromedriver_linux64/chromedriver')
# servicio = Service(ChromeDriverManager().install())
path = os.getcwd()


# servicio = Service('usr/bin/chromium-browser')
# Servicio = Service('usr/bin/chromedriver')

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
    global item
    global descripcion
    global titulo
    global autor
    global opciones
    descripcion = ''
    a = ''
    # print(url)
    op = webdriver.ChromeOptions()
    op.headless = True
    # driver = uc.Chrome(use_subprocess=True, service=servicio)
    driver = webdriver.Chrome(options=op)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    tit = soup.find_all(class_='titulo-novela')
    titulo = quitar_simbolos_especiales(str(tit[0].string).strip())
    print(titulo)
    aut = soup.find_all(class_='author-content')
    autor = aut[0].string
    descrip = soup.find_all(class_='summary__content')
    descripp = descrip[0].find_all('p')
    for i in range(len(descripp)):
        if str(descripp[i].string) == 'None':
            break
        elif 'javascript' in descripp[i].string:
            break
        else:
            descripcion += descripp[i].string
    lcp_paginator = soup.find_all(class_='lcp_paginator')
    try:
        lcp_paginator_li = lcp_paginator[0].find_all('li')
        # print(lcp_paginator_li[-2].string)
        return lcp_paginator_li[-2].string
    except:
        return 1


def obtenertablecontents(url):
    global listaCapitulos
    global opciones
    datos = []
    op = webdriver.ChromeOptions()
    op.headless = True
    # driver = uc.Chrome(use_subprocess=True, service=servicio)
    driver = webdriver.Chrome(options=op)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    lcp_catlist = soup.find_all(class_='lcp_catlist')
    lcp_catlist_a = lcp_catlist[0].find_all('a')
    for i in range((len(lcp_catlist_a) - 1), -1, -1):
        listaCapitulos.append([lcp_catlist_a[i].string, str(lcp_catlist_a[i].get('href'))])


def obtenercapitulotable(limite, listacap):
    global opciones
    datos2 = []
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
    print((titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn + '.csv'))

    if (titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn + '.csv') not in os.listdir(
            os.path.join(path, 'chapters')):
        if x < limitecap:
            # print(x,y,inin,finn)
            for i in range(x, y + 1):
                if i < limitecap:
                    txt = ''
                    print(listacap['nombrecap'][i], listacap['urlcap'][i])
                    op = webdriver.ChromeOptions()
                    op.headless = True
                    # driver = uc.Chrome(use_subprocess=True, service=servicio)
                    driver = webdriver.Chrome(options=op)
                    driver.minimize_window()
                    driver.get(listacap['urlcap'][i])
                    html = driver.page_source
                    soup = bs(html, 'html.parser')
                    driver.close()
                    p_chapter_c = soup.find_all('p')
                    # print(len(p_chapter_c))
                    for j in range(len(p_chapter_c)):
                        if str(p_chapter_c[j].get_text()).strip() != 'None':
                            if 'tunovelaligera' not in str(p_chapter_c[j].get_text()).strip():
                                if 'Notifications' not in str(p_chapter_c[j].get_text()).strip():
                                    if 'TNL' not in str(p_chapter_c[j].get_text()).strip():
                                        txt += str(p_chapter_c[j].get_text()).strip() + ' <br> '
                        # print(str(p_chapter_c[i].string).strip())
                    # print(txt)
                    datos2.append([listacap['nombrecap'][i], txt])
            escribircapitulotable(titulo.lower().replace(' ', '_') + '_' + inin + '_' + finn, datos2)
        return 'True'
    else:
        return 'False'


def crearepub():
    global titulo
    global autor
    global descripcion
    global ext
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


# links = ['https://tunovelaligera.com/novelas/emperors-domination-tnl/']
links = [
         # 'https://tunovelaligera.com/novelas/omniscient-readers-viewpoint/',
         # 'https://tunovelaligera.com/novelas/i-shall-seal-the-heavens-cielos/',
         # 'https://tunovelaligera.com/novelas/return-of-the-former-hero-tnl/',
         # 'https://tunovelaligera.com/novelas/only-i-am-a-necromancer/',
         # 'https://tunovelaligera.com/novelas/seoul-stations-necromancer/',
         # 'https://tunovelaligera.com/novelas/una-estrella-renace-el-regreso-de-la-reina-alexa/',
         # 'https://tunovelaligera.com/novelas/el-renacimiento-de-la-reina-del-apocalipsis-ponte-de-rodillas-joven-emperador/',
         # 'https://tunovelaligera.com/novelas/responde-me-diosa-orgullosa/',
         # 'https://tunovelaligera.com/novelas/la-maestra-de-los-elixires/',
         # 'https://tunovelaligera.com/novelas/back-then-i-adored-you/',
         # 'https://tunovelaligera.com/novelas/insanely-pampered-wife-divine-doctor-fifth-young-miss-tnla-3a/',
         # 'https://tunovelaligera.com/novelas/trial-marriage-husband-need-to-work-hard/',
         # 'https://tunovelaligera.com/novelas/ghost-emperor-wild-wife-dandy-eldest-miss-tnla/',
         # 'https://tunovelaligera.com/novelas/a-billion-stars-cant-amount-to-you-mia/',
         # 'https://tunovelaligera.com/novelas/the-99th-divorce-tnla/',
         # 'https://tunovelaligera.com/novelas/evil-emperors-wild-consort-tnla/',
         # 'https://tunovelaligera.com/novelas/the-demonic-king-chases-his-wife-the-rebellious-good-for-nothing-miss/',
         # 'https://tunovelaligera.com/novelas/my-cold-and-elegant-ceo-wife-tns/',
         # 'https://tunovelaligera.com/novelas/venerated-venomous-consort/',
         # 'https://tunovelaligera.com/novelas/adorable-treasured-fox-divine-doctor-mother-overturning-the-heavens/',
         # 'https://tunovelaligera.com/novelas/el-doctor-granjero-piadoso-un-marido-arrogante-que-no-se-puede-permitirse-ofender/',
         # 'https://tunovelaligera.com/novelas/robando-tu-corazon/',
         # 'https://tunovelaligera.com/novelas/cultivo-de-espiritus/',
         # 'https://tunovelaligera.com/novelas/reverend-insanity-tnla-2/',
         # 'https://tunovelaligera.com/novelas/the-good-for-nothing-seventh-young-lady/',
         # 'https://tunovelaligera.com/novelas/wdqk-tnl/',
         # 'https://tunovelaligera.com/novelas/the-death-mage/',
         # 'https://tunovelaligera.com/novelas/gourmet-of-another-world-tnla-1/',
         # 'https://tunovelaligera.com/novelas/reincarnation-of-the-strongest-sword-god-mia/',
         # 'https://tunovelaligera.com/novelas/everyone-else-is-a-returnee/',
         # 'https://tunovelaligera.com/novelas/death-march-tnl/',
         # 'https://tunovelaligera.com/novelas/omniscient-readers-viewpoint/',
         # 'https://tunovelaligera.com/novelas/superstars-of-tomorrow-tnla-2s/',
         # 'https://tunovelaligera.com/novelas/genius-doctor-black-belly-miss-tnla/',
         # 'https://tunovelaligera.com/novelas/el-divino-emperador-de-la-muerte/',
         # 'https://tunovelaligera.com/novelas/cultivation-chat-group-tnla/',
         # 'https://tunovelaligera.com/novelas/reincarnated-as-a-dragons-tnl/',
         # 'https://tunovelaligera.com/novelas/the-legendary-mechanic-tnla/',
         # 'https://tunovelaligera.com/novelas/kog-tnla/',
         # 'https://tunovelaligera.com/novelas/ex-hero-candidates/',
         # 'https://tunovelaligera.com/novelas/divine-doctor-daughter-of-the-first-wife/',
         # 'https://tunovelaligera.com/novelas/poison-genius-consort/',
         # 'https://tunovelaligera.com/novelas/prodigiously-amazing-weaponsmith-tnla/',
         # 'https://tunovelaligera.com/novelas/omnipotent-sage/',
         # 'https://tunovelaligera.com/novelas/the-record-of-unusual-creatures/',
         # 'https://tunovelaligera.com/novelas/pmg-tnl/',
         # 'https://tunovelaligera.com/novelas/nine-star-hegemon-body-art/',
         # 'https://tunovelaligera.com/novelas/tempest-of-the-stellar-war-tnla-a/',
         # 'https://tunovelaligera.com/novelas/doomsday-wonderland/',
         # 'https://tunovelaligera.com/novelas/ultimate-scheming-system-tn/',
         # 'https://tunovelaligera.com/novelas/versatile-mage/', 'https://tunovelaligera.com/novelas/nine-sun-god-king/',
         # 'https://tunovelaligera.com/novelas/mga/',
         # 'https://tunovelaligera.com/novelas/la-encantadora-de-la-medicina-con-el-nino-desafiante-del-cielo-y-el-padre-del-vientre-negro/',
         # 'https://tunovelaligera.com/novelas/the-sage-who-transcended-samsara/',
         # 'https://tunovelaligera.com/novelas/my-master-disconnected-yet-again/',
         # 'https://tunovelaligera.com/novelas/la-consorte-venenosa-del-malvado-emperador/',
         # 'https://tunovelaligera.com/novelas/the-monk-that-wanted-to-renounce-asceticism/',
         # 'https://tunovelaligera.com/novelas/aun-asi-esperame/',
         # 'https://tunovelaligera.com/novelas/mi-padre-es-el-principe-azul-de-la-galaxia-ta/',
         # 'https://tunovelaligera.com/novelas/absolute-great-teacher/',
         # 'https://tunovelaligera.com/novelas/everybody-is-kung-fu-fighting-while-i-started-a-farm/',
         # 'https://tunovelaligera.com/novelas/bank-of-the-universe/',
         # 'https://tunovelaligera.com/novelas/dual-cultivation-tns/',
         # 'https://tunovelaligera.com/novelas/swallowed-star-tnla',
         # 'https://tunovelaligera.com/novelas/emperors-domination-tnl/',
         # 'https://tunovelaligera.com/novelas/bringing-the-farm-to-live-in-another-world/',
         # 'https://tunovelaligera.com/novelas/my-disciple-died-yet-again/',
         # 'https://tunovelaligera.com/novelas/sonomono-nochi-ni-tnl/',
         # 'https://tunovelaligera.com/novelas/monarca-del-tiempo/',
         # 'https://tunovelaligera.com/novelas/rebirth-of-the-urban-immortal-cultivator/',
         # 'https://tunovelaligera.com/novelas/de-hecho-soy-un-gran-cultivador/',
         # 'https://tunovelaligera.com/novelas/against-the-gods-tnl/',
         # 'https://tunovelaligera.com/novelas/xian-ni-tnl/',
         # 'https://tunovelaligera.com/novelas/god-and-devil-world-tnl/',
         # 'https://tunovelaligera.com/novelas/martial-peak/',
         # 'https://tunovelaligera.com/novelas/i-have-a-mansion-in-the-post-apocalyptic-world/',
         # 'https://tunovelaligera.com/novelas/super-gene-tnla/',
         # 'https://tunovelaligera.com/novelas/tsuki-ga-michibiku-isekai-douchuu-tnl/',
    ]
for link in links:
    print(link)
    listaCapitulos = []
    numpag = int(obtenernumpagurl(str(link)))
    urllist = []
    if titulo.lower().replace(' ', '_') + '.epub' not in os.listdir(path + '/epub'):
        if (titulo.lower().replace(' ', '_') + '_tablecontents.csv') not in os.listdir(
                os.path.join(path, 'tableofcontents')):
            for i in range(numpag, 0, -1):
                obtenertablecontents(str(link) + '?lcp_page0=' + str(i))
            # print(titulo, len(listaCapitulos))
            escribirtablecontents(titulo.lower().replace(' ', '_'), listaCapitulos)
            listacapnovel = pd.DataFrame(data=listaCapitulos, columns=['nombrecap', 'urlcap'])
            print(listacapnovel)
        else:
            listacapnovel = pd.read_csv(os.path.join(
                path, 'tableofcontents', titulo.lower().replace(' ', '_') + '_tablecontents.csv'),
                sep=';',
                quotechar='"')
            print(listacapnovel)
        for i in range(int(len(listacapnovel['nombrecap']) / 200) + 1):
            if obtenercapitulotable(i + 1, listacapnovel) == 'True':
                time.sleep(3)
        crearepub()
    item = 0
    titulo = ''
    cantidadcaptitulo = 0
    listaCapitulos = []
    autor = ''
    descripcion = ''
