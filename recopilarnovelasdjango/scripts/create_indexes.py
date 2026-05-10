#!/usr/bin/env python
"""
Script to create MongoDB indexes for the recopilarnovelas database.
Run: python scripts/create_indexes.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGODB_HOST = os.environ.get("MONGODB_HOST", "192.168.1.11")
MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "recopilarnovelas")


def create_indexes():
    try:
        client = MongoClient(
            host=MONGODB_HOST,
            port=MONGODB_PORT,
            serverSelectionTimeoutMS=5000
        )
        db = client[MONGODB_DATABASE]
        
        print(f"Connecting to MongoDB at {MONGODB_HOST}:{MONGODB_PORT}")
        print(f"Database: {MONGODB_DATABASE}")
        
        indexes_created = 0
        
        # Novela collection indexes
        print("\n[Novela] Creating indexes...")
        
        # Index: sitio_id - list novels by site
        db.app_novela.create_index("sitio_id", background=True)
        print("  - Created: {sitio_id: 1}")
        indexes_created += 1
        
        # Index: nombre (text search)
        db.app_novela.create_index(
            [("nombre", "text")],
            default_language="spanish",
            background=True
        )
        print("  - Created: {nombre: 'text'}")
        indexes_created += 1
        
        # Index: updated_at for sorting
        db.app_novela.create_index(
            [("updated_at", -1)],
            background=True
        )
        print("  - Created: {updated_at: -1}")
        indexes_created += 1
        
        # Index: sitio_id + genero (compound)
        db.app_novela.create_index(
            [("sitio_id", 1), ("genero", 1)],
            background=True
        )
        print("  - Created: {sitio_id: 1, genero: 1}")
        indexes_created += 1
        
        # Index: nombre with case-insensitive collation
        db.app_novela.create_index(
            [("nombre", 1)],
            collation={"locale": "es", "strength": 2},
            background=True,
            unique=False
        )
        print("  - Created: {nombre: 1} (collation: es)")
        indexes_created += 1
        
        # Capitulo collection indexes
        print("\n[Capitulo] Creating indexes...")
        
        db.app_capitulo.create_index("novela_id", background=True)
        print("  - Created: {novela_id: 1}")
        indexes_created += 1
        
        db.app_capitulo.create_index(
            [("novela_id", 1), ("created_at", -1)],
            background=True
        )
        print("  - Created: {novela_id: 1, created_at: -1}")
        indexes_created += 1
        
        # ContenidoCapitulo collection indexes
        print("\n[ContenidoCapitulo] Creating indexes...")
        
        db.app_contenidocapitulo.create_index("novela_id", background=True)
        print("  - Created: {novela_id: 1}")
        indexes_created += 1
        
        db.app_contenidocapitulo.create_index("capitulo_id", background=True)
        print("  - Created: {capitulo_id: 1}")
        indexes_created += 1
        
        # Sitio collection indexes
        print("\n[Sitio] Creating indexes...")
        
        db.app_sitio.create_index("nombre", background=True)
        print("  - Created: {nombre: 1}")
        indexes_created += 1
        
        print(f"\n✅ Successfully created {indexes_created} indexes!")
        
        # List all indexes
        print("\nCurrent indexes:")
        for coll_name in ["app_novela", "app_capitulo", "app_contenidocapitulo", "app_sitio"]:
            print(f"\n{coll_name}:")
            for idx in db[coll_name].list_indexes():
                print(f"  - {idx['name']}: {idx['key']}")
                
    except ConnectionFailure as e:
        print(f"\n❌ Error connecting to MongoDB: {e}")
        sys.exit(1)
    except OperationFailure as e:
        print(f"\n❌ Error creating indexes: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_indexes()