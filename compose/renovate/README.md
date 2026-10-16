# Renovate Self-Hosted Runner

This directory contains the self-hosted Renovate runner service for updating Docker Compose images across the `homeserver` stack.

## Configuration
- `config.js`: Runner configuration for the Renovate bot (platform, repo, cache path).
- `renovate-compose.yaml`: Docker Compose runner definition with UID/GID `12021:144` and secret mounting.
- Root `renovate.json5`: Policy configuration governing digest pinning, stability delays, and automerge rules.

## Manual Execution
To perform an immediate one-off update run:
```bash
. ~/.envvars
docker compose --file /home/matthewkdies/Documents/compose/renovate/renovate-compose.yaml run --rm renovate
```

To run with full dry-run logging (no PRs or commits created):
```bash
. ~/.envvars
docker compose --file /home/matthewkdies/Documents/compose/renovate/renovate-compose.yaml run --rm renovate renovate --dry-run=full
```
