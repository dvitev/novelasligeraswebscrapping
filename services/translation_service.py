import logging
import translators as ts
from google_trans_new import google_translator

from config.constants import CHARACTER_LIMITS

logger = logging.getLogger(__name__)


class TranslationService:
    """Servicio de traducción con fallback multi-proveedor."""

    @staticmethod
    def traducir(texto: str) -> str:
        """Traduce texto usando múltiples servicios de traducción con fallback."""
        servicios = [
            ('google', lambda t: ts.translate_text(t, translator='google', to_language='es')),
            ('google_new', lambda t: google_translator().translate(t, lang_tgt='es')),
            ('bing', lambda t: ts.translate_text(t, translator='bing', to_language='es')),
        ]
        for name, func in servicios:
            try:
                return func(texto)
            except Exception as e:
                logger.warning(f"Fallo en {name}: {e}")
                continue
        return texto

    @staticmethod
    def traducir_texto_largo(texto: str, delimitador: str = '--- párrafo_delimiter ---') -> str:
        """
        Traduce texto largo dividiéndolo si excede el límite de caracteres.
        """
        limit = min(CHARACTER_LIMITS.values(), default=4500)

        if len(texto) <= limit:
            return TranslationService.traducir(texto)

        partes = texto.split(delimitador)
        partes_traducidas = []
        parte_actual = ""

        for parte in partes:
            parte_con_delimitador = (delimitador if parte_actual else "") + parte
            if len(parte_actual + parte_con_delimitador) > limit and parte_actual:
                partes_traducidas.append(TranslationService.traducir(parte_actual))
                parte_actual = parte
            else:
                parte_actual += parte_con_delimitador

        if parte_actual:
            partes_traducidas.append(TranslationService.traducir(parte_actual))

        return "".join(partes_traducidas)
