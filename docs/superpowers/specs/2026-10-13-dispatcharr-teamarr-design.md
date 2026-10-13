# Dispatcharr & Teamarr Integration Design

## 1. Overview

This document specifies the integration of **Dispatcharr** (IPTV stream proxy, channel curator, and EPG manager) and **Teamarr** (sports schedule and dynamic EPG generator) into the existing self-hosted media server ecosystem.

The services will run as part of the `arr-suite` Docker Compose stack alongside Sonarr, Radarr, Prowlarr, Bazarr, and Gluetun. All outbound IPTV traffic from Dispatcharr will be routed through the Mullvad WireGuard VPN provided by Gluetun to prevent stream tracking and ISP throttling. Inbound web access is secured behind Authelia and Caddy reverse proxy using internal Docker networking without exposing container ports to the host.

---

## 2. Architecture & Network Topology

```mermaid
graph TD
    subgraph Host Network
        Plex["Plex Media Server (network_mode: host)"]
        LAN["Local Clients / Browsers (10.144.88.0/24)"]
    end

    subgraph webapps Docker Bridge (172.19.0.0/16)
        Caddy["Caddy (172.19.0.3)"]
        Authelia["Authelia (172.19.0.2)"]
        Teamarr["Teamarr (172.19.0.28:9195)"]

        subgraph Gluetun Network Namespace
            Gluetun["Gluetun Container (172.19.0.15)<br/>Mullvad WireGuard VPN"]
            Dispatcharr["Dispatcharr Container<br/>(service:gluetun, internal port 9191)"]
            Qbit["qbittorrent (internal port 8090)"]
        end
    end

    subgraph External
        IPTV["IPTV Provider Streams"]
        ESPN["ESPN APIs (Sports Schedules)"]
        CF["Cloudflare DNS"]
    end

    LAN -->|HTTPS / *.mattdies.com| Caddy
    Caddy -->|Forward Auth| Authelia
    Caddy -->|Reverse Proxy| Gluetun
    Caddy -->|Reverse Proxy| Teamarr

    Plex -->|HDHomeRun Emulation (172.19.0.15:9191)| Gluetun
    Teamarr -->|Channel/EPG Sync (gluetun:9191)| Gluetun
    Teamarr -->|HTTP/HTTPS| ESPN

    Dispatcharr -->|Tunneled Outbound Video Streams| Gluetun
    Gluetun -->|VPN WireGuard Tunnel| IPTV
```

### Key Architectural Decisions:
1. **VPN Routing**: Dispatcharr shares Gluetun's network namespace (`network_mode: service:gluetun`) and depends on Gluetun's health check (`depends_on: gluetun: condition: service_healthy`). All upstream IPTV connections exit via Mullvad.
2. **Teamarr Network Isolation**: Teamarr resides directly on the `webapps` bridge network (`172.19.0.28`). It queries public sports data (ESPN) without VPN interference or rate-limiting and pushes schedules to Dispatcharr via internal Docker networking (`http://gluetun:9191`).
3. **No Published Host Ports**: Neither Dispatcharr nor Teamarr publishes ports directly to the host (`ports:`). Instead, internal ports (`9191` and `9195`) are declared using `expose:` on Gluetun and Teamarr, respectively.
4. **Plex Routing**: Plex runs with `network_mode: host`. Linux automatically routes host packets destined for Docker bridge subnets (`172.19.0.0/16`), allowing Plex to communicate with Dispatcharr at `http://172.19.0.15:9191`.

---

## 3. Configuration Details

### 3.1 `arr-suite/arr-suite-compose.yaml` Modifications

#### Gluetun Service Update
Add port `9191` to Gluetun's `expose:` directive:
```yaml
  gluetun:
    image: qmcgaw/gluetun:v3
    container_name: gluetun
    hostname: gluetun
    cap_add:
      - NET_ADMIN
    expose:
      - 8090 # qbittorrent
      - 9191 # dispatcharr
...
```

#### Dispatcharr Service
Add `dispatcharr` with `network_mode: service:gluetun`:
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
```

#### Teamarr Service
Add `teamarr` attached to the `webapps` network:
```yaml
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

#### Named Volumes
Add both persistence volumes to the top-level `volumes:` section:
```yaml
volumes:
...
  dispatcharr_data:
  teamarr_data:
```

---

### 3.2 Caddyfile Configuration (`caddy/config/Caddyfile`)

Add two subdomain blocks under the `# plex + arr suite` section:

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

- **Authelia**: Inherits two-factor authentication because `*.mattdies.com` is configured with `policy: two_factor` in `docker/authelia/configuration.yml`.
- **Cloudflare Dynamic DNS**: Caddy's `dynamic_domains` directive will automatically detect and manage DNS records for these two new subdomains.
- **Local Network Restriction**: `local_network_only` restricts access to `10.144.88.0/24` and `172.19.0.0/16`.

---

## 4. Post-Deployment & Integration Steps

### 4.1 First-Time Setup of Dispatcharr
1. Navigate to `https://dispatcharr.mattdies.com`.
2. Authenticate through Authelia.
3. Complete initial superuser setup.
4. Go to **Settings** > **API Keys** and generate an API key for Teamarr.
5. In **Playlists / Providers**, add the M3U or Xtream Codes trial credentials provided by the IPTV provider.

### 4.2 First-Time Setup of Teamarr
1. Navigate to `https://teamarr.mattdies.com`.
2. Authenticate through Authelia.
3. Set the Dispatcharr URL to `http://gluetun:9191` (or `http://172.19.0.15:9191`).
4. Enter the Dispatcharr API key.
5. Select sports leagues/teams and configure automatic channel sync into Dispatcharr.

### 4.3 Connecting Dispatcharr to Plex Live TV & DVR
1. Open Plex Web UI at `https://plex.mattdies.com` or `http://10.144.88.102:32400/web`.
2. Navigate to **Settings** > **Live TV & DVR** > **Set up Plex DVR**.
3. When Plex begins searching for tuners, click **"Don't see your device? Enter its network address manually"**.
4. Enter `172.19.0.15:9191`.
5. Plex will query Dispatcharr's HDHomeRun emulation endpoint (`/device.xml`) and discover the virtual tuner channels.
6. Map XMLTV guide data from Dispatcharr (available at `http://172.19.0.15:9191/epg.xml` or via XMLTV file upload).

---

## 5. Verification & Testing Checklist

- [ ] Syntax check: Validate `docker compose -f arr-suite/arr-suite-compose.yaml config` passes with zero errors.
- [ ] Syntax check: Validate Caddyfile formatting and syntax via `docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile`.
- [ ] Deployment: Recreate Gluetun, Dispatcharr, and Teamarr (`docker compose -f arr-suite/arr-suite-compose.yaml up -d gluetun dispatcharr teamarr qbittorrent`).
- [ ] Reload Caddy: `docker exec -w /etc/caddy caddy caddy reload --config /etc/caddy/Caddyfile`.
- [ ] Healthcheck: Verify Gluetun health status remains `healthy`.
- [ ] VPN Verification: Execute `docker exec dispatcharr curl -s https://ipinfo.io/ip` or similar to confirm public IP matches Mullvad VPN egress IP, not home ISP IP.
- [ ] UI Reachability: Verify `https://dispatcharr.mattdies.com` and `https://teamarr.mattdies.com` load through Caddy and prompt for Authelia authentication.
- [ ] Internal Communication: Verify Teamarr can reach `http://gluetun:9191`.
- [ ] Plex Reachability: Verify host curl `curl -s http://172.19.0.15:9191/` succeeds.
