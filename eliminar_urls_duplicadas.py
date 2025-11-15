from pymongo import MongoClient
COLLECTION_NOVELAS = "app_novela"
COLLECTION_CAPITULOS = "app_capitulo"
COLLECTION_CONTENIDO_CAPITULOS = 'app_contenidocapitulo'
# Conexión a MongoDB (sin usuario ni contraseña)
client = MongoClient('mongodb://192.168.1.11:27017/')
db = client['recopilarnovelas']
collection_novelas = db[COLLECTION_NOVELAS]
collection_contenidocapitulo = db[COLLECTION_CONTENIDO_CAPITULOS]
collection = db[COLLECTION_CAPITULOS]
FANMTL_SITIO_ID = '67de23f6e131d527f2995103'
coleccion_novelas = collection_novelas.find({'sitio_id': FANMTL_SITIO_ID}, {'_id': 1, 'nombre': 1}).sort('_id', 1)
for novela in coleccion_novelas:
    print(f"{novela['_id']} - {novela['nombre']}")
    # Filtro para novela_id específico
    filtro = {"novela_id": f"{str(novela['_id'])}"}

    # Pipeline de agregación para encontrar duplicados por 'url'
    pipeline = [
        {"$match": filtro},
        {
            "$group": {
                "_id": "$url",
                "count": {"$sum": 1},
                "docs": {"$push": {"_id": "$_id", "created_at": "$created_at"}}
            }
        },
        {"$match": {"count": {"$gt": 1}}}
    ]

    # Obtener los grupos con duplicados
    duplicados = list(collection.aggregate(pipeline))

    # Recorrer cada grupo de duplicados y eliminar todos excepto uno
    for grupo in duplicados:
        # Ordenar los documentos por '_id' (o por 'created_at' si prefieres mantener el más antiguo)
        docs = sorted(grupo['docs'], key=lambda x: x['_id'])
        # Mantener el primer documento (el de menor '_id')
        ids_a_mantener = [docs[0]['_id']]
        ids_a_eliminar = [doc['_id'] for doc in docs[1:]]

        # Eliminar los documentos duplicados
        if ids_a_eliminar:
            collection.delete_many({"_id": {"$in": ids_a_eliminar}})
            collection_contenidocapitulo.delete_many({"capitulo_id": {"$in": ids_a_eliminar}})
            print(f"Eliminados {len(ids_a_eliminar)} documentos duplicados para la URL: {grupo['_id']}")

print("Proceso de eliminación de duplicados completado.")