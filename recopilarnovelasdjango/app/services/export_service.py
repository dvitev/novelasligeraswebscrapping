"""
Service for generating PDF and EPUB exports of novels.
"""
import os
import uuid
import io
import logging
import requests
import signal
import translators as ts
from contextlib import contextmanager
from django.conf import settings
from django.http import FileResponse
from bson.objectid import ObjectId
from fpdf import FPDF
from ebooklib import epub
from rest_framework import status
from rest_framework.exceptions import APIException
from ..models import Novela, Capitulo, ContenidoCapitulo

logger = logging.getLogger('app')

TRANSLATION_TIMEOUT = 10


class TranslationTimeout(Exception):
    pass


def timeout_handler(signum, frame):
    raise TranslationTimeout("Translation timed out")


@contextmanager
def translate_with_timeout(seconds=TRANSLATION_TIMEOUT):
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def traducir(texto):
    if not texto:
        return texto
    
    for translator in ['bing', 'google']:
        try:
            with translate_with_timeout(TRANSLATION_TIMEOUT):
                contenido_p = ts.translate_text(
                    texto, 
                    translator=translator, 
                    to_language='es'
                )
                if contenido_p:
                    logger.debug(f"Translated with {translator}")
                    return contenido_p
        except TranslationTimeout:
            logger.warning(f"Translation timed out for {translator}")
        except Exception as e:
            logger.warning(f"Translation failed with {translator}: {e}")
            continue
    logger.warning(f"Returning original text without translation")
    return texto


def descargar_imagen(imagen_url, nombre_archivo):
    if not imagen_url:
        return None
    image_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', nombre_archivo)
    if not os.path.exists(image_path):
        try:
            response = requests.get(imagen_url, timeout=10)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                logger.debug(f"Imagen descargada: {image_path}")
                return image_path
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
    else:
        logger.debug(f"Imagen ya existe: {image_path}")
    return None


