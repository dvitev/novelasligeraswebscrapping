import os

# IDs de Sitios
FANMTL_SITIO_ID = '67de23f6e131d527f2995103'
TUNOVELA_LIGERA_SITIO_ID = '680ecb15e1ce8081ecb8b4d1'
DEVILNOVELS_SITIO_ID = '699910bb09d676d0eee6c8e3'

# Límites de caracteres para servicios de traducción
CHARACTER_LIMITS = {
    'google': 5000,
    'google_new': 5000,
    'bing': 5000,
}

# Constantes generales
DEFAULT_SLEEP_TIME = 3
PARAGRAPH_DELIMITER = "---PARAGRAPH_DELIMITER---"
TEMP_IMAGE_FILENAME = "imagen_descargada.jpg"
PINGO_FONT_PATH = os.path.join(
    os.getcwd(), 'recopilarnovelasdjango', 'static', 'fonts', 'Poppins-Regular.ttf'
)

# Constantes de Paginación
NOVELAS_POR_PAGINA = 20
CAPITULOS_POR_PAGINA = 50
