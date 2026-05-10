#!/bin/bash
# =============================================================================
# restore-mongodb.sh - Restaurar MongoDB desde backup
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BACKUP_DIR:-./backups}"

MONGODB_HOST="${MONGODB_HOST:-localhost}"
MONGODB_PORT="${MONGODB_PORT:-27017}"
MONGODB_DATABASE="${MONGODB_DATABASE:-recopilarnovelas}"

echo "========================================"
echo "  Restaurar MongoDB desde Backup"
echo "========================================"
echo ""

if [ $# -eq 0 ]; then
    echo "Uso: $0 <backup_name>"
    echo ""
    echo "Backups disponibles:"
    ls -1 "$BACKUP_DIR" 2>/dev/null | grep "mongodb_backup_" || echo "  No hay backups disponibles"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "Error: Backup no encontrado: $BACKUP_PATH"
    exit 1
fi

echo "Advertencia: Esto eliminará la base de datos actual '$MONGODB_DATABASE'"
echo "y la reemplazará con el backup '$BACKUP_NAME'."
echo ""
read -p "Continuar? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo ""
echo "Restaurando..."

docker run --rm \
    -v "$BACKUP_PATH:/backup" \
    mongo:7 \
    mongorestore \
        --host="$MONGODB_HOST" \
        --port="$MONGODB_PORT" \
        --db="$MONGODB_DATABASE" \
        --drop \
        --gzip \
        /backup/$MONGODB_DATABASE

echo ""
echo "========================================"
echo "  Restauración completada"
echo "========================================"