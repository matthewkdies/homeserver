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

## Automation (Systemd User Timer)
Automated daily execution is managed via a systemd user timer (`~/.config/systemd/user/renovate.timer`), scheduled for 04:00 AM daily with a 10-minute randomized delay.
Unit definitions are version-controlled in `compose/renovate/systemd/`.

### Setup
```bash
mkdir -p ~/.config/systemd/user
ln -sf /home/matthewkdies/Documents/compose/renovate/systemd/renovate.service ~/.config/systemd/user/renovate.service
ln -sf /home/matthewkdies/Documents/compose/renovate/systemd/renovate.timer ~/.config/systemd/user/renovate.timer
systemctl --user daemon-reload
systemctl --user enable --now renovate.timer
```

### Checking Status & Logs
Check timer status and next trigger:
```bash
systemctl --user list-timers renovate.timer
```

Trigger an immediate execution via systemd:
```bash
systemctl --user start renovate.service
```

Inspect execution logs:
```bash
journalctl --user -u renovate.service -e
```
