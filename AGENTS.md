# AGENTS.md — Guidelines for AI Agents

## Overview
This repository manages the orchestration, configuration, and automation for a live Linux home server (`matthewkdies/homeserver`). It runs 30+ production Docker Compose stacks alongside system maintenance scripts, reverse proxy routing (Caddy), internal DNS (Pi-hole), authentication (Authelia), and automated updates (Renovate).

Treat this environment as a **live production system**. Prioritize safety, reproducibility, and minimal disruption to active services.

---

## 1. Directory Structure & Naming Conventions

Maintain strict consistency with existing directory and naming standards:

| Directory | Purpose & Naming Conventions |
| :--- | :--- |
| `compose/<service>/` | Docker Compose stack configurations. Each folder **must** contain `<service>-compose.yaml` (e.g., `compose/authelia/authelia-compose.yaml`, `compose/mealie/mealie-compose.yaml`). Any stack-specific documentation or Dockerfiles reside in this folder. |
| `docker/<service>/` | Persistent container state, mounted configs, and application data (gitignored). **Never track volume data in git.** |
| `docker/secrets/` | Host secrets storage (`chmod 600` files, gitignored). Secrets are mounted in compose stacks via Docker secrets referencing `${SECRETS_DIR}/<secret_name>`. |
| `docker/log/` | Centralized logs for host maintenance scripts (`update_containers.log`, `backup_volumes.log`, etc.). |
| `scripts/` | Host utility scripts, maintenance automation, and custom container entrypoints. Shell scripts use `.sh` (or bare executable name for top-level CLI commands like `recompose` or `reload-caddy`). |
| `scripts/tests/` | Pytest test files for Python scripts, following `test_<script_name>.py`. |
| `fail2ban/` | Host intrusion prevention jails (`jail.d/`), filters (`filter.d/`), and custom actions (`action.d/`). |
| `changelog.md` | Follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/). Updating the latest `## [X.Y.Z]` version triggers automated GitHub releases via `.github/workflows/automatic-versioning.yaml` upon merging to `main`. |

### Standard Environment Variables
The host loads global server paths via `~/.envvars`:
- `DOCUMENTS_DIR`: `/home/matthewkdies/Documents` (repository root)
- `COMPOSE_DIR`: `${DOCUMENTS_DIR}/compose`
- `SCRIPTS_DIR`: `${DOCUMENTS_DIR}/scripts`
- `DOCKER_DIR`: `${DOCUMENTS_DIR}/docker`
- `SECRETS_DIR`: `${DOCKER_DIR}/secrets`

---

## 2. Environment & Command Execution Guidelines

### Environment Variables & PATH Loading
The agent runs commands in non-interactive subshells, which do **not** automatically source `~/.bashrc`. Consequently, custom environment variables and user binary paths may be unset in fresh subshell calls unless explicitly loaded:
- **Binary Execution (`~/.local/bin`)**: Essential development binaries (such as `uv`, `prek`, `ruff`, `detect-secrets`, `rg`, and custom Python interpreters) are installed in `~/.local/bin`. Always ensure commands look in `~/.local/bin` (or prefix with `PATH="${HOME}/.local/bin:${PATH}"`) when executing CLI utilities.
- **Auto-Loading `~/.envvars`**: Server paths and configuration variables reside in `~/.envvars`. Whenever a command or script depends on environment variables (like `${SECRETS_DIR}`, `${DOCUMENTS_DIR}`, `${DOCKER_DIR}`, or `${COMPOSE_DIR}`), automatically source `~/.envvars` upfront:
  ```bash
  [ -f ~/.envvars ] && . ~/.envvars
  ```
- **Shell Scripts**: Any host or maintenance script in `scripts/` should proactively source `~/.envvars` near the top:
  ```bash
  if [ -f "${HOME}/.envvars" ]; then
      . "${HOME}/.envvars"
  fi
  ```

### Command Execution
- **Use Real Linux Commands**: Execute direct, standard Linux / Bash commands (`docker`, `docker compose`, `systemctl`, `sed`, `awk`, `grep`, `find`, `curl`, `jq`, `gh`, `tail`) rather than generating ad-hoc Python scripts to perform basic shell or inspection tasks. Real shell commands are transparent, easy to audit, and simple to approve.
- **Use Existing Repository Helpers**:
  - Recompose a stack cleanly: `scripts/recompose <path_to_compose_file>`
  - Hot-reload Caddy reverse proxy: `scripts/reload-caddy`
- **Avoid Interactive Prompts**: Ensure commands run non-interactively (e.g., `-y`, `--batch`, `-q`, or `-d` / `--detach` where appropriate).

---

## 3. Scoped & Appropriate Testing

Verify changes using **targeted, relevant tools** based solely on the files modified. Avoid running repo-wide test suites that test untouched systems:

### Docker Compose Changes (`compose/*/*compose*.yaml`)
- Validate compose syntax without starting containers:
  ```bash
  docker compose -f compose/<service>/<service>-compose.yaml config -q
  ```
- If environment variables or dummy secrets are required for config parsing in CI/dry-run, reference how `.github/workflows/ci.yaml` mocks missing secrets.

