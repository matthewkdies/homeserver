#!/bin/bash
# note that I name this file a bit differently because I don't run it on my own
# I have it run as a daily cron job at 4 AM instead
set -euo pipefail

echo "Starting Caddy update process at $(date)"

# pull latest base images
docker pull caddy:2-builder-alpine
docker pull caddy:2

# build and restart using docker-compose
docker compose --file "${COMPOSE_DIR}/caddy/caddy-compose.yaml" build
docker compose --file "${COMPOSE_DIR}/caddy/caddy-compose.yaml" restart

echo "Caddy update process completed successfully at $(date)"
