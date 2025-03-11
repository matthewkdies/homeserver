#!/usr/bin/bash

set -e

DATE=$(date +"%d%b%y")
docker build \
    --file "${COMPOSE_DIR}/football-pool/football-pool/prod/prod.dockerfile" \
    --tag matthewkdies/football-pool:latest \
    --tag matthewkdies/football-pool:${DATE} \
    --build-arg UID=$(id -u football-pool) --build-arg GID=$(id -g football-pool) \
    ${COMPOSE_DIR}/football-pool/football-pool

docker push matthewkdies/football-pool:latest
docker push matthewkdies/football-pool:${DATE}
