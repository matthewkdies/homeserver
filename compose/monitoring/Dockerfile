FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:08fb9402c2f313e5cb99cf3b517471f7cb3fd23552067db5f0fadbcf26acb0d8 AS binary
FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
