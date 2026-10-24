FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:cd6716e39f5095624337bc4cce9036f2c478575e6ccafe3e1576a3168ba4c83e AS binary
FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
