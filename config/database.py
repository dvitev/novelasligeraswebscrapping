import os
import logging
from pymongo import MongoClient, ASCENDING

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.1.11:27017")
DB_NAME = "recopilarnovelas"


class Database:
    """Singleton de conexión MongoDB con gestión de índices."""

    _instance = None

    def __new__(cls, uri=None, db_name=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, uri=None, db_name=None):
        if self._initialized:
            return
        self._uri = uri or MONGO_URI
        self._db_name = db_name or DB_NAME
        self._client = MongoClient(
            self._uri,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
        )
        self._db = self._client[self._db_name]
        self._initialized = True
        logger.info(f"MongoDB conectado a {self._uri}/{self._db_name}")

    # --- Propiedades para acceder a colecciones ---
    @property
    def sitios(self):
        return self._db["app_sitio"]

    @property
    def novelas(self):
        return self._db["app_novela"]

    @property
    def capitulos(self):
        return self._db["app_capitulo"]

    @property
    def contenido_capitulos(self):
        return self._db["app_contenidocapitulo"]

    def ensure_indexes(self):
        """Crea índices para optimizar consultas frecuentes."""
        try:
            self.novelas.create_index(
                [("sitio_id", ASCENDING)],
                name="idx_novela_sitio",
                background=True,
            )
            self.novelas.create_index(
                [("sitio_id", ASCENDING), ("_id", ASCENDING)],
                name="idx_sitio_id_paginacion",
                background=True,
            )
            self.novelas.create_index(
                [("nombre", "text")],
                name="idx_novela_nombre_text",
                background=True,
            )
            self.capitulos.create_index(
                [("novela_id", ASCENDING)],
                name="idx_capitulo_novela",
                background=True,
            )
            self.capitulos.create_index(
                [("novela_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_capitulo_novela_fecha",
                background=True,
            )
            self.contenido_capitulos.create_index(
                [("novela_id", ASCENDING)],
                name="idx_contenido_novela",
                background=True,
            )
            self.contenido_capitulos.create_index(
                [("capitulo_id", ASCENDING)],
                name="idx_contenido_capitulo",
                background=True,
            )
            logger.info("Índices MongoDB verificados/creados.")
        except Exception as e:
            logger.warning(f"No se pudieron crear índices: {e}")

    def close(self):
        """Cierra la conexión MongoDB limpiamente."""
        if self._client:
            self._client.close()
            logger.info("Conexión MongoDB cerrada.")
            Database._instance = None
            self._initialized = False
