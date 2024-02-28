import asyncio
import os
from pdb import run
import time
import datetime
import pandas as pd
import translators as ts
from icrawler.builtin import GoogleImageCrawler
from ebooklib import epub
import uuid
import sys
import re
from fpdf import FPDF, HTML2FPDF, TitleStyle
from tools.funciones import *
import chardet

try:
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
except Exception as e:
    pass


async def btn_guardar_pdf_click():
    global df_contentchapters
    global df_infobox
    global resumen
    global tituloarchivo
    global titulo_datos
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
    # pdf.set_text_shaping(True)
    # pdf.add_font(fname='ttf/DejaVuSansCondensed.ttf')
    # pdf.set_font('DejaVuSansCondensed', size=12)
    pdf.add_font(fname='ttf/Poppins-Regular.ttf')
    pdf.set_font('Poppins-Regular', size=12)

    pdf.set_title(f"{titulo_datos}")
    for idx, info in df_infobox.iterrows():
        if 'autor' in str(info['descripcion']).lower():
            pdf.set_author(f"{info['descripcion'].split(':')[-1].strip()}")
    pdf.set_creator('David Eliceo Vite Vergara')
    pdf.add_page()
    pdf.chapter_title(f"{titulo_datos}")
    pdf.image(name=os.path.join(path, 'images',
                                imgenportada), x=pdf.epw/3, w=75)
    for idx, info in df_infobox.iterrows():
        pdf.write_html(text=f"<p>{info['descripcion']}</p>")
    pdf.write_html(text="<h5>Resumen:</h5>")
    pdf.write_html(text=''.join(
        [f"<p>{x}.</p>" for x in resumen.split('.')]))

    for index, chapter in df_contentchapters.iterrows():
        pdf.print_chapter(f"{chapter['nombre']}",
                          f"{chapter['contenido']}")
        print(f"Añadido {chapter['nombre']} al PDF")

    pdf.output(f"{os.path.join(path,'pdf',tituloarchivo)}.pdf")
    print('archivo pdf de ', tituloarchivo, ' creado')


async def btn_guardar_epub_click():
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
    for idx, info in df_infobox.iterrows():
        if 'autor' in str(info['descripcion']).lower():
            book.add_author(
                f"{info['descripcion'].split(':')[-1].strip()}")

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
                texto, translator='bing', to_language='es')
            break
        except Exception as e:
            print(e)
            try:
                contenido_p = ts.translate_text(
                    texto, translator='google', to_language='es')
                break
            except Exception as e:
                print(e)
                pass
            pass
    return contenido_p


async def detect_encoding(text):
    detected = chardet.detect(text)
    encoding = detected['encoding']
    print(f"detected as {encoding}.")
    return encoding


async def read_file(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        print(e)


async def main():
    txt_ko = os.listdir(os.path.join(os.getcwd(), 'txt'))
    txt_ko_no_es = [x for x in txt_ko if '_es' not in x]
    # txt_ko_es = [x for x in txt_ko if '_es' in x]

    for txt_k in txt_ko_no_es:
        txt_ko_es = [x for x in txt_ko if '_es' in x]
        if f"{txt_k[0:-4]}_es.txt" not in txt_ko_es:
            try:
                path = os.path.join(os.getcwd(), 'txt', txt_k)
                print(path)
                text = await read_file(path)
                print(text[0:100])
                encod = await detect_encoding(text[0:100000])
                print(encod)
                content_text = text.decode(encod, errors='ignore')
                print(content_text[0:100])
                text_arr = content_text.split('\n')
                content_text_es = []
                for txt_ar in text_arr:
                    if txt_ar.strip().rstrip() != '':
                        texto_es = await traducir(txt_ar)
                        if f"{txt_k[0:-4]}_es.txt" not in txt_ko_es:
                            with open(file=os.path.join(os.getcwd(), 'txt', f"{txt_k[0:-4]}_es.txt"), mode="w", encoding='utf-8') as f:
                                f.write(f"{texto_es}\n")
                            txt_ko_es = [x for x in os.listdir(os.path.join(os.getcwd(), 'txt')) if '_es' in x]
                        else:
                            with open(file=os.path.join(os.getcwd(), 'txt', f"{txt_k[0:-4]}_es.txt"), mode="a", encoding='utf-8') as f:
                                f.write(f"{texto_es}\n")
                        print(texto_es)

            except Exception as e:
                print(f"Error: {e}")

            # rows_listchapters = []
            # chaptercontent_list = []


if __name__ == '__main__':
    asyncio.run(main())
