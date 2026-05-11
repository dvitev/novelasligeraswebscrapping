#!/usr/bin/env python3
"""
MongoDB Migration Script: Djongo → PyMongo
Handles: Export, Verify, Import, Rollback
"""
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import date, datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

MONGODB_HOST = os.environ.get("MONGODB_HOST", "192.168.1.11")
MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "recopilarnovelas")
BACKUP_DIR = "./mongodb_backups"


class MongoMigrator:
    def __init__(self, db):
        self.db = db
        self.backup_timestamp = datetime.now().strftime("%Y%m%d")
        self.backup_path = os.path.join(BACKUP_DIR, f"backup_{self.backup_timestamp}")
        
    def export_collections(self):
        """Phase 1: Export all collections to JSON using streaming"""
        print("=" * 60)
        print("FASE 1: EXPORTANDO COLECCIONES")
        print("=" * 60)
        
        os.makedirs(self.backup_path, exist_ok=True)
        
        collections = ["app_sitio", "app_novela", "app_capitulo", 
                      "app_contenidocapitulo", "app_estructurasitio"]
        
        exported = {}
        batch_size = 1000
        
        for coll_name in collections:
            print(f"  Exportando {coll_name}...")
            collection = self.db[coll_name]
            count = collection.count_documents({})
            
            file_path = os.path.join(self.backup_path, f"{coll_name}.json")
            exported_count = 0
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("[\n")
                
                cursor = collection.find().batch_size(batch_size)
                first = True
                
                for doc in cursor:
                    if "_id" in doc and isinstance(doc["_id"], ObjectId):
                        doc["_id"] = str(doc["_id"])
                    
                    if not first:
                        f.write(",\n")
                    first = False
                    
                    json.dump(doc, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
                    exported_count += 1
                    
                    if exported_count % 5000 == 0:
                        print(f"    -> {exported_count}/{count} documentos...")
                
                f.write("\n]")
            
            exported[coll_name] = exported_count
            print(f"    -> {exported_count} documentos exportados")
        
        # Save metadata
        metadata = {
            "timestamp": self.backup_timestamp,
            "collections": exported,
            "database": MONGODB_DATABASE
        }
        with open(os.path.join(self.backup_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Backup completo guardado en: {self.backup_path}")
        return exported
    
    def verify_data(self):
        """Phase 2: Verify data integrity with streaming"""
        print("\n" + "=" * 60)
        print("FASE 2: VERIFICANDO INTEGRIDAD")
        print("=" * 60)
        
        issues = []
        
        # Check required collections exist
        required = ["app_sitio", "app_novela", "app_capitulo"]
        for coll_name in required:
            count = self.db[coll_name].count_documents({})
            if count == 0:
                issues.append(f"Colección {coll_name} vacía")
        
        # Check referential integrity: capitulos -> novelas (streaming)
        print("  Verificando integridad referencial...")
        novela_ids = set(self.db.app_novela.distinct("_id"))
        orphan_count = 0
        batch_size = 5000
        
        cursor = self.db.app_capitulo.find(
            {"novela_id": {"$nin": list(novela_ids)}},
            {"_id": 1}
        ).batch_size(batch_size)
        
        for _ in cursor:
            orphan_count += 1
        
        if orphan_count > 0:
            issues.append(f"{orphan_count} capítulos huérfanos encontrados")
        
        # Check referential integrity: contenidos -> capitulos (streaming)
        capitulo_ids = set()
        cursor = self.db.app_capitulo.find({}, {"_id": 1}).batch_size(batch_size)
        for doc in cursor:
            capitulo_ids.add(doc["_id"])
        
        orphan_cont_count = 0
        
        cursor = self.db.app_contenidocapitulo.find(
            {"capitulo_id": {"$nin": list(capitulo_ids)}},
            {"_id": 1}
        ).batch_size(batch_size)
        
        for _ in cursor:
            orphan_cont_count += 1
        
        if orphan_cont_count > 0:
            issues.append(f"{orphan_cont_count} contenidos huérfanos encontrados")
        
        # Verify ObjectId formats
        print("  Verificando formatos de ObjectId...")
        invalid_sitios = self.db.app_sitio.count_documents({
            "_id": {"$not": {"$type": "objectId"}}
        })
        if invalid_sitios > 0:
            issues.append(f"{invalid_sitios} sitio(s) con _id inválido")
        
        if issues:
            print("\n⚠️ PROBLEMAS ENCONTRADOS:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("  ✓ Todos los verificaciones pasaron")
            return True
    
    def import_with_indexes(self):
        """Phase 3: Manage indexes - verify, fix if wrong, create if missing"""
        print("\n" + "=" * 60)
        print("FASE 3: GESTIONANDO INDICES")
        print("=" * 60)
        
        # Definición completa de índices esperados por colección
        expected_indexes = {
            "app_novela": [
                ([("sitio_id", 1)], "idx_novela_sitio"),
                ([("nombre", "text")], "idx_novela_nombre_text"),
                ([("genero", 1)], "idx_novela_genero"),
                ([("sitio_id", 1), ("genero", 1)], "idx_novela_sitio_genero"),
                ([("sitio_id", 1), ("updated_at", -1)], "idx_novela_sitio_updated"),
                ([("nombre", 1)], "idx_novela_nombre_es", {"collation": {"locale": "es", "strength": 2}}),
            ],
            "app_capitulo": [
                ([("novela_id", 1)], "idx_capitulo_novela"),
                ([("novela_id", 1), ("created_at", 1)], "idx_capitulo_novela_fecha"),
            ],
            "app_contenidocapitulo": [
                ([("novela_id", 1)], "idx_contenido_novela"),
                ([("capitulo_id", 1)], "idx_contenido_capitulo"),
            ],
            "app_sitio": [],
            "app_estructurasitio": [],
        }
        
        created = 0
        fixed = 0
        skipped = 0
        errors = 0
        
        for coll_name, indexes in expected_indexes.items():
            if not indexes:
                print(f"\n  Coleccion {coll_name}: sin indices requeridos")
                continue
                
            print(f"\n  Procesando coleccion: {coll_name}")
            print(f"  Indices esperados: {len(indexes)}")
            
            coll = self.db[coll_name]
            existing_indexes = coll.index_information()
            print(f"  Indices existentes: {len(existing_indexes)}")
            
            # Build a map of existing indexes by key pattern
            existing_by_keys = {}
            for idx_name, idx_info in existing_indexes.items():
                if 'key' in idx_info:
                    key_pattern = [(k, v) for k, v in idx_info['key']]
                    existing_by_keys[tuple(key_pattern)] = idx_name
            
            for idx_spec in indexes:
                keys = idx_spec[0]
                name = idx_spec[1]
                options = idx_spec[2] if len(idx_spec) > 2 else {}
                key_tuple = tuple(keys)
                
                try:
                    # Check 1: Index with correct name exists
                    if name in existing_indexes:
                        idx_info = existing_indexes[name]
                        existing_keys = [(k, v) for k, v in idx_info.get('key', [])]
                        
                        if existing_keys == keys:
                            print(f"    [OK] {name}: correcto")
                            skipped += 1
                            continue
                        else:
                            # Name exists but keys are different - DROP and RECREATE
                            print(f"    [FIX] {name}: campos incorrectos {existing_keys} -> {keys}")
                            print(f"      -> Eliminando indice incorrecto...")
                            coll.drop_index(name)
                            coll.create_index(keys, name=name, **options)
                            print(f"      -> [OK] Indice corregido")
                            fixed += 1
                            continue
                    
                    # Check 2: Same keys exist with different name
                    if key_tuple in existing_by_keys:
                        existing_name = existing_by_keys[key_tuple]
                        if existing_name == "_id":
                            # Special case: don't touch _id index
                            print(f"    [WARN] {name}: conflicto con indice _id, creando con nombre alternativo...")
                            coll.create_index(keys, name=name, **options)
                            created += 1
                        else:
                            # Keys exist with different name - DROP old and CREATE with correct name
                            print(f"    [WARN] {name}: ya existe como '{existing_name}'")
                            print(f"      -> Eliminando indice '{existing_name}'...")
                            coll.drop_index(existing_name)
                            coll.create_index(keys, name=name, **options)
                            print(f"      -> [OK] Indice renombrado a {name}")
                            fixed += 1
                        continue
                    
                    # Check 3: Index doesn't exist - CREATE
                    print(f"    -> Creando {name}...")
                    coll.create_index(keys, name=name, **options)
                    print(f"      -> [OK] Indice creado")
                    created += 1
                    
                except Exception as e:
                    errors += 1
                    print(f"    [ERROR] {name}: {e}")
        
        print("\n" + "=" * 60)
        print("RESUMEN DE INDICES")
        print("=" * 60)
        print(f"  [OK] Creados:    {created}")
        print(f"  [FIX] Corregidos: {fixed}")
        print(f"  [SKIP] Saltados:  {skipped}")
        print(f"  [ERROR] Errores:  {errors}")
        print("=" * 60)
        
        if errors == 0:
            print("\n[OK] Todos los indices verificados/creados exitosamente")
        else:
            print(f"\n[WARN] {errors} indice(s) fallaron - revisar logs")
        
        return errors == 0
    
    def create_rollback_script(self):
        """Generate rollback script"""
        print("\n" + "=" * 60)
        print("GENERANDO SCRIPT DE ROLLBACK")
        print("=" * 60)
        
        rollback_path = os.path.join(self.backup_path, "rollback.sh")
        
        content = f"""#!/bin/bash
# Rollback Script - Backup: {self.backup_timestamp}
# Usage: bash rollback.sh

echo "Ejecutando rollback..."

# Stop services
docker-compose down

# Restore MongoDB from backup
docker volume rm recopilarnovelas_mongodb_data
docker volume create recopilarnovelas_mongodb_data

# Restore data
mongorestore --host {MONGODB_HOST} --port {MONGODB_PORT} --db {MONGODB_DATABASE} \\
    --drop {self.backup_path}

# Restart services
docker-compose up -d

echo "Rollback completado"
"""
        
        with open(rollback_path, "w") as f:
            f.write(content)
        
        os.chmod(rollback_path, 0o755)
        print(f"  ✓ Script de rollback: {rollback_path}")
        
        return rollback_path
    
    def run_full_migration(self):
        """Execute complete migration pipeline"""
        # Phase 1: Export
        self.export_collections()
        
        # Phase 2: Verify
        if not self.verify_data():
            print("\n⚠️ Verificación fallida. Verifique los datos antes de continuar.")
            response = input("¿Continuar de todos modos? (s/n): ")
            if response.lower() != 's':
                sys.exit(1)
        
        # Phase 3: Import with indexes
        self.import_with_indexes()
        
        # Phase 4: Generate rollback
        self.create_rollback_script()
        
        print("\n" + "=" * 60)
        print("MIGRACIÓN COMPLETADA")
        print("=" * 60)
        print(f"Backup: {self.backup_path}")
        print("Ejecute: python manage.py migrate para actualizar esquemas Django")


def main():
    parser = argparse.ArgumentParser(description="MongoDB Migration Tool")
    parser.add_argument(
        "--phase",
        choices=["export", "verify", "import", "rollback", "full"],
        default="full",
        help="Phase to execute"
    )
    parser.add_argument(
        "--host",
        default=MONGODB_HOST,
        help="MongoDB host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=MONGODB_PORT,
        help="MongoDB port"
    )
    
    args = parser.parse_args()
    
    # Connect to MongoDB
    client = MongoClient(
        host=args.host,
        port=args.port,
        serverSelectionTimeoutMS=5000
    )
    db = client[MONGODB_DATABASE]
    
    migrator = MongoMigrator(db)
    
    if args.phase == "export":
        migrator.export_collections()
    elif args.phase == "verify":
        migrator.verify_data()
    elif args.phase == "import":
        migrator.import_with_indexes()
    elif args.phase == "full":
        migrator.run_full_migration()
    
    client.close()


if __name__ == "__main__":
    main()