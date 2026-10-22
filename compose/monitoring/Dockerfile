FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:cd6716e39f5095624337bc4cce9036f2c478575e6ccafe3e1576a3168ba4c83e AS binary
FROM alpine:3.24@sha256:71e9b7bae160ba167fa17414401b94cbcdaf3c32feeab9298bd794a2a0614c35
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
