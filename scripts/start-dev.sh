#!/bin/bash
# =============================================================================
# start-dev.sh - Levantar todos los servicios en modo desarrollo
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "  Novelas Ligeras - Modo Desarrollo"
echo "========================================"

if [ ! -f .env ]; then
    echo "Copiando .env.example a .env..."
    cp .env.example .env
    echo "Por favor edita .env con tu configuración antes de continuar."
    exit 1
fi

echo "Levantando servicios con Docker Compose..."
docker-compose up -d

echo ""
echo "Esperando a que los servicios estén listos..."

echo "  - MongoDB..."
sleep 5

echo "  - Redis..."
sleep 3

echo "  - API Django..."
sleep 5

echo "  - Frontend Next.js..."
sleep 5

echo ""
echo "========================================"
echo "  Servicios iniciados"
echo "========================================"
echo ""
echo "  API Django:    http://localhost:8000"
echo "  Frontend:      http://localhost:3000"
echo "  MongoDB:       localhost:27017"
echo "  Redis:         localhost:6379"
echo ""
echo "Ver logs con: ./scripts/logs.sh"
echo "Detener con:  docker-compose down"
echo ""