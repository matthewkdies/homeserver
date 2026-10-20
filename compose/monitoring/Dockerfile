FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:cd6716e39f5095624337bc4cce9036f2c478575e6ccafe3e1576a3168ba4c83e AS binary
FROM alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
