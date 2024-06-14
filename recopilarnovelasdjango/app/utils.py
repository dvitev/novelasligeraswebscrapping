import translators as ts
from icrawler.builtin import GoogleImageCrawler
from ebooklib import epub
import uuid
import os
import time
from fpdf import FPDF



class PDF(FPDF):
    # HTML2FPDF_CLASS = CustomHTML2FPDF
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")

    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        # Printing chapter name:
        self.cell(
            0,
            6,
            f"{label}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
            fill=True,
        )
        # Performing a line break:
        self.ln(4)

    def chapter_body(self, texto):
        self.set_font('Poppins-Regular', size=12)
        # Printing justified text:
        self.write_html(texto)
        # Performing a line break:
        self.ln()

    def add_section(self, title):
        self.start_section(title)

    def print_chapter(self, title, texto):
        self.add_page()
        # self.start_section(title)
        self.chapter_title(title)
        self.chapter_body(texto)


async def btn_guardar_pdf_click(e):
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
    pdf.write(text=f"Url de Novela: txt_name.value")

    for index, chapter in df_contentchapters.iterrows():
        pdf.print_chapter(f"{chapter['nombre']}", f"{chapter['contenido']}")
        print(f"Añadido {chapter['nombre']} al PDF")
    pdf.output(f"{os.path.join(path,'pdf',tituloarchivo)}.pdf")
    print('archivo pdf de ', tituloarchivo, ' creado')


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
    for idx, info in df_infobox.iterrows():
        if 'autor' in str(info['descripcion']).lower():
            book.add_author(f"{info['descripcion'].split(':')[-1].strip()}")

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
