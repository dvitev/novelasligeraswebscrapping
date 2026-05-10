import logging
from django.shortcuts import render
from .services.export_service import generar_pdf as _generar_pdf, generar_epub as _generar_epub

logger = logging.getLogger('app')


def generar_pdf(request, novela_id):
    return _generar_pdf(novela_id)


def generar_epub(request, novela_id):
    return _generar_epub(novela_id)
