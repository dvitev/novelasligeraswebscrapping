import base64
import os
import logging
import threading

import flet as ft
import requests
from datetime import datetime
from tempfile import gettempdir
from urllib.parse import urlparse
from ebooklib import epub
from fpdf import FPDF

from config.constants import PINGO_FONT_PATH, TEMP_IMAGE_FILENAME
from views.theme import AppColors

logger = logging.getLogger(__name__)


# ============================================================
# Clase PDF para generación de documentos
# ============================================================
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
        self.write_html(texto)
        self.ln()

    def add_section(self, title):
        self.start_section(title)

    def print_chapter(self, title, texto):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(texto)


# ============================================================
# Servicio de Exportación (EPUB / PDF)
# ============================================================
class ExportService:
    """Genera archivos EPUB y PDF en hilos separados con progreso visual."""

    def __init__(self, page, repo, translation_svc, filepicker, ui_controls):
        self.page = page
        self.repo = repo
        self.translation = translation_svc
        self.filepicker = filepicker
        self.btn_epub = ui_controls['btn_epub']
        self.btn_pdf = ui_controls['btn_pdf']
        self.btn_procesar = ui_controls['btn_procesar']
        self.progress_ring = ui_controls['progress_ring']
        self.open_banner = ui_controls['open_banner']

        # Estado mutable de instancia (elimina global/nonlocal)
        self.cancelar = False
        self._portada_path = None

    # ------------------------------------------------------------------
    # Métodos privados de UI
    # ------------------------------------------------------------------
    def _preparar_ui(self):
        """Deshabilita botones y muestra progreso."""
        self.cancelar = False
        self.progress_ring.visible = True
        self.btn_epub.disabled = True
        self.btn_pdf.disabled = True
        self.btn_procesar.disabled = True
        self.page.update()

    def _actualizar_progreso(self, idx, total, nombre, formato):
        """Muestra progreso en banner cada 5 capítulos o al final."""
        if idx % 5 == 0 or idx == total:
            emoji = "📖" if formato == 'epub' else "📄"
            icon = ft.Icons.BOOK_OUTLINED if formato == 'epub' else ft.Icons.PICTURE_AS_PDF_OUTLINED
            self.open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(icon, color=AppColors.ACCENT_GREEN, size=40),
                [ft.Text(
                    value=f"{emoji} [{idx}/{total}] {nombre[:40]}...",
                    color=AppColors.TEXT_PRIMARY, size=12,
                )],
            )
            self.page.update()

    def _finalizar_ui(self):
        """Restaura botones y oculta progreso."""
        self.progress_ring.visible = False
        self.btn_epub.disabled = False
        self.btn_pdf.disabled = False
        self.btn_procesar.disabled = False
        self._limpiar_portada()
        self.page.update()

    # ------------------------------------------------------------------
    # Utilidades de archivos
    # ------------------------------------------------------------------
    @staticmethod
    def _sanitizar_nombre(nombre):
        """Elimina caracteres no válidos para nombres de archivo."""
        return "".join(c for c in nombre if c.isalnum() or c in (' ', '_', '-')).rstrip()

    def _descargar_imagen(self, url):
        """Descarga imagen a carpeta temporal."""
        temp_dir = gettempdir()
        parsed_url = urlparse(url)
        nombre_archivo = os.path.basename(parsed_url.path)
        if not nombre_archivo:
            nombre_archivo = TEMP_IMAGE_FILENAME
        ruta_destino = os.path.join(temp_dir, nombre_archivo)
        try:
            respuesta = requests.get(url, stream=True, timeout=30)
            respuesta.raise_for_status()
            with open(ruta_destino, 'wb') as archivo:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    if chunk:
                        archivo.write(chunk)
            logger.info(f"Imagen descargada en: {ruta_destino}")
            return ruta_destino
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red al descargar: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al descargar: {e}")
            return None

    def _descargar_y_preparar_portada(self, url):
        """Descarga imagen y retorna (ruta_temporal, bytes)."""
        portada = self._descargar_imagen(url)
        if not portada or not os.path.exists(portada):
            raise Exception("Error al obtener la portada")
        with open(portada, 'rb') as f:
            portada_bytes = f.read()
        self._portada_path = portada
        return portada, portada_bytes

    def _limpiar_portada(self):
        """Elimina archivo temporal de portada."""
        if self._portada_path and os.path.exists(self._portada_path):
            try:
                os.remove(self._portada_path)
                logger.info("Archivo temporal de portada eliminado.")
            except OSError as oe:
                logger.warning(f"No se pudo eliminar el archivo temporal: {oe}")
            self._portada_path = None

    # ------------------------------------------------------------------
    # EPUB
    # ------------------------------------------------------------------
    def crear_epub(self, novela, capitulos):
        """Lanza generación de EPUB en hilo separado."""
        self._preparar_ui()
        threading.Thread(target=self._epub_worker, args=(novela, capitulos), daemon=True).start()

    def _epub_worker(self, novela, capitulos):
        try:
            contenido = self.repo.obtener_contenido_capitulos(novela['_id'])
            if self.cancelar:
                raise Exception("Exportación cancelada por el usuario")

            _, portada_bytes = self._descargar_y_preparar_portada(novela['imagen_url'])
            base64_cover = base64.b64encode(portada_bytes).decode('utf-8')

            book = epub.EpubBook()
            book.set_identifier(str(novela['_id']))
            book.set_title(novela['nombre'])
            book.set_language('es')
            book.add_author(novela['autor'])
            book.set_cover('cover.jpg', portada_bytes)

            nombre_traducido = self.translation.traducir(novela['nombre']) or novela['nombre']
            sinopsis_traducida = self.translation.traducir(novela['sinopsis']) or novela['sinopsis']

            intro_html = f"""
            <h1>{nombre_traducido}</h1>
            <img src="data:image/jpeg;base64,{base64_cover}"
                style="width: 300px; height: auto; margin: 0 auto; display: block;">
            <h2>Detalles de la Novela</h2>
            <table style="width:100%; border-collapse: collapse;">
            <tr><td style="font-weight:bold;">Novela ID</td><td>{novela.get('_id', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">Nombre</td><td>{nombre_traducido}</td></tr>
            <tr><td style="font-weight:bold; vertical-align:top;">Sinopsis</td><td>{sinopsis_traducida}</td></tr>
            <tr><td style="font-weight:bold;">Autor</td><td>{novela.get('autor', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">Género</td><td>{novela.get('genero', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">Estado</td><td>{novela.get('status', 'N/A')}</td></tr>
            <tr><td style="font-weight:bold;">URL</td><td><a href="{novela.get('url', '#')}">{novela.get('url', 'N/A')}</a></td></tr>
            <tr><td style="font-weight:bold;">Creado</td><td>{novela.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if isinstance(novela.get('created_at'), datetime) else 'N/A'}</td></tr>
            </table>
            """

            intro = epub.EpubHtml(title='Introducción', file_name='intro.xhtml', lang='es')
            intro.content = intro_html
            book.add_item(intro)

            chapters = [intro]
            total = len(capitulos)
            zfill_length = len(str(total))

            for idx, capitulo in enumerate(capitulos, 1):
                if self.cancelar:
                    raise Exception("Exportación cancelada por el usuario")
                nombre_capitulo = capitulo['nombre']
                cap_contenido = contenido.get(str(capitulo['_id']), '')
                chapter = epub.EpubHtml(
                    title=nombre_capitulo,
                    file_name=f'cap_{idx:0{zfill_length}}.xhtml',
                    lang='es',
                )
                chapter.content = f"<h1>{nombre_capitulo}</h1>{cap_contenido}"
                book.add_item(chapter)
                chapters.append(chapter)
                self._actualizar_progreso(idx, total, nombre_capitulo, 'epub')

            notas = epub.EpubHtml(title='Notas', file_name='notas.xhtml', lang='es')
            notas.content = "<h1>Notas</h1><p>Generado con Novelas Manager</p>"
            book.add_item(notas)

            book.toc = (
                epub.Link('intro.xhtml', 'Introducción', 'intro'),
                (epub.Section('Capítulos'), chapters[1:]),
                (epub.Section('Apéndices'), [notas]),
            )
            book.spine = chapters + [notas]
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            css = epub.EpubItem(
                uid="style_css", file_name="style/style.css",
                content="body{font-family:serif;}h1{font-size:1.8em;}table{border:1px solid #ccc;margin:1em 0;}td{border:1px solid #ccc;padding:5px;}",
            )
            book.add_item(css)

            nombre_archivo = self._sanitizar_nombre(novela['nombre']) + '.epub'

            def save_file_result(e: ft.FilePickerResultEvent):
                try:
                    if e.path is None:
                        self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=AppColors.WARNING, size=40),
                                         [ft.Text(value="⚠️ Operación cancelada", color=AppColors.TEXT_PRIMARY, size=14)])
                        return
                    epub.write_epub(e.path, book, {})
                    logger.info(f"EPUB guardado en: {e.path}")
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
                                     [ft.Text(value="✅ EPUB guardado exitosamente", color=AppColors.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_500)])
                except PermissionError:
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.LOCK_ROUNDED, color=AppColors.ERROR, size=40),
                                     [ft.Text(value="🔒 Error: Permisos denegados", color=AppColors.TEXT_PRIMARY, size=14)])
                except Exception as ex:
                    logger.error(f"Error al guardar EPUB: {ex}")
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                     [ft.Text(value=f"❌ Error: {str(ex)[:50]}", color=AppColors.TEXT_PRIMARY, size=14)])
                finally:
                    self._limpiar_portada()
                    self.page.update()

            self.filepicker.on_result = save_file_result
            self.filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["epub"])

        except Exception as e:
            logger.error(f"Error en crear_epub: {e}")
            self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                             [ft.Text(value=f"❌ Error: {str(e)[:60]}", color=AppColors.TEXT_PRIMARY, size=14)])
            self._limpiar_portada()
        finally:
            self._finalizar_ui()

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def crear_pdf(self, novela, capitulos):
        """Lanza generación de PDF en hilo separado."""
        self._preparar_ui()
        threading.Thread(target=self._pdf_worker, args=(novela, capitulos), daemon=True).start()

    def _pdf_worker(self, novela, capitulos):
        try:
            contenido = self.repo.obtener_contenido_capitulos(novela['_id'])
            if self.cancelar:
                raise Exception("Exportación cancelada por el usuario")

            portada, _ = self._descargar_y_preparar_portada(novela['imagen_url'])

            nombre_traducido = self.translation.traducir(novela['nombre']) or novela['nombre']
            sinopsis_traducida = self.translation.traducir(novela['sinopsis']) or novela['sinopsis']

            pdf = PDF(orientation='P', unit='mm', format='A4')
            pdf.add_font('Poppins-Regular', '', PINGO_FONT_PATH, uni=True)
            pdf.set_font('Poppins-Regular', size=12)
            pdf.set_title(nombre_traducido)
            pdf.set_author(novela['autor'])
            pdf.set_creator('Novelas Manager - David Eliceo Vite Vergara')
            pdf.alias_nb_pages()

            pdf.add_page()
            pdf.chapter_title(nombre_traducido)
            pdf.image(name=portada, x=pdf.epw / 3, w=75)
            pdf.write_html(text="<h5>Resumen:</h5>")
            pdf.write_html(text=f"<p>{sinopsis_traducida}</p>")
            pdf.write(text=f"Url de Novela: {novela['url']}")

            total = len(capitulos)
            for idx, capitulo in enumerate(capitulos, 1):
                if self.cancelar:
                    raise Exception("Exportación cancelada por el usuario")
                capitulo_id = str(capitulo['_id'])
                nombre_capitulo = capitulo['nombre']
                cap_contenido = contenido.get(capitulo_id, '')
                pdf.print_chapter(f"{nombre_capitulo}", f"{cap_contenido}")
                self._actualizar_progreso(idx, total, nombre_capitulo, 'pdf')

            nombre_archivo = self._sanitizar_nombre(novela['nombre']) + '.pdf'

            def save_file_result(e: ft.FilePickerResultEvent):
                try:
                    if e.path is None:
                        self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=AppColors.WARNING, size=40),
                                         [ft.Text(value="⚠️ Operación cancelada", color=AppColors.TEXT_PRIMARY, size=14)])
                        return
                    with open(e.path, 'wb') as filepdf:
                        pdf.output(filepdf)
                    logger.info(f"PDF guardado en: {e.path}")
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
                                     [ft.Text(value="✅ PDF guardado exitosamente", color=AppColors.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_500)])
                except PermissionError:
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.LOCK_ROUNDED, color=AppColors.ERROR, size=40),
                                     [ft.Text(value="🔒 Error: Permisos denegados", color=AppColors.TEXT_PRIMARY, size=14)])
                except Exception as ex:
                    logger.error(f"Error al guardar PDF: {ex}")
                    self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                     [ft.Text(value=f"❌ Error: {str(ex)[:50]}", color=AppColors.TEXT_PRIMARY, size=14)])
                finally:
                    self._limpiar_portada()
                    self.page.update()

            self.filepicker.on_result = save_file_result
            self.filepicker.save_file(file_name=nombre_archivo, allowed_extensions=["pdf"])

        except Exception as e:
            logger.error(f"Error en crear_pdf: {e}")
            self.open_banner(AppColors.BG_ELEVATED, ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                             [ft.Text(value=f"❌ Error: {str(e)[:60]}", color=AppColors.TEXT_PRIMARY, size=14)])
            self._limpiar_portada()
        finally:
            self._finalizar_ui()
