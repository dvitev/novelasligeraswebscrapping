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
    global genero
    genero = []
    op = uc.ChromeOptions()
    op.headless = True
    descripcion = ''
    a = ''
    # driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    tit = soup.find_all(class_='novel-title')
    # print(tit[0])
    tituloen = str(tit[0].get_text()).strip()
    titulo = ts.google(tituloen, from_language='en', to_language='es')
    print(titulo)
    autor = 'N/A'
    descrip = soup.find_all(id='info')
    descripsum = descrip[0].find_all(class_='summary')
    descripp = ts.google(descripsum[0].get_text().strip(), from_language='en', to_language='es')
    print(descripp)
    gen = soup.find_all(class_='categories')
    gen_li = gen[0].find_all('li')
    if len(gen_li) > 0:
        for i in range(len(gen_li)):
            genero.append(str(gen_li[i].get_text()).rstrip().strip().upper())
        print(' - '.join(genero))


def obtenertablecontents(url):
    global listaCapitulos
    global page
    global novelname
    op = uc.ChromeOptions()
    op.headless = True
    url_split = url.split('/')
    url_split_name = str(url_split[-1]).replace('.html', '')
    datos = []
    # driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
    driver.minimize_window()
    driver.get(url)
    html = driver.page_source
    soup = bs(html, 'html.parser')
    driver.close()
    dominio = comprobarurl(url)
    urls = []
    pagination = soup.find_all('ul', class_='pagination')
    pagination_li = pagination[0].find_all('li')
    filters = soup.find_all(class_='filters')
    filters_a = filters[0].find_all('a')
    filters_a_last_split = str(filters_a[-2].get('href')).replace('fy1.php', 'fy.php').split('?')
    filters_a_last_split_second = filters_a_last_split[1].split('&')
    page = ''
    for m in range(len(filters_a_last_split_second[0])):
        if filters_a_last_split_second[0][m].isdigit():
            page += filters_a_last_split_second[0][m]
    # urls.append(str(filters_a[-1].get('href')).replace('fy1.php', 'fy.php'))
    # for l in range(1, len(pagination_li) - 2):
    #     urls.append(str(pagination_li[l].find('a').get('href')).replace('fy1.php', 'fy.php'))
    # print(urls)
    # print(novelname % (page, url_split_name))
    for i in range(int(page) + 1):
        # print(dominio+urls[i])
        op2 = uc.ChromeOptions()
        op2.headless = True
        # driver = uc.Chrome(use_subprocess=True, service=servicio, options=op2, version_main=106)
        driver = uc.Chrome(use_subprocess=True, service=servicio, options=op2, version_main=106)
        driver.minimize_window()
        driver.get(novelname % (i, url_split_name))
        html2 = driver.page_source
        soup2 = bs(html2, 'html.parser')
        driver.close()
        chapter_list = soup2.find_all(class_='chapter-list')
        chapter_list_li = chapter_list[0].find_all('li')
        if len(chapter_list_li) > 0:
            for j in range(len(chapter_list_li)):
                cap_url = dominio + chapter_list_li[j].find('a').get('href')
                cap_tit = ts.google(str(chapter_list_li[j].find('a').find('strong').get_text()).strip(),
                                    from_language='en',
                                    to_language='es')
                print(cap_tit, cap_url)
                listaCapitulos.append([cap_tit, str(cap_url)])


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
                    op = Options()
                    op.headless = True
                    print(listacap['nombrecap'][i], listacap['urlcap'][i])
                    driver = uc.Chrome(use_subprocess=True, service=servicio, options=op, version_main=106)
                    # driver = webdriver.Chrome(service=servicio, options=op)
                    driver.minimize_window()
                    driver.get(listacap['urlcap'][i])
                    html = driver.page_source
                    soup = bs(html, 'html.parser')
                    driver.close()
                    cha_content = soup.find_all(class_='chapter-content')
                    cha_content_p = cha_content[0].find_all('p')
                    txt_trad = []
                    for j in range(len(cha_content_p)):
                        txt = str(cha_content_p[j].get_text()).strip().rstrip()
                        if txt != '':
                            txt_trad.append(txt)
                    datos2.append([listacap['nombrecap'][i], ' '.join(txt_trad)])
                    # print(' '.join(txt_trad[0:5]))
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
    bandera = True
    if titulo.replace(' ', '_').replace(':', '') + '_complete.csv' not in listaarchivos:
        for i in range(total1):
            if titulo.replace(' ', '_').replace(':', '') in str(listaarchivos[i]):
                if 'tablecontents' not in str(listaarchivos[i]) and 'complete' not in str(
                        listaarchivos[i]) and '.jpg' not in str(listaarchivos[i]) and '.epub' not in str(
                    listaarchivos[i]):
                    print(listaarchivos[i])
                    dfs.append(pd.read_csv(
                        listaarchivos[i], sep=';', quotechar='"'))
    else:
        bandera = False
    if bandera:
        print('compilado no existe')
        dFrame = pd.concat(dfs, ignore_index=True)
        dFrame['idioma'] = 'en'
        dFrame.to_csv((titulo.replace(' ', '_').replace(':', '') + '_complete.csv'), sep=';', quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC, index=False)
    else:
        print('compilado existe')
        dFrame = pd.read_csv((titulo.replace(' ', '_').replace(':', '') + '_complete.csv'), sep=';', quotechar='"')
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


def main():
    global titulo
    global tituloen
    global autor
    global descripcion
    global listaCapitulos
    global genero
    links = [
        'https://www.readwn.com/novel/after-10-years-of-chopping-wood-i-am-invincible.html',
    ]
    # 'https://www.readwn.com/novel/im-in-charge-of-scp.html',
    # 'https://www.readwn.com/novel/astral-apostle.html',
    # 'https://www.readwn.com/novel/war-sovereign-soaring-the-heavens.html',
    # 'https://www.readwn.com/novel/i-became-a-progenitor-vampire.html',
    # 'https://www.readwn.com/novel/infinite-evolution.html',
    # 'https://www.readwn.com/novel/all-stars-are-my-food-fans.html',
    # 'https://www.readwn.com/novel/nine-yang-sword-saint.html',
    # 'https://www.readwn.com/novel/unlimited-machine-war.html',
    # 'https://www.readwn.com/novel/i-open-a-store-in-the-end-times.html',
    # 'https://www.readwn.com/novel/forty-millenniums-of-cultivation.html',
    # 'https://www.readwn.com/novel/swallowed-star.html',
    # 'https://www.readwn.com/novel/martial-arts-world.html',
    # 'https://www.readwn.com/novel/i-am-not-the-supreme-god.html',
    # 'https://www.readwn.com/novel/planet-escape.html',
    # 'https://www.readwn.com/novel/super-invincible-battleship.html',
    # 'https://www.readwn.com/novel/era-of-disaster.html',
    # 'https://www.readwn.com/novel/i-have-48-hours-a-day.html',
    # 'https://www.readwn.com/novel/the-emerald-tower.html',
    # 'https://www.readwn.com/novel/star-odyssey.html',
    # 'https://www.readwn.com/novel/bringing-the-farm-to-live-in-another-world.html',
    # 'https://www.readwn.com/novel/flower-master-in-the-city.html',
    # 'https://www.readwn.com/novel/my-dad-is-too-strong.html',
    # 'https://www.readwn.com/novel/the-whole-world-wants-them-to-get-divorced.html',
    # 'https://www.readwn.com/novel/god-level-demon.html',
    # 'https://www.readwn.com/novel/my-master-is-a-god.html',
    # 'https://www.readwn.com/novel/abandoned-peasant-woman-farming-with-a-cute-baby.html',
    # 'https://www.readwn.com/novel/national-film-empress-was-sweet-as-honey.html',
    # 'https://www.readwn.com/novel/the-young-generals-wife-is-mr-lucky.html',
    # 'https://www.readwn.com/novel/super-god-gene.html',
    # 'https://www.readwn.com/novel/cultivation-chat-group.html',
    # 'https://www.readwn.com/novel/the-abandoned-son-runs-rampant.html',
    # 'https://www.readwn.com/novel/empress-running-away-with-the-ball.html',
    # 'https://www.readwn.com/novel/the-demonic-king-chases-his-wife.html',
    # 'https://www.readwn.com/novel/plundering-the-heavens.html',
    # 'https://www.readwn.com/novel/wild-malicious-consort-good-for-nothing-ninth-miss.html',
    # 'https://www.readwn.com/novel/my-cold-and-elegant-ceo-wife.html',
    # 'https://www.readwn.com/novel/perfect-secret-love-the-bad-new-wife-is-a-little-sweet.html',
    # 'https://www.readwn.com/novel/wang-familys-peasant-woman-raising-kids-and-making-wealth.html',
    # 'https://www.readwn.com/novel/adorable-treasured-fox-divine-doctor-mother-overturning-the-heavens.html',
    # 'https://www.readwn.com/novel/heaven-defying-supreme.html',
    # 'https://www.readwn.com/novel/leisurely-beast-world-plant-some-fields-have-some-cubs.html',
    # 'https://www.readwn.com/novel/the-delicate-prince-and-his-shrewd-peasant-consort.html',
    # 'https://www.readwn.com/novel/4-6-billion-year-symphony-of-evolution.html',
    # 'https://www.readwn.com/novel/the-demonic-king-chases-his-wife-the-rebellious-good-for-nothing-miss.html',
    # 'https://www.readwn.com/novel/divine-genius-healer-abandoned-woman-demonic-tyrant-in-love-with-a-mad-little-consort.html',
    # 'https://www.readwn.com/novel/reincarnation-of-the-businesswoman-at-school.html',
    # 'https://www.readwn.com/novel/mesmerizing-ghost-doctor.html',

    for link in links:
        print(link)
        listaCapitulos = []
        obtenernumpagurl(str(link))
        if 'YAOI' not in genero and 'YURI' not in genero:
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
                    obtenertablecontents(str(link))
                    print(titulo, len(listaCapitulos))
                    escribirtablecontents(titulo, listaCapitulos)
                listnovelcaps = pd.read_csv(
                    titulo.replace(' ', '_').replace(':', '').strip() + '_tablecontents.csv', sep=';',
                    quotechar='"')
                # print(listnovelcaps)
                for i in range(int(len(listnovelcaps['nombrecap']) / 200) + 1):
                    if obtenercapitulotable(i + 1) == 'True':
                        time.sleep(3)
                crearepub()
            titulo = ''
            cantidadcaptitulo = 0
            listaCapitulos = []
            autor = ''
            descripcion = ''
            genero = []
            ext = ''
    return False


band = True
while band == True:
    try:
        band = main()
    except Exception as e:
        print('\nhubo un error\n', e.args)
        time.sleep(3)
        band = True
