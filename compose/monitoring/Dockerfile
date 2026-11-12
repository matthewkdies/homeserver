FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:b3c9a3976cc30c42f9217c1bdef2819e43defa2bf36eee85b50fd7bc5aa8a89d AS tautulli-binary
FROM druggeri/nut_exporter:3.3.0@sha256:276460d141c732772f8b1fcd785a7de272473e6d39fd85c32b163efc2999cb9a AS nut-binary

FROM alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf AS base
RUN apk add --no-cache ca-certificates

FROM base AS tautulli-exporter
COPY --from=tautulli-binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]

FROM base AS nut-exporter
COPY --from=nut-binary /nut_exporter /nut_exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/nut_exporter"]
