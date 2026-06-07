#!/bin/bash
#
# Gestion Docker de l'application Achat-Revente
# Usage: ./run.sh [build|up|down|restart|logs|ps]
#
set -e

# Se placer dans le dossier du script (docker/)
cd "$(dirname "$0")"

PROJECT_ROOT="$(cd .. && pwd)"

# Détection de la commande compose (v2 plugin ou v1 standalone)
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "[!] Erreur : docker compose introuvable. Installez Docker."
    exit 1
fi

# S'assurer que les cibles des bind-mounts existent côté hôte
prepare() {
    [ -f "$PROJECT_ROOT/database.db" ] || touch "$PROJECT_ROOT/database.db"
    mkdir -p "$PROJECT_ROOT/static/uploads"
}

ACTION="${1:-up}"

case "$ACTION" in
    build)
        prepare
        echo "[+] Build de l'image..."
        $COMPOSE build
        ;;
    up)
        prepare
        echo "[+] Build + démarrage des conteneurs..."
        $COMPOSE up -d --build
        echo "[+] Application disponible sur http://localhost:9096"
        ;;
    down)
        echo "[+] Arrêt et suppression des conteneurs..."
        $COMPOSE down
        ;;
    restart)
        $0 down
        $0 up
        ;;
    logs)
        $COMPOSE logs -f
        ;;
    ps)
        $COMPOSE ps
        ;;
    *)
        echo "Usage: $0 [build|up|down|restart|logs|ps]"
        exit 1
        ;;
esac
