import logging
from datetime import datetime
from bson.objectid import ObjectId

from config.constants import NOVELAS_POR_PAGINA

logger = logging.getLogger(__name__)


class DataRepository:
    """Capa de acceso a datos MongoDB para novelas, capítulos y contenido."""

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Sitios
    # ------------------------------------------------------------------
    def load_home_data(self):
        """Carga todos los sitios registrados."""
        try:
            return list(self.db.sitios.find())
        except Exception as e:
            logger.error(f"Error loading home: {e}")
            return []

    # ------------------------------------------------------------------
    # Novelas (paginado + búsqueda server-side)
    # ------------------------------------------------------------------
    def load_sitio_details_paginado(self, sitio_id, pagina=1, por_pagina=NOVELAS_POR_PAGINA, query=""):
        """
        Carga detalles del sitio y un subconjunto paginado de novelas.
        Si *query* no está vacío aplica filtro $regex sobre 'nombre'.
        Devuelve: (sitio_doc, lista_novelas_pagina, total_novelas)
        """
        try:
            sitio = self.db.sitios.find_one({'_id': ObjectId(sitio_id)})
            if not sitio:
                return None, [], 0

            filtro = {'sitio_id': sitio_id}
            if query:
                filtro['nombre'] = {'$regex': query, '$options': 'i'}

            skip = (pagina - 1) * por_pagina
            total_novelas = self.db.novelas.count_documents(filtro)
            novelas_cursor = (
                self.db.novelas
                .find(filtro)
                .skip(skip)
                .limit(por_pagina)
                .sort('_id', 1)
            )
            return sitio, list(novelas_cursor), total_novelas
        except Exception as e:
            logger.error(f"Error loading sitio details (paginado) for sitio {sitio_id}, page {pagina}: {e}")
            return None, [], 0

    # ------------------------------------------------------------------
    # Novela individual + capítulos
    # ------------------------------------------------------------------
    def load_novela_details(self, novela_id):
        """Retorna (novela_doc, lista_capitulos) ordenados por created_at."""
        try:
            novela = self.db.novelas.find_one({'_id': ObjectId(novela_id)})
            capitulos = list(
                self.db.capitulos.find({'novela_id': novela_id}).sort('created_at', 1)
            )
            return novela, capitulos
        except Exception as e:
            logger.error(f"Error loading novela details: {e}")
            return None, []

    def load_ids_capitulos_novela(self, novela_id):
        """Retorna set de IDs de capítulos de una novela."""
        try:
            return {
                str(cap['_id'])
                for cap in self.db.capitulos.find({'novela_id': novela_id}, {'_id': 1}).sort('created_at', 1)
            }
        except Exception as e:
            logger.error(f"Error loading capitulo novela details: {e}")
            return set()

    def load_ids_urls_capitulos_novela(self, novela_id):
        """Retorna dict {cap_id: url} de capítulos de una novela."""
        try:
            return {
                str(cap['_id']): cap['url']
                for cap in self.db.capitulos.find(
                    {'novela_id': novela_id}, {'_id': 1, 'url': 1}
                ).sort('created_at', 1)
            }
        except Exception as e:
            logger.error(f"Error loading ids urls capitulos details: {e}")
            return {}

    def load_ids_contenido_capitulos_novela(self, novela_id):
        """Retorna set de IDs de capítulos con contenido descargado (O(1) lookup)."""
        try:
            return {
                str(c['capitulo_id'])
                for c in self.db.contenido_capitulos.find(
                    {'novela_id': novela_id}, {'capitulo_id': 1, '_id': 0}
                ).sort('created_at', 1)
            }
        except Exception as e:
            logger.error(f"Error loading ids contenido capitulos novela: {e}")
            return set()

    # ------------------------------------------------------------------
    # Contenido de capítulos
    # ------------------------------------------------------------------
    def enviar_contenido_capitulo(self, novela_id, capitulo_id, texto_capitulo):
        """Inserta contenido de un capítulo en BD y retorna su _id como str."""
        novel_data = {
            'novela_id': novela_id,
            'capitulo_id': capitulo_id,
            'texto': texto_capitulo,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        return str(self.db.contenido_capitulos.insert_one(novel_data).inserted_id)

    def obtener_contenido_capitulos(self, novela_id):
        """Retorna dict {capitulo_id: texto} con todo el contenido de una novela."""
        return {
            str(x['capitulo_id']): x['texto']
            for x in self.db.contenido_capitulos.find(
                {'novela_id': str(novela_id)}
            ).sort('created_at', 1)
        }

    # ------------------------------------------------------------------
    # Búsqueda server-side de capítulos
    # ------------------------------------------------------------------
    def buscar_capitulos(self, novela_id, query):
        """Busca capítulos por nombre con $regex (case-insensitive)."""
        try:
            filtro = {'novela_id': novela_id}
            if query:
                filtro['nombre'] = {'$regex': query, '$options': 'i'}
            return list(
                self.db.capitulos.find(filtro).sort('created_at', 1)
            )
        except Exception as e:
            logger.error(f"Error buscando capítulos: {e}")
            return []

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def get_capitulos_faltantes(todos_ids, ids_con_contenido):
        """Retorna lista de IDs que faltan por descargar (set difference)."""
        return list(set(todos_ids) - set(ids_con_contenido))

    def find_novela_by_id(self, novela_id):
        """Busca una novela por su _id."""
        try:
            return self.db.novelas.find_one({'_id': ObjectId(novela_id)})
        except Exception as e:
            logger.error(f"Error finding novela: {e}")
            return None
