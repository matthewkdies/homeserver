# Dispatcharr & Teamarr Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Dispatcharr (IPTV proxy) and Teamarr (sports EPG generator) in the `arr-suite` stack with Mullvad VPN routing via Gluetun, internal-only ports, static IP for Teamarr, Authelia-protected Caddy reverse proxies, and host accessibility for Plex DVR.

**Architecture:** Dispatcharr joins Gluetun's network namespace (`network_mode: service:gluetun`) with healthcheck dependency, exposing internal port `9191` through Gluetun. Teamarr runs on the `webapps` bridge network with static IP `172.19.0.28`, exposing internal port `9195`. Caddy reverse proxies `dispatcharr.mattdies.com` and `teamarr.mattdies.com` with Authelia forward authentication. Plex connects directly to Gluetun's bridge IP (`172.19.0.15:9191`).

**Tech Stack:** Docker Compose v2, Gluetun (WireGuard VPN), Dispatcharr AIO (`ghcr.io/dispatcharr/dispatcharr:latest`), Teamarr (`ghcr.io/pharaoh-labs/teamarr:latest`), Caddy, Authelia.

**Spec:** [docs/superpowers/specs/2026-10-13-dispatcharr-teamarr-design.md](file:///home/matthewkdies/Documents/docs/superpowers/specs/2026-10-13-dispatcharr-teamarr-design.md)

## Global Constraints

- Dispatcharr must route all outbound traffic through Gluetun (`network_mode: service:gluetun`).
- Teamarr must run on `networks: webapps` with static IP `172.19.0.28` (disregard static IP on Dispatcharr as it inherits `172.19.0.15` from Gluetun).
- No container ports may be exposed directly to the host (`ports:` is forbidden for both services; use `expose:`).
- Caddy endpoints must import `use_authelia`, `cloudflare_dns`, `local_network_only`, and `log_for_app`.
- Named volumes `dispatcharr_data` and `teamarr_data` must be defined for persistent state.

---

### Task 1: Add Dispatcharr and Teamarr Services to `arr-suite-compose.yaml`

**Files:**
- Modify: `compose/arr-suite/arr-suite-compose.yaml:334-338` (gluetun expose)
- Modify: `compose/arr-suite/arr-suite-compose.yaml:520-521` (service declarations)
- Modify: `compose/arr-suite/arr-suite-compose.yaml:555-558` (named volumes)

**Interfaces:**
- Consumes: `gluetun` service definition and `webapps` external network in `arr-suite-compose.yaml`.
- Produces: `dispatcharr` service running on Gluetun network; `teamarr` service on `webapps` (`172.19.0.28:9195`); Gluetun exposing internal port `9191`.

- [ ] **Step 1: Check baseline compose syntax**

Run:
```bash
docker compose -f /home/matthewkdies/Documents/compose/arr-suite/arr-suite-compose.yaml config --quiet
```
Expected: Exit code 0 (no syntax errors).

- [ ] **Step 2: Add port 9191 to Gluetun expose list in `compose/arr-suite/arr-suite-compose.yaml`**

In the `gluetun` service block, update `expose:`:
```yaml
    expose:
      # since gluetun acts as a network, everything that runs on it needs exposed here
      # so in order to expose apps on the VPN to the internet, we need to expose ports here
      - 8090 # qbittorrent
      - 9191 # dispatcharr
```

- [ ] **Step 3: Add `dispatcharr` and `teamarr` service definitions to `compose/arr-suite/arr-suite-compose.yaml`**

Add the following service blocks right after `maintainerr`:
```yaml
  # IPTV stream proxy and EPG management
  dispatcharr:
    image: ghcr.io/dispatcharr/dispatcharr:latest
    container_name: dispatcharr
    restart: unless-stopped
    network_mode: service:gluetun
    depends_on:
      gluetun:
        condition: service_healthy
    environment:
      - TZ=America/New_York
      - DISPATCHARR_ENV=aio
      - REDIS_HOST=localhost
      - CELERY_BROKER_URL=redis://localhost:6379/0
      - DISPATCHARR_LOG_LEVEL=info
      - DISPATCHARR_PORT=9191
      - DISPATCHARR_TRUSTED_PROXIES=172.19.0.0/16
    volumes:
      - dispatcharr_data:/data
    security_opt:
      - no-new-privileges:true

  # sports channel and dynamic EPG generator for Dispatcharr
  teamarr:
    image: ghcr.io/pharaoh-labs/teamarr:latest
    container_name: teamarr
    hostname: teamarr
    restart: unless-stopped
    environment:
      - TZ=America/New_York
    volumes:
      - teamarr_data:/app/data
    expose:
      - 9195
    networks:
      webapps:
        ipv4_address: 172.19.0.28 # static IP for in-app config
    security_opt:
      - no-new-privileges:true
    depends_on:
      - dispatcharr
```

- [ ] **Step 4: Add `dispatcharr_data` and `teamarr_data` to top-level `volumes:`**

In the `volumes:` section at the bottom of `compose/arr-suite/arr-suite-compose.yaml`, add:
```yaml
  dispatcharr_data:
  teamarr_data:
```

- [ ] **Step 5: Validate compose configuration syntax**

Run:
```bash
docker compose -f /home/matthewkdies/Documents/compose/arr-suite/arr-suite-compose.yaml config --quiet
```
Expected: Exit code 0 with no errors.

- [ ] **Step 6: Commit changes to git**

Run:
```bash
git add compose/arr-suite/arr-suite-compose.yaml
git commit -m "feat(arr-suite): add dispatcharr and teamarr services"
```
Expected: Pre-commit hooks pass and commit is created.

---

### Task 2: Configure Caddy Reverse Proxy for Dispatcharr and Teamarr

**Files:**
- Modify: `compose/caddy/config/Caddyfile:278-285`

**Interfaces:**
- Consumes: `gluetun:9191` (Dispatcharr) and `teamarr:9195` on `webapps` network.
- Produces: Reverse proxy routes for `dispatcharr.mattdies.com` and `teamarr.mattdies.com`.

- [ ] **Step 1: Check baseline Caddyfile syntax**

Run:
```bash
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
```
Expected: Output ends with `Valid configuration`.

- [ ] **Step 2: Add Caddyfile blocks for Dispatcharr and Teamarr**

Under the `# plex + arr suite` section (after the `maintainerr` block around line 278) in `compose/caddy/config/Caddyfile`, add:
```caddy
dispatcharr.mattdies.com {
	import use_authelia
	import cloudflare_dns
	import local_network_only
	import log_for_app "dispatcharr"
	reverse_proxy gluetun:9191
}

teamarr.mattdies.com {
	import use_authelia
	import cloudflare_dns
	import local_network_only
	import log_for_app "teamarr"
	reverse_proxy teamarr:9195
}
```

- [ ] **Step 3: Validate Caddy configuration**

Run:
```bash
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
```
Expected: Output contains `Valid configuration`.

- [ ] **Step 4: Commit changes to git**

Run:
```bash
git add compose/caddy/config/Caddyfile
git commit -m "feat(caddy): add reverse proxy routes for dispatcharr and teamarr"
```
Expected: Pre-commit hooks pass and commit is created.

---

### Task 3: Deploy and Verify Stack Runtime

**Files:**
- Test only (no files modified)

**Interfaces:**
- Consumes: Updated `arr-suite-compose.yaml` and `Caddyfile`.
- Produces: Running and healthy `gluetun`, `dispatcharr`, `teamarr`, and `caddy` containers.

- [ ] **Step 1: Deploy Gluetun, Dispatcharr, Teamarr, and recreate Qbittorrent**

Run:
```bash
docker compose -f /home/matthewkdies/Documents/compose/arr-suite/arr-suite-compose.yaml up -d gluetun dispatcharr teamarr qbittorrent
```
Expected: Gluetun, Dispatcharr, Teamarr, and Qbittorrent pulled/started in running state.

- [ ] **Step 2: Reload Caddy reverse proxy**

Run:
```bash
docker exec -w /etc/caddy caddy caddy reload --config /etc/caddy/Caddyfile
```
Expected: Output ends with `reload complete`.

- [ ] **Step 3: Verify Gluetun health and container statuses**

Run:
```bash
docker inspect --format='{{.State.Health.Status}}' gluetun
docker ps --filter "name=dispatcharr" --filter "name=teamarr" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
Expected: Gluetun is `healthy`, Dispatcharr and Teamarr status is `Up`.

- [ ] **Step 4: Verify Dispatcharr egress traffic is routed through Mullvad VPN**

Compare the host IP with Dispatcharr egress IP:
```bash
curl -s https://ipinfo.io/ip
docker exec dispatcharr curl -s https://ipinfo.io/ip
```
Expected: Host IP and Dispatcharr IP are different; Dispatcharr IP corresponds to Mullvad VPN (Zurich/Switzerland as configured in Gluetun).

- [ ] **Step 5: Verify Teamarr static IP assignment**

Run:
```bash
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' teamarr
```
Expected: `172.19.0.28`.

- [ ] **Step 6: Verify internal connectivity between Teamarr and Dispatcharr**

Run:
```bash
docker exec teamarr python3 -c "import urllib.request; resp = urllib.request.urlopen('http://gluetun:9191/'); print(resp.getcode())"
```
Expected: `200` (or valid HTTP response from Dispatcharr web server).

- [ ] **Step 7: Verify Plex reachability to Dispatcharr over host bridge routing**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://172.19.0.15:9191/
```
Expected: `200` (or `302`/`200` depending on initial setup redirect).

- [ ] **Step 8: Verify Caddy reverse proxy and Authelia protection**

Run:
```bash
curl -k -s -o /dev/null -w "%{http_code}\n" --resolve dispatcharr.mattdies.com:443:172.19.0.3 https://dispatcharr.mattdies.com/
curl -k -s -o /dev/null -w "%{http_code}\n" --resolve teamarr.mattdies.com:443:172.19.0.3 https://teamarr.mattdies.com/
```
Expected: `302` (redirect to Authelia login `auth.mattdies.com`) or `401`.
