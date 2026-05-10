"""
Script de migración para mejorar el diseño de documentos MongoDB.
Mejoras: Embedding, Denormalización, Genero como array
"""
import os
import sys
import re
from bson import ObjectId
from pymongo import MongoClient

MONGODB_HOST = os.environ.get("MONGODB_HOST", "192.168.1.11")
MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "recopilarnovelas")


def get_db():
    client = MongoClient(
        host=MONGODB_HOST,
        port=MONGODB_PORT,
        serverSelectionTimeoutMS=5000
    )
    return client[MONGODB_DATABASE]


def migrate_genero_to_array(db):
    print("Migrando genero de string a array...")
    
    collection = db["app_novela"]
    count = 0
    
    for doc in collection.find({"genero": {"$type": "string"}}):
        genero_str = doc.get("genero", "")
        if genero_str:
            generos = [g.strip() for g in genero_str.split(",") if g.strip()]
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"generos": generos}}
            )
            count += 1
    
    print(f"  -> {count} documentos actualizados")
    return count


def migrate_sitio_with_estructura(db):
    print("Migrando EstructuraSitio como subdocumento...")
    
    estructura_collection = db["app_estructurasitio"]
    sitio_collection = db["app_sitio"]
    count = 0
    
    for estructura in estructura_collection.find():
        sitio_id = estructura.get("sitio_id")
        if sitio_id:
            sitio_collection.update_one(
                {"_id": ObjectId(sitio_id)},
                {"$set": {"estructura": estructura.get("estructura", {})}}
            )
            count += 1
    
    print(f"  -> {count} sitios actualizados con estructura embebida")
    return count


def add_cantidad_capitulos_field(db):
    print("Agregando campo cantidad_capitulos a novelas...")
    
    novela_collection = db["app_novela"]
    capitulo_collection = db["app_capitulo"]
    count = 0
    
    for novela in novela_collection.find():
        novela_id = str(novela["_id"])
        cantidad = capitulo_collection.count_documents({"novela_id": novela_id})
        novela_collection.update_one(
            {"_id": novela["_id"]},
            {"$set": {"cantidad_capitulos": cantidad}}
        )
        count += 1
    
    print(f"  -> {count} novelas actualizadas con cantidad_capitulos")
    return count


def create_indexes(db):
    print("Creando índices compuestos...")
    
    indexes = [
        ("app_novela", [("sitio_id", 1), ("generos", 1)]),
        ("app_novela", [("sitio_id", 1), ("updated_at", -1)]),
        ("app_capitulo", [("novela_id", 1), ("created_at", -1)]),
        ("app_novela", [("nombre", 1)], {"collation": {"locale": "es", "strength": 2}}),
    ]
    
    for idx in indexes:
        collection_name = idx[0]
        keys = idx[1]
        options = idx[2] if len(idx) > 2 else {}
        
        try:
            collection = db[collection_name]
            collection.create_index(keys, **options)
            print(f"  -> Índice creado en {collection_name}: {keys}")
        except Exception as e:
            print(f"  -> Error creando índice en {collection_name}: {e}")
    
    return True


def main():
    print("=" * 60)
    print("MIGRACIÓN DE DISEÑO DE DOCUMENTOS MONGODB")
    print("=" * 60)
    
    try:
        db = get_db()
        print(f"Conectado a MongoDB: {MONGODB_DATABASE}")
        
        print("\n--- Fase 1: Genero como array ---")
        migrate_genero_to_array(db)
        
        print("\n--- Fase 2: EstructuraSitio embedding ---")
        migrate_sitio_with_estructura(db)
        
        print("\n--- Fase 3: Denormalización cantidad_capitulos ---")
        add_cantidad_capitulos_field(db)
        
        print("\n--- Fase 4: Índices compuestos ---")
        create_indexes(db)
        
        print("\n" + "=" * 60)
        print("MIGRACIÓN COMPLETADA")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()