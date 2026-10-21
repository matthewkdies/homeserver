# Home Server

![Version](https://img.shields.io/github/v/release/matthewkdies/homeserver)
![License](https://img.shields.io/github/license/matthewkdies/homeserver)
![Issues](https://img.shields.io/github/issues/matthewkdies/homeserver)
![Pull Requests](https://img.shields.io/github/issues-pr/matthewkdies/homeserver)
![Docker Compose Version](https://img.shields.io/badge/Docker%20Compose-v2-blue)
![Secrets Scan](https://img.shields.io/badge/Secrets%20Scan-Passing-brightgreen)

# Installation

Clone the repository to wherever you'd like on your host machine.
Pre-requisuites for this repository are essentially just Docker, though I might be forgetting something.
The scripts themselves are intended to run in `sh` or `bash`.
A lot of this is tightly coupled with my desired and existing setup, though I hope that things in here are helpful to you regardless!

```
# ssh
git clone git@github.com:matthewkdies/homeserver.git

# https
git clone https://github.com/matthewkdies/homeserver.git
```

# Prerequisites

Docker and Docker Compose must be available.

# Setup

I use a couple of environment variables throughout the stack that you might want to set for convenience.
To set them, I created a file at `~/.envvars` in which I export my environment variables, currently set with the following:
```bash
# configuration/docker dirs
export DOCUMENTS_DIR="/home/matthewkdies/Documents"
export DOCKER_DIR="${DOCUMENTS_DIR}/docker"
export COMPOSE_DIR="${DOCUMENTS_DIR}/compose"
export SCRIPTS_DIR="${DOCUMENTS_DIR}/scripts"
export SECRETS_DIR="${DOCKER_DIR}/secrets"
```

There are some other variables that I am not showing here, but that's the gist.
I then added to my `~/.bashrc` file to get them loaded:
```bash
# load environment variables
if [ -f ~/.envvars ]; then
    . ~/.envvars
fi
```

# Running

In order to run any of the files to start the included containers, I make the following assumptions:
1. You have a working knowledge of [Docker Compose](https://docs.docker.com/reference/compose-file/).
2. You will be able to interpret the files to see what you need to change to fit your specific setup. For example, changing the paths of secrets files or the values of environment variables.

Beyond that, starting a stack is as simple as `docker compose --file <path_to_file> up --detach`.

# Hosted Services

<!-- SERVICES_TABLE_START -->
| Service | Category | Description | Access Level | Compose Stack |
| :--- | :--- | :--- | :--- | :--- |
| **Ollama** | AI & Local LLM | Local LLM inference backend with NVIDIA GPU acceleration | `Internal Service` | [`llm`](./compose/llm/llm-compose.yaml) |
| **Open-WebUI** | AI & Local LLM | Web chat interface and agent orchestration for local LLMs | `Local Network Only` | [`llm`](./compose/llm/llm-compose.yaml) |
| **Authelia** | Core & Ingress | Single Sign-On (SSO) and Multi-Factor Authentication | `Local Network + MFA` | [`authelia`](./compose/authelia/authelia-compose.yaml) |
| **Caddy** | Core & Ingress | Reverse proxy with automatic HTTPS and Cloudflare DNS ([Guide](./compose/caddy/cloudflare-pihole-integration.md)) | `Public (Edge)` | [`caddy`](./compose/caddy/caddy-compose.yaml) |
| **Dozzle** | Core & Ingress | Real-time container log viewer and resource monitor | `Local Network + MFA` | [`dozzle`](./compose/dozzle/dozzle-compose.yaml) |
| **Ntfy** | Core & Ingress | Self-hosted push notification service for alerts | `Local Network Only` | [`ntfy`](./compose/ntfy/ntfy-compose.yaml) |
| **Pi-hole** | Core & Ingress | Network-wide ad and tracker blocking DNS sinkhole | `Local Network Only` | [`pihole`](./compose/pihole/pihole-nas-compose.yaml) |
| **Renovate** | Core & Ingress | Automated container and dependency update bot | `Internal Job` | [`renovate`](./compose/renovate/renovate-compose.yaml) |
| **Uptime Kuma** | Core & Ingress | Service uptime and health status monitoring | `Local Network + MFA` | [`uptime-kuma`](./compose/uptime-kuma/uptime-kuma-compose.yaml) |
| **WireGuard** | Core & Ingress | Fast and secure VPN tunnel for remote access | `Public (VPN Port)` | [`wireguard`](./compose/wireguard/wireguard-compose.yaml) |
| **Minecraft (Spigot)** | Gaming | Multiplayer Minecraft survival server | `Public (Game Port)` | [`minecraft`](./compose/minecraft/minecraft-compose.yaml) |
| **Bazarr** | Media & Streaming | Automated subtitle downloader for Sonarr and Radarr | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Dispatcharr** | Media & Streaming | IPTV stream and EPG guide management proxy | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Gluetun** | Media & Streaming | Secure VPN client container routing download traffic | `Internal VPN Client` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Lidarr** | Media & Streaming | Music collection manager and download automator | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Maintainerr** | Media & Streaming | Rule-based automated media cleanup and library maintenance | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Meloday** | Media & Streaming | Automated smart playlist generator for Plex music | `Internal Service` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Plex** | Media & Streaming | Central media server for movies, TV, and music streaming | `Public / Local` | [`plex`](./compose/plex/plex-compose.yaml) |
| **Prowlarr** | Media & Streaming | Torrent indexer and Usenet tracker aggregator | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Radarr** | Media & Streaming | Movie collection manager and download automator | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Radarr (4K)** | Media & Streaming | Dedicated 4K HDR movie collection manager | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Recyclarr** | Media & Streaming | Automated TRaSH Guides syncing for Sonarr and Radarr | `Internal Service` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Seerr** | Media & Streaming | Media request management and content discovery | `Public` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Slskd (Soulseek)** | Media & Streaming | Soulseek network client for music sharing | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Sonarr** | Media & Streaming | TV show collection manager and download automator | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Soularr** | Media & Streaming | Bridge linking Lidarr requests to Soulseek downloads | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Tautulli** | Media & Streaming | Plex monitoring, analytics, and watch history tracking | `Local Network Only` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Tdarr** | Media & Streaming | Distributed media transcoding and library optimization | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **qBittorrent** | Media & Streaming | BitTorrent client routed through Gluetun VPN | `Local Network + MFA` | [`arr-suite`](./compose/arr-suite/arr-suite-compose.yaml) |
| **Actual Budget** | Productivity & Personal | Privacy-focused personal budgeting application | `Local Network Only` | [`actual`](./compose/actual/actual-compose.yaml) |
| **Football Pool** | Productivity & Personal | Custom sports prediction and league pool web app | `Public` | [`football-pool`](./compose/football-pool/football-pool-compose.yaml) |
| **Immich** | Productivity & Personal | Self-hosted photo and video backup with AI search | `Local Network Only` | [`immich`](./compose/immich/immich-compose.yaml) |
| **LubeLogger** | Productivity & Personal | Vehicle service history, maintenance, and fuel tracker | `Local Network + MFA` | [`lubelogger`](./compose/lubelogger/lubelogger-compose.yaml) |
| **Mealie** | Productivity & Personal | Recipe manager, meal planner, and grocery list organizer | `Public (Rate-limited)` | [`mealie`](./compose/mealie/mealie-compose.yaml) |
| **Paperless-ngx** | Productivity & Personal | Document management and OCR archive system | `Local Network + MFA` | [`paperless`](./compose/paperless/paperless-compose.yaml) |
| **Home Assistant** | Smart Home & IoT | Central home automation and smart device coordinator | `Local Network Only` | [`home-assistant`](./compose/home-assistant/home-assistant-compose.yaml) |
| **Z-Wave JS UI** | Smart Home & IoT | Z-Wave device management panel and gateway | `Local Network + MFA` | [`home-assistant`](./compose/home-assistant/home-assistant-compose.yaml) |
<!-- SERVICES_TABLE_END -->

# Basic Structure

- [`compose/`](./compose/): Contains the Docker Compose files, Dockerfiles, configuration files, healthscripts, and documentation related to the Docker containers on my home server.
  - [**Cloudflare, Pi-hole, and Caddy Integration Guide**](./compose/caddy/cloudflare-pihole-integration.md): Comprehensive architecture guide covering split-horizon DNS, dynamic DNS automation, DNS-01 ACME TLS certificates, and defense-in-depth access controls.
- [`scripts/`](./scripts/): Contains the scripts that I use within containers and in common use.
- [`changelog.md`](./changelog.md): Documentation on updates to the repository.
- [`prek.toml`](./prek.toml): A `prek` config file that runs the [`detect-secrets`](https://github.com/Yelp/detect-secrets) CLI to prevent secrets from inadvertantly being committed to the remote repository.
- [`.github/workflows`](./.github/workflows/): Contains custom workflows, which currently includes making releases automatically.