### Shell Script Changes (`scripts/*.sh`)
- Run ShellCheck targeting only modified shell scripts:
  ```bash
  shellcheck --severity=warning scripts/<modified_script>.sh
  ```
- Optional formatting verification with `shfmt`:
  ```bash
  shfmt -d scripts/<modified_script>.sh
  ```

### Python Script Changes (`scripts/*.py` & `scripts/tests/*.py`)
- Do **not** run Python tests if Python files were not modified.
- When Python scripts or tests are changed, run targeted tests using `uv`:
  ```bash
  PYTHONPATH=scripts uv run --with pytest --with requests --with pydantic pytest scripts/tests/test_<name>.py
  ```
- Check linting on modified Python files:
  ```bash
  ruff check scripts/<modified_script>.py
  ```

### Pre-commit Hooks (`prek`)
- `.git/hooks/pre-commit` is managed by `prek` and executes automatically before every `git commit`.
- Run `prek` on modified files before committing to prevent rejected commits:
  ```bash
  prek run --files <path/to/modified/file>
  ```

---

## 4. Troubleshooting & Container Observability

When debugging service health, startup errors, or network anomalies:

1. **Review Container Logs**:
   ```bash
   # View recent logs for a specific service
   docker logs --tail 100 <container_name>

   # Follow live output during an operation
   docker logs -f <container_name>
   ```
2. **Inspect Container Health**:
   ```bash
   # Check Docker healthcheck status and last failure message
   docker inspect --format='{{json .State.Health}}' <container_name> | jq .

   # Check exit code and status
   docker inspect --format='{{.State.Status}} (exit code: {{.State.ExitCode}})' <container_name>
   ```
3. **Check Host & Maintenance Logs**:
   Review log outputs in `docker/log/` for cron jobs and background automations:
   - `docker/log/update_containers.log`
   - `docker/log/backup_volumes.log`
   - `docker/log/disk_monitor.log`
   - `docker/log/weekly_ha_suggestions.log`
4. **Network & Ingress Debugging**:
   - Caddy reverse proxy logs: `docker logs --tail 100 caddy`
   - Test internal split-horizon DNS routing: verify domains resolve to `10.144.88.102` per `compose/caddy/cloudflare-pihole-integration.md`.

---

## 5. Safety, Secrets & Production Safeguards

- **Never Commit Secrets**: Do not commit API tokens, passwords, `.env` files, or contents of `docker/secrets/`. All secrets must use file-based secrets referenced via environment variables.
- **Docker Secret Syntax**: Always reference host secrets as `${SECRETS_DIR}/<secret_name>`. The CI suite (`.github/workflows/ci.yaml`) specifically matches this regex pattern to generate dummy secrets during automated compose validation.
- **Secrets Baseline (`.secrets.baseline`)**: High-entropy strings (tokens, hashes) will trigger `detect-secrets` in `prek`. If a legitimate non-secret hash triggers a false positive, update the baseline:
  ```bash
  detect-secrets scan --baseline .secrets.baseline
  ```
- **Never Run Destructive Pruning**: Do not run `docker system prune --volumes`, `docker volume rm`, or commands that delete untracked files in `docker/` without explicit user permission.
- **Image Pinning & Updates**: Compose images are typically pinned by exact version tag and `sha256` digest for reproducibility. Container updates are managed automatically by Renovate (`compose/renovate/`) and `scripts/update_containers.sh`.

---

## 6. Web Ingress & Service Lifecycle

When adding or modifying an HTTP web service routed through Caddy:

### 1. `webapps` Network & Static IP Assignment
All web services routed by Caddy attach to the external `webapps` network (`172.19.0.0/16`).
- **Hardcoded Static IP**: Any container added to `webapps` **must hardcode its IP address** (`ipv4_address`) and **increment to the next available IP**.
- **Finding the Next IP**: Inspect the highest currently assigned IP across all compose stacks:
  ```bash
  grep -rohP '172\.19\.0\.\K[0-9]+' compose/*/*compose*.yaml | sort -un | tail -1
  ```
- **Compose Definition Pattern**:
  ```yaml
  services:
    my-service:
      container_name: my-service
      # ...
      networks:
        webapps:
          ipv4_address: 172.19.0.<next_ip>

  networks:
    webapps:
      external: true
  ```

### 2. Caddy Reverse Proxy & Routing
- Add the route block in `compose/caddy/config/Caddyfile`.
- Import standard snippets:
  - `import cloudflare_tls`
  - `import security_headers`
  - `import local_network_only` (default for private apps) or omit for public access
  - `import use_authelia` (if Authelia SSO / MFA protection is required)
- Apply changes with zero downtime:
  ```bash
  scripts/reload-caddy
  ```
- **Internal DNS**: Subdomains of `mattdies.com` automatically resolve to Caddy (`10.144.88.102`) via Pi-hole's wildcard dnsmasq configuration (`address=/mattdies.com/10.144.88.102`). No manual Pi-hole DNS record is required.

### 3. Service Inventory Synchronization
- Register the new service in `SERVICE_METADATA` within `scripts/generate_services_matrix.py`.
- Run the script to regenerate the markdown services table in `README.md`:
  ```bash
  python3 scripts/generate_services_matrix.py
  ```
