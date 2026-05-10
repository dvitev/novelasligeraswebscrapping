#!/bin/bash
# =============================================================================
# logs.sh - Ver logs de todos los servicios con colores
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

SERVICES=("mongodb" "redis" "api" "selenium-worker" "celery-beat" "frontend")

COLOR_MAPPING=(
    "mongodb:36"          # Cyan
    "redis:35"            # Magenta
    "api:32"             # Green
    "selenium-worker:33" # Yellow
    "celery-beat:34"     # Blue
    "frontend:31"        # Red
)

show_usage() {
    echo "Uso: $0 [servicio|all] [opciones]"
    echo ""
    echo "Servicios disponibles:"
    for svc in "${SERVICES[@]}"; do
        echo "  - $svc"
    done
    echo ""
    echo "Opciones de Docker Compose:"
    echo "  --follow (-f)   Follow logs"
    echo "  --since         Mostrar logs desde tiempo relativo (ej: 1h)"
    echo "  --tail          Número de líneas a mostrar (default: 50)"
}

SERVICE="${1:-all}"
shift || true

case "$SERVICE" in
    all)
        echo "========================================"
        echo "  Logs de todos los servicios"
        echo "========================================"
        docker-compose logs -f --tail=50 --since=5m
        ;;
    -h|--help)
        show_usage
        exit 0
        ;;
    *)
        if [[ " ${SERVICES[*]} " =~ " $SERVICE " ]]; then
            echo "========================================"
            echo "  Logs de $SERVICE"
            echo "========================================"
            docker-compose logs -f --tail=50 "$SERVICE" "$@"
        else
            echo "Error: Servicio desconocido '$SERVICE'"
            echo ""
            show_usage
            exit 1
        fi
        ;;
esac