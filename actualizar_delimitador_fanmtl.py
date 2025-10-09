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

def actualizar_delimitador_fanmtl():
    """
    Busca documentos en 'app_contenidocapitulo' asociados a novelas de 'FANMTL_SITIO_ID'
    y reemplaza la frase específica en el campo 'texto'.
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
    # que contengan el delimitador incorrecto
    filtro_busqueda = {
        'novela_id': {'$in': ids_novelas},
        'texto': {'$regex': '--- párrafo_delimiter ---', '$options': 'i'} # 'i' para case-insensitive
    }

    logger.info("Buscando documentos de contenido de capítulo con el delimitador incorrecto...")
    cursor = collection_contenido_capitulos.find(filtro_busqueda)

    documentos_a_actualizar = []
    for doc in cursor:
        documentos_a_actualizar.append(doc)
    logger.info(f"Se encontraron {len(documentos_a_actualizar)} documentos para actualizar.")

    # 3. Actualizar cada documento
    if documentos_a_actualizar:
        for doc in documentos_a_actualizar:
            texto_original = doc['texto']
            # Reemplazar la cadena específica
            texto_corregido = texto_original.replace('--- párrafo_delimiter ---', '</p><p>')

            # Preparar el filtro y la actualización para upsert
            filtro_update = {'_id': doc['_id']}
            actualizacion = {
                '$set': {
                    'texto': texto_corregido,
                    'updated_at': doc.get('updated_at') # Mantener la fecha original o actualizar si es necesario
                }
            }
            # Opcional: Si deseas actualizar `updated_at` a la hora actual, descomenta la línea siguiente
            # actualizacion['$set']['updated_at'] = datetime.now()

            # Ejecutar la actualización
            try:
                result = collection_contenido_capitulos.update_one(filtro_update, actualizacion)
                if result.modified_count > 0:
                    logger.info(f"Documento {doc['_id']} actualizado correctamente.")
                else:
                    logger.warning(f"Documento {doc['_id']} encontrado pero no modificado (¿filtro erróneo o ya estaba corregido?).")
            except Exception as e:
                logger.error(f"Error actualizando documento {doc['_id']}: {e}")

        logger.info("Proceso de actualización de delimitadores completado.")
    else:
        logger.info("No se encontraron documentos que requieran corrección.")


if __name__ == "__main__":
    actualizar_delimitador_fanmtl()
    client.close()
    logger.info("Conexión a MongoDB cerrada.")