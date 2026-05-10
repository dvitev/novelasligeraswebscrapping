#!/bin/bash
# =============================================================================
# backup-mongodb.sh - Backup diario de MongoDB
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mongodb_backup_${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

mkdir -p "$BACKUP_PATH"

MONGODB_HOST="${MONGODB_HOST:-localhost}"
MONGODB_PORT="${MONGODB_PORT:-27017}"
MONGODB_DATABASE="${MONGODB_DATABASE:-recopilarnovelas}"

echo "========================================"
echo "  Backup de MongoDB"
echo "========================================"
echo "  Host: $MONGODB_HOST:$MONGODB_PORT"
echo "  Database: $MONGODB_DATABASE"
echo "  Destination: $BACKUP_PATH"
echo ""

docker run --rm \
    -v "$BACKUP_PATH:/backup" \
    mongo:7 \
    mongodump \
        --host="$MONGODB_HOST" \
        --port="$MONGODB_PORT" \
        --db="$MONGODB_DATABASE" \
        --out=/backup \
        --gzip

COMPRESSION_RATIO=$(du -sh "$BACKUP_PATH" | cut -f1)

echo ""
echo "========================================"
echo "  Backup completado exitosamente"
echo "========================================"
echo "  Tamaño: $COMPRESSION_RATIO"
echo "  Ubicación: $BACKUP_PATH"
echo ""

RETENTION_DAYS="${RETENTION_DAYS:-7}"
echo "Limpiando backups antiguos (más de $RETENTION_DAYS días)..."
find "$BACKUP_DIR" -type d -name "mongodb_backup_*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true

echo "Listo."