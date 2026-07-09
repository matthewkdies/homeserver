#!/usr/bin/bash

set -e

. /home/matthewkdies/.envvars

sudo modprobe ip_tables
docker compose -f "${COMPOSE_DIR}/wireguard/wireguard-compose.yaml" up --detach
