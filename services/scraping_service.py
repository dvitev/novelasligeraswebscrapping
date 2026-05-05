import os
import time
import logging
import threading

import flet as ft
import requests
from bson.objectid import ObjectId
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from config.constants import (
    FANMTL_SITIO_ID,
    TUNOVELA_LIGERA_SITIO_ID,
    DEVILNOVELS_SITIO_ID,
    DEFAULT_SLEEP_TIME,
    PARAGRAPH_DELIMITER,
)
from views.theme import AppColors

logger = logging.getLogger(__name__)


class ScrapingService:
    """Obtiene capítulos faltantes en un hilo separado (no bloquea la UI)."""

    def __init__(self, page, repo, translation_svc, ui_controls):
        self.page = page
        self.repo = repo
        self.translation = translation_svc
        self.open_banner = ui_controls['open_banner']
        self.progress_ring = ui_controls['progress_ring']
        self.btn_epub = ui_controls['btn_epub']
        self.btn_pdf = ui_controls['btn_pdf']
        self.btn_procesar = ui_controls['btn_procesar']
        self.txt_number = ui_controls['txt_number']

        # Estado mutable de instancia
        self.cancelar = False
        self._on_chapter_done = None  # callback(cap_id) para actualizar UI

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def obtener_capitulos(self, cap_faltantes, novela_id, on_chapter_done=None):
        """Lanza scraping en hilo separado. FIX: ya no bloquea la UI."""
        self.cancelar = False
        self._on_chapter_done = on_chapter_done
        self.progress_ring.visible = True
        self.btn_procesar.disabled = True
        self.btn_epub.disabled = True
        self.btn_pdf.disabled = True
        self.page.update()
        threading.Thread(
            target=self._scraping_worker,
            args=(cap_faltantes, novela_id),
            daemon=True,
        ).start()

    def cancelar_scraping(self):
        self.cancelar = True

    # ------------------------------------------------------------------
    # Worker (hilo secundario)
    # ------------------------------------------------------------------
    def _scraping_worker(self, cap_faltantes, novela_id):
        urls_capitulos = self.repo.load_ids_urls_capitulos_novela(novela_id)
        driver = self._instanciar_driver()
        contador = 0
        try:
            for cap_id, url in urls_capitulos.items():
                if self.cancelar:
                    logger.info("Scraping cancelado por el usuario.")
                    break
                if str(cap_id) not in cap_faltantes:
                    continue

                max_intentos = 3
                intento = 0
                while intento < max_intentos:
                    if self.cancelar:
                        break
                    try:
                        driver.get(url)
                        self._manejar_driver(driver, novela_id, str(cap_id))

                        contador += 1
                        self.txt_number.value = str(contador)

                        if self._on_chapter_done:
                            self._on_chapter_done(str(cap_id))
                        self.page.update()
                        break  # éxito → siguiente capítulo
                    except requests.exceptions.RequestException as re:
                        intento += 1
                        logger.warning(f"Intento {intento} fallido para capítulo {cap_id} (red): {re}")
                        if intento == max_intentos:
                            logger.error(f"Error persistente de red: capítulo {cap_id}")
                            self.open_banner(
                                AppColors.BG_ELEVATED,
                                ft.Icon(ft.Icons.WIFI_OFF_ROUNDED, color=AppColors.ERROR, size=40),
                                [ft.Text(value=f"📡 Error de red en capítulo {cap_id}", color=AppColors.TEXT_PRIMARY, size=14)],
                            )
                        time.sleep(2)
                    except Exception as error:
                        intento += 1
                        logger.error(f"Intento {intento} fallido para capítulo {cap_id}: {error}")
                        if intento == max_intentos:
                            self.open_banner(
                                AppColors.BG_ELEVATED,
                                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                                [ft.Text(value=f"❌ Error al obtener capítulo {cap_id}", color=AppColors.TEXT_PRIMARY, size=14)],
                            )
                        time.sleep(2)
        finally:
            driver.quit()
            logger.info("WebDriver cerrado.")
            self.progress_ring.visible = False
            self.btn_procesar.disabled = True
            self.btn_epub.disabled = False
            self.btn_pdf.disabled = False
            self.page.update()

    # ------------------------------------------------------------------
    # Manejo de contenido por sitio
    # ------------------------------------------------------------------
    def _manejar_driver(self, driver, novela_id, capitulo_id):
        novela_doc = self.repo.find_novela_by_id(novela_id)
        if not novela_doc:
            logger.error("Novela no encontrada.")
            self.open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                [ft.Text(value="❌ Novela no encontrada", color=AppColors.TEXT_PRIMARY, size=14)],
            )
            return

        sitio_id = novela_doc.get('sitio_id')
        time.sleep(DEFAULT_SLEEP_TIME)
        soup = bs(driver.page_source, 'html.parser')

        if sitio_id == FANMTL_SITIO_ID:
            self._extraer_y_guardar_contenido(
                soup, 'chapter-content', novela_id, capitulo_id,
                traducir_flag=True, delimitador=PARAGRAPH_DELIMITER,
            )
        elif sitio_id == TUNOVELA_LIGERA_SITIO_ID:
            self._extraer_y_guardar_contenido(
                soup, 'entry-content_wrap', novela_id, capitulo_id,
                traducir_flag=False, delimitador=PARAGRAPH_DELIMITER,
            )
        elif sitio_id == DEVILNOVELS_SITIO_ID:
            self._extraer_y_guardar_contenido(
                soup, 'dv-post-article', novela_id, capitulo_id,
                traducir_flag=False, delimitador=PARAGRAPH_DELIMITER,
            )
        else:
            logger.warning("Sitio no soportado para scraping.")
            self.open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=AppColors.WARNING, size=40),
                [ft.Text(value="⚠️ Sitio no soportado", color=AppColors.TEXT_PRIMARY, size=14)],
            )

    def _extraer_y_guardar_contenido(self, soup, selector_css, novela_id, capitulo_id,
                                      traducir_flag=False, delimitador=PARAGRAPH_DELIMITER):
        div_contenido = soup.find('div', class_=selector_css)
        if not div_contenido:
            logger.error(f"No se encontró contenido con selector {selector_css}.")
            self.open_banner(
                AppColors.BG_ELEVATED,
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=AppColors.ERROR, size=40),
                [ft.Text(value=f"❌ Sin contenido: {selector_css}", color=AppColors.TEXT_PRIMARY, size=14)],
            )
            return None

        p_tags = div_contenido.find_all('p')
        p_tags_con_texto = [p for p in p_tags if p.getText().strip()]

        if p_tags_con_texto:
            textos_originales = [p.getText().strip() for p in p_tags_con_texto]
        else:
            html_str = str(div_contenido)
            br_separated = html_str.split('<br/>')
            textos_originales = [
                bs(part, 'html.parser').get_text().strip()
                for part in br_separated
                if bs(part, 'html.parser').get_text().strip()
            ]

        if textos_originales:
            if traducir_flag:
                texto_a_traducir = delimitador.join(textos_originales)
                texto_traducido = self.translation.traducir_texto_largo(texto_a_traducir, delimitador)
                texto_capitulo = f"<p>{texto_traducido.replace(delimitador, '</p><p>')}</p>"
            else:
                texto_capitulo = ''.join(f"<p>{t}</p>" for t in textos_originales)
        else:
            texto_capitulo = "<p>(Sin contenido)</p>"

        _id = self.repo.enviar_contenido_capitulo(novela_id, capitulo_id, texto_capitulo)
        logger.info(f"Contenido creado id:{_id} para capítulo:{capitulo_id}")
        self.open_banner(
            AppColors.BG_ELEVATED,
            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=AppColors.ACCENT_GREEN, size=40),
            [ft.Text(value=f"✅ Contenido creado id:{_id}", color=AppColors.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_500)],
        )
        return _id

    # ------------------------------------------------------------------
    # WebDriver
    # ------------------------------------------------------------------
    @staticmethod
    def _instanciar_driver():
        options = webdriver.FirefoxOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        )
        return webdriver.Firefox(
            options=options,
            service=Service(executable_path=f"{os.getcwd()}/geckodriver/geckodriver.exe"),
        )
