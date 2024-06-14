from django.shortcuts import render
from django.http import HttpResponse,FileResponse
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
        self.cell(0, 6, f"{label}", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
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
    ruta_archivo = os.path.join(settings.STATICFILES_DIRS[0], 'images')
    if not os.path.exists(os.path.join(ruta_archivo,nombre_archivo.lower())):
        google_crawler = GoogleImageCrawler(storage={'root_dir': ruta_archivo})
        google_crawler.crawl(keyword=nombre_archivo, max_num=1)
        print(imagen_url)
        time.sleep(5)
        dirimgs = os.listdir(ruta_archivo)
        imgenportada = ''.join(
            [x for x in dirimgs if '000001' in x]).split('.')
        # if imgenportada[0] != '':
        try:
            os.rename(os.path.join(ruta_archivo, '.'.join(imgenportada)), os.path.join(ruta_archivo, nombre_archivo.lower()))
        except:
            pass
    
    return os.path.join(ruta_archivo, nombre_archivo.lower())
    

def generar_pdf(request, novela_id):
    print(novela_id)
    novela = Novela.objects.values('_id','nombre','autor', 'imagen_url', 'sinopsis', 'url').filter(_id=ObjectId(novela_id))
    # print(novela)
    capitulos = Capitulo.objects.values('_id','nombre').filter(novela_id=novela_id)
    # print(capitulos)
    contenido_capitulos = {str(cont_cap['capitulo_id']):cont_cap['texto'] for cont_cap in ContenidoCapitulo.objects.values('capitulo_id','texto').filter(novela_id=novela_id)}
    # print(contenido_capitulos)

    response = HttpResponse(content_type='application/pdf')
    for x in novela:
        nom = x['nombre']
        response['Content-Disposition'] = f'attachment; filename="{nom}.pdf"'

        pdf = PDF(orientation='P', unit='mm', format='A4')
        pdf.add_font('Poppins-Regular', '', os.path.join(settings.STATIC_ROOT, 'fonts', 'Poppins-Regular.ttf'), uni=True)
        pdf.set_font('Poppins-Regular', size=12)
        pdf.set_title(x['nombre'])
        pdf.set_author(x['autor'])
        pdf.set_creator('David Eliceo Vite Vergara')
        pdf.add_page()

        pdf.chapter_title(x['nombre'])
        nombre_imagen = os.path.basename(x['imagen_url'])
        ruta_imagen = descargar_imagen(x['imagen_url'], nombre_imagen)
        # print(ruta_imagen)
        pdf.image(name=ruta_imagen, x=pdf.epw / 3, w=75)
        pdf.write_html(text="<h5>Resumen:</h5>")
        pdf.write_html(text=''.join([f"<p>{traducir(sinop)}</p><br>" for sinop in x['sinopsis'].split('\r\n')]))
        pdf.write(text=f"Url de Novela: {x['url']}")
        for cap in capitulos:
            cap_id = str(cap['_id'])
            print(f"{cap['nombre']}")
            # print(contenido_capitulos[cap_id])
            pdf.print_chapter(f"{traducir(cap['nombre'])}", f"{str(contenido_capitulos[cap_id])}")
        
        filename = x['nombre'].lower().replace(' ','-')+'.pdf' 
        file_path = f"{os.path.join(settings.STATICFILES_DIRS[0],'pdf', filename)}"
        pdf.output(file_path)
        # pdf.output(name=response)

        # return response
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)