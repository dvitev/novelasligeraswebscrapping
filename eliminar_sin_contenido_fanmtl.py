import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.1.11:27017")
DB_NAME = "recopilarnovelas"
COLLECTION_SITIOS = "app_sitio"
COLLECTION_NOVELAS = "app_novela"
COLLECTION_CAPITULOS = "app_capitulo"
COLLECTION_CONTENIDO_CAPITULOS = 'app_contenidocapitulo'

# IDs de Sitios
FANMTL_SITIO_ID = '67de23f6e131d527f2995103'
TUNOVELA_LIGERA_SITIO_ID = '680ecb15e1ce8081ecb8b4d1'

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection_sitios = db[COLLECTION_SITIOS]
collection_novelas = db[COLLECTION_NOVELAS]
collection_capitulos = db[COLLECTION_CAPITULOS]
collection_contenido_capitulos = db[COLLECTION_CONTENIDO_CAPITULOS]

def eliminar_contenido_sin_contenido():
    """
    Busca documentos en 'app_contenidocapitulo' asociados a novelas de 'FANMTL_SITIO_ID'
    que contengan la frase '<p>(Sin contenido)</p>' y los elimina.
    """
    # 1. Obtener todos los IDs de novelas asociadas a FANMTL_SITIO_ID
    logger.info(f"Buscando novelas para sitio_id: {FANMTL_SITIO_ID}")
    novelas_fanmtl = collection_novelas.find(
        {'sitio_id': FANMTL_SITIO_ID},
        {'_id': 1} # Solo proyectar el ID
    )
    ids_novelas = [str(doc['_id']) for doc in novelas_fanmtl]

    if not ids_novelas:
        logger.info(f"No se encontraron novelas para sitio_id: {FANMTL_SITIO_ID}")
        return

    logger.info(f"Se encontraron {len(ids_novelas)} novelas asociadas.")

    # 2. Buscar documentos de contenido de capítulo para esas novelas
    # que contengan la frase específica
    filtro_busqueda = {
        'novela_id': {'$in': ids_novelas},
        'texto': {'$regex': r'<p>\s*\(Sin contenido\)\s*</p>', '$options': 'i'}  # 'i' para case-insensitive
    }

    logger.info("Buscando documentos de contenido de capítulo con la frase '<p>(Sin contenido)</p>'...")
    cursor = collection_contenido_capitulos.find(filtro_busqueda, {'_id': 1})

    documentos_a_eliminar = []
    for doc in cursor:
        documentos_a_eliminar.append(doc['_id'])
    
    logger.info(f"Se encontraron {len(documentos_a_eliminar)} documentos para eliminar.")

    # 3. Eliminar cada documento
    if documentos_a_eliminar:
        logger.info("Iniciando proceso de eliminación...")
        for doc_id in documentos_a_eliminar:
            # Preparar el filtro para eliminación
            filtro_eliminacion = {'_id': doc_id}

            # Ejecutar la eliminación
            try:
                result = collection_contenido_capitulos.delete_one(filtro_eliminacion)
                if result.deleted_count > 0:
                    logger.info(f"Documento {doc_id} eliminado correctamente.")
                else:
                    logger.warning(f"No se encontró el documento {doc_id} para eliminar (¿ya fue eliminado?).")
            except Exception as e:
                logger.error(f"Error eliminando documento {doc_id}: {e}")

        logger.info("Proceso de eliminación completado.")
    else:
        logger.info("No se encontraron documentos que contengan la frase '<p>(Sin contenido)</p>'.")


if __name__ == "__main__":
    eliminar_contenido_sin_contenido()
    client.close()
    logger.info("Conexión a MongoDB cerrada.")