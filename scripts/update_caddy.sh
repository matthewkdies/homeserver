#!/bin/bash
# note that I name this file a bit differently because I don't run it on my own
# I have it run as a daily cron job at 4 AM instead
set -euo pipefail

update_caddy() {
    echo "Starting Caddy update process at $(date)"

    # pull latest base images
    docker pull caddy:2-builder-alpine
    docker pull caddy:2

    # build and restart using docker-compose
    docker compose --file "${COMPOSE_DIR}/caddy/caddy-compose.yaml" build
    docker compose --file "${COMPOSE_DIR}/caddy/caddy-compose.yaml" up --detach

    echo "Caddy update process completed successfully at $(date)"
}

# call the function, then "chain" calls to update ntfy
# https://docs.ntfy.sh/examples/#cronjobs
update_caddy \
    && curl \
    -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: Caddy Updated" \
    -H "Priority: low" \
    -H "Tags: globe_with_meridians" \
    -d "Successfully updated Caddy." \
    "https://ntfy.mattdies.com/${NTFY_SERVER_HEALTH_TOPIC}"

