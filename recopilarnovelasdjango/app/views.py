from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from fpdf import FPDF
from .models import Novela, Capitulo, ContenidoCapitulo
from django.conf import settings
from bson.objectid import ObjectId
import translators as ts
from icrawler.builtin import GoogleImageCrawler
from ebooklib import epub
import uuid
import os
import time
import requests
import logging

# Obtén una referencia al logger
logger = logging.getLogger('app')

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")

    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f"{label}", new_x="LMARGIN",
                  new_y="NEXT", align="L", fill=True)
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


def traducir(texto):
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


def descargar_imagen(imagen_url, nombre_archivo):
    image_path = os.path.join(
        settings.STATICFILES_DIRS[0], 'images', nombre_archivo)
    if not os.path.exists(image_path):
        response = requests.get(imagen_url)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'wb') as f:
                f.write(response.content)
            logger.debug(f"Imagen descargada y guardada en: {image_path}")
        else:
            logger.debug(f"No se pudo descargar la imagen: {imagen_url}")
            return None
    else:
        logger.debug(f"Imagen ya existe en: {image_path}")
    return image_path


def generar_pdf(request, novela_id):
    logger.debug(novela_id)
    novela = Novela.objects.values(
        '_id', 'nombre', 'autor', 'imagen_url', 'sinopsis', 'url').filter(_id=ObjectId(novela_id))
    # logger.debug(novela)
    capitulos = Capitulo.objects.values(
        '_id', 'nombre').filter(novela_id=novela_id)
    # logger.debug(capitulos)
    contenido_capitulos = {str(cont_cap['capitulo_id']): cont_cap['texto'] for cont_cap in ContenidoCapitulo.objects.values(
        'capitulo_id', 'texto').filter(novela_id=novela_id)}
    # logger.debug(contenido_capitulos)

    response = HttpResponse(content_type='application/pdf')
    for x in novela:
        nom = x['nombre']
        response['Content-Disposition'] = f'attachment; filename="{nom}.pdf"'

        pdf = PDF(orientation='P', unit='mm', format='A4')
        pdf.add_font('Poppins-Regular', '', os.path.join(settings.STATIC_ROOT,
                     'fonts', 'Poppins-Regular.ttf'), uni=True)
        pdf.set_font('Poppins-Regular', size=12)
        pdf.set_title(x['nombre'])
        pdf.set_author(x['autor'])
        pdf.set_creator('David Eliceo Vite Vergara')
        pdf.add_page()

        pdf.chapter_title(x['nombre'])
        nombre_imagen = os.path.basename(x['imagen_url'])
        ruta_imagen = descargar_imagen(x['imagen_url'], nombre_imagen)
        logger.debug(ruta_imagen)
        pdf.image(name=ruta_imagen, x=pdf.epw / 3, w=75)
        pdf.write_html(text="<h5>Resumen:</h5>")
        pdf.write_html(text=''.join([f"<p>{traducir(sinop)}</p><br>" for sinop in x['sinopsis'].split('\r\n')]))
        pdf.write(text=f"Url de Novela: {x['url']}")
        for cap in capitulos:
            cap_id = str(cap['_id'])
            logger.debug(f"{cap['nombre']}")
            # logger.debug(contenido_capitulos[cap_id])
            pdf.print_chapter(f"{traducir(cap['nombre'])}", f"{str(contenido_capitulos[cap_id])}")

        filename = ''.join([a.lower() for a in x['nombre'] if a.isalpha() or a == ' '])+'.pdf'
        file_path = f"{os.path.join(settings.STATICFILES_DIRS[0],'pdf', filename)}"
        pdf.output(file_path)
        # pdf.output(name=response)

        # return response
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)


def generar_epub(request, novela_id):
    logger.debug(novela_id)
    novela = Novela.objects.values(
        '_id', 'nombre', 'autor', 'imagen_url', 'sinopsis', 'url').filter(_id=ObjectId(novela_id))
    # logger.debug(novela)
    capitulos = Capitulo.objects.values(
        '_id', 'nombre').filter(novela_id=novela_id)
    # logger.debug(capitulos)
    contenido_capitulos = {str(cont_cap['capitulo_id']): cont_cap['texto'] for cont_cap in ContenidoCapitulo.objects.values(
        'capitulo_id', 'texto').filter(novela_id=novela_id)}
    # logger.debug(contenido_capitulos)

    response = HttpResponse(content_type='application/epub')
    for x in novela:
        nom = x['nombre']
        response['Content-Disposition'] = f'attachment; filename="{nom}.epub"'
        nombre_imagen = os.path.basename(x['imagen_url'])
        ruta_imagen = descargar_imagen(x['imagen_url'], nombre_imagen)
        # print(ruta_imagen)
        
        book = epub.EpubBook()
        # set metadata
        book.set_identifier(str(uuid.uuid4()))
        book.set_cover('cover.jpg', open(ruta_imagen, 'rb').read())
        book.set_title(x['nombre'])
        book.set_language('es')
        book.add_author(x['autor'])
        
        cs = ()
        
        c = epub.EpubHtml(title='Introduction',
                      file_name='intro.xhtml', lang='es')
        nombre = x['nombre']
        url=x['url']
        sinopsis = x['sinopsis'].split('\r\n')
        sinopsis = ''.join([f"<p>{traducir(sinop)}</p><br>" for sinop in sinopsis])
        c.content = f'<h1>{nombre}</h1> <br> <h4>Sinopsis:</h4> <br> {sinopsis} <br> <h4>Url:</h4> <p>{url}</p>'
        # add chapter
        book.add_item(c)
        for idx, cap in enumerate(capitulos):
            cap_id = str(cap['_id'])
            nombre_cap = traducir(cap['nombre'])
            logger.debug(f"{cap['nombre']}")
            cp = str(idx+1).zfill(len(str(len(capitulos))))
            c = epub.EpubHtml(title=nombre_cap, file_name=f"chap_{cp}.xhtml", lang='es')
            c.content = f"<h1>{nombre_cap}</h1><br>{contenido_capitulos[cap_id]}"
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
        
        filename = ''.join([a.lower() for a in x['nombre'] if a.isalpha() or a == ' '])+'.epub'
        file_path = f"{os.path.join(settings.STATICFILES_DIRS[0],'epub', filename)}"
        epub.write_epub(file_path, book, {})
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
