FROM ghcr.io/mm503/tautulli-exporter:latest AS binary
FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
