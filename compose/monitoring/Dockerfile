FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:08fb9402c2f313e5cb99cf3b517471f7cb3fd23552067db5f0fadbcf26acb0d8 AS tautulli-binary
FROM druggeri/nut_exporter:2.5.2@sha256:c5d6835ce340f861d257d52af7151c531125ebe0e208a823e8ec7ad9355671c9 AS nut-binary

FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a AS base
RUN apk add --no-cache ca-certificates

FROM base AS tautulli-exporter
COPY --from=tautulli-binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]

FROM base AS nut-exporter
COPY --from=nut-binary /nut_exporter /nut_exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/nut_exporter"]
