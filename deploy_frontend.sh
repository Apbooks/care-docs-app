#!/usr/bin/env bash
# Helper to rebuild and restart only the frontend service with a PUBLIC_API_URL
# Usage: PUBLIC_API_URL=http://host:8000/api ./deploy_frontend.sh

set -euo pipefail

: ${PUBLIC_API_URL:="http://localhost:8000"}
COMPOSE_FILE="docker-compose.prod.yml"

echo "Building frontend with PUBLIC_API_URL=${PUBLIC_API_URL}"
export PUBLIC_API_URL

docker compose -f "${COMPOSE_FILE}" build frontend

echo "Recreating frontend service"
docker compose -f "${COMPOSE_FILE}" up -d --no-deps --force-recreate frontend

echo "Frontend deployed."
