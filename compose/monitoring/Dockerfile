FROM ghcr.io/mm503/tautulli-exporter:latest@sha256:cd6716e39f5095624337bc4cce9036f2c478575e6ccafe3e1576a3168ba4c83e AS binary
FROM alpine:3.20@sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
RUN apk add --no-cache ca-certificates
COPY --from=binary /app/tautulli-exporter /app/tautulli-exporter
ENTRYPOINT ["/docker-entrypoint.sh", "/app/tautulli-exporter"]