def read_image_bytes(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            return f.read()
    return None


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
        self.write_html(texto)
        self.ln()

    def add_section(self, title):
        self.start_section(title)

    def print_chapter(self, title, texto):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(texto)


def generar_pdf(novela_id):
    logger.debug(f"Generando PDF para novela_id: {novela_id}")
    
    novela = Novela.objects.values(
        '_id', 'nombre', 'autor', 'imagen_url', 'sinopsis', 'url'
    ).filter(_id=ObjectId(novela_id))
    
    if not novela:
        raise APIException(
            detail="Novela no encontrada",
            code="not_found"
        )
    
    novela_data = list(novela)[0]
    
    capitulos = list(Capitulo.objects.values('_id', 'nombre').filter(novela_id=novela_id))
    
    contenido_capitulos = {
        str(cont_cap['capitulo_id']): cont_cap['texto']
        for cont_cap in ContenidoCapitulo.objects.values('capitulo_id', 'texto').filter(novela_id=novela_id)
    }
    
    if not contenido_capitulos:
        logger.warning(f"No hay contenido de capítulos para novela {novela_id}")
    
    pdf = PDF(orientation='P', unit='mm', format='A4')
    font_path = os.path.join(settings.STATIC_ROOT, 'fonts', 'Poppins-Regular.ttf')
    if os.path.exists(font_path):
        pdf.add_font('Poppins-Regular', '', font_path, uni=True)
        pdf.set_font('Poppins-Regular', size=12)
    else:
        pdf.set_font('Helvetica', size=12)

    pdf.set_title(novela_data['nombre'])
    pdf.set_author(novela_data['autor'])
    pdf.set_creator('David Eliceo Vite Vergara')
    pdf.add_page()

    pdf.chapter_title(novela_data['nombre'])
    if novela_data.get('imagen_url'):
        nombre_imagen = os.path.basename(novela_data['imagen_url'])
        ruta_imagen = descargar_imagen(novela_data['imagen_url'], nombre_imagen)
        if ruta_imagen:
            try:
                pdf.image(name=ruta_imagen, x=pdf.epw / 3, w=75)
            except Exception as e:
                logger.warning(f"No se pudo agregar imagen: {e}")

    sinopsis = novela_data.get('sinopsis', '')
    if sinopsis:
        sinopsis_html = ''.join([f"<p>{traducir(sinop)}</p><br>" for sinop in sinopsis.split('\r\n') if sinop])
        pdf.write_html(text="<h5>Resumen:</h5>")
        pdf.write_html(text=sinopsis_html)
    
    if novela_data.get('url'):
        pdf.write(text=f"Url de Novela: {novela_data['url']}")

    if capitulos:
        for cap in capitulos:
            cap_id = str(cap['_id'])
            if cap_id in contenido_capitulos:
                titulo = traducir(cap['nombre']) if cap.get('nombre') else f"Capítulo {cap_id}"
                pdf.print_chapter(titulo, str(contenido_capitulos[cap_id]))
    else:
        pdf.write_html(text="<p><em>No hay capítulos disponibles</em></p>")

    pdf_buffer = io.BytesIO()
    try:
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        filename = ''.join([a.lower() for a in novela_data['nombre'] if a.isalpha() or a == ' ']) + '.pdf'
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        raise APIException(detail=f"Error generando PDF: {str(e)}")


def generar_epub(novela_id):
    logger.debug(f"Generando EPUB para novela_id: {novela_id}")
    
    novela = Novela.objects.values(
        '_id', 'nombre', 'autor', 'imagen_url', 'sinopsis', 'url'
    ).filter(_id=ObjectId(novela_id))
    
    if not novela:
        raise APIException(
            detail="Novela no encontrada",
            code="not_found"
        )
    
    novela_data = list(novela)[0]
    
    capitulos = list(Capitulo.objects.values('_id', 'nombre').filter(novela_id=novela_id))
    
    contenido_capitulos = {
        str(cont_cap['capitulo_id']): cont_cap['texto']
        for cont_cap in ContenidoCapitulo.objects.values('capitulo_id', 'texto').filter(novela_id=novela_id)
    }
    
    if not contenido_capitulos:
        logger.warning(f"No hay contenido de capítulos para novela {novela_id}")
    
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    
    if novela_data.get('imagen_url'):
        nombre_imagen = os.path.basename(novela_data['imagen_url'])
        ruta_imagen = descargar_imagen(novela_data['imagen_url'], nombre_imagen)
        image_bytes = read_image_bytes(ruta_imagen)
        if image_bytes:
            try:
                book.set_cover('cover.jpg', image_bytes)
            except Exception as e:
                logger.warning(f"No se pudo agregar cover: {e}")

    book.set_title(novela_data['nombre'])
    book.set_language('es')
    book.add_author(novela_data['autor'])

    sinopsis = novela_data.get('sinopsis', '')
    if sinopsis:
        sinopsis_html = ''.join([f"<p>{traducir(sinop)}</p><br>" for sinop in sinopsis.split('\r\n') if sinop])
    else:
        sinopsis_html = "<p>Sinopsis no disponible</p>"
    
    intro = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='es')
    intro.content = f'<h1>{novela_data["nombre"]}</h1> <br> <h4>Sinopsis:</h4> <br> {sinopsis_html} <br> <h4>Url:</h4> <p>{novela_data.get("url", "No disponible")}</p>'
    book.add_item(intro)

    chapters = []
    if capitulos:
        for idx, cap in enumerate(capitulos):
            cap_id = str(cap['_id'])
            if cap_id not in contenido_capitulos:
                continue
            nombre_cap = traducir(cap['nombre']) if cap.get('nombre') else f"Capítulo {idx + 1}"
            cp = str(idx + 1).zfill(len(str(len(capitulos))))
            c = epub.EpubHtml(title=nombre_cap, file_name=f"chap_{cp}.xhtml", lang='es')
            c.content = f"<h1>{nombre_cap}</h1><br>{contenido_capitulos[cap_id]}"
            book.add_item(c)
            chapters.append(c)
    else:
        empty_chapter = epub.EpubHtml(title='Sin capítulos', file_name='chap_01.xhtml', lang='es')
        empty_chapter.content = "<h1>Sin capítulos disponibles</h1><p>Esta novela no tiene capítulos disponibles aún.</p>"
        book.add_item(empty_chapter)
        chapters.append(empty_chapter)

    book.toc = (
        epub.Link('intro.xhtml', 'Introduction', 'intro'),
        (epub.Section('Introduction', 'intro.xhtml'), tuple(chapters))
    )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.spine = ['nav'] + chapters

    epub_buffer = io.BytesIO()
    try:
        epub.write_epub(epub_buffer, book, {})
        epub_buffer.seek(0)
        
        filename = ''.join([a.lower() for a in novela_data['nombre'] if a.isalpha() or a == ' ']) + '.epub'
        return FileResponse(
            epub_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/epub'
        )
    except Exception as e:
        logger.error(f"Error generando EPUB: {e}")
        raise APIException(detail=f"Error generando EPUB: {str(e)}")