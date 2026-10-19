#!/usr/bin/env python3
"""Generates a sanitized services matrix table for README.md.

Extracts services from Docker Compose stacks, maps them to human-readable
descriptions and access tiers, and updates the README.md table between markers.
This intentionally avoids publishing internal IPs, private host ports,
or internal domain names.
"""

from __future__ import annotations

import re
from pathlib import Path

START_MARKER = "<!-- SERVICES_TABLE_START -->"
END_MARKER = "<!-- SERVICES_TABLE_END -->"

# Comprehensive metadata mapping for known services
SERVICE_METADATA: dict[str, dict[str, str]] = {
    # Core Infrastructure & Ingress
    "caddy": {
        "name": "Caddy",
        "category": "Core & Ingress",
        "desc": "Reverse proxy with automatic HTTPS and Cloudflare DNS",
        "access": "Public (Edge)",
    },
    "authelia": {
        "name": "Authelia",
        "category": "Core & Ingress",
        "desc": "Single Sign-On (SSO) and Multi-Factor Authentication",
        "access": "Local Network + MFA",
    },
    "wireguard": {
        "name": "WireGuard",
        "category": "Core & Ingress",
        "desc": "Fast and secure VPN tunnel for remote access",
        "access": "Public (VPN Port)",
    },
    "pihole": {
        "name": "Pi-hole",
        "category": "Core & Ingress",
        "desc": "Network-wide ad and tracker blocking DNS sinkhole",
        "access": "Local Network Only",
    },
    "uptime-kuma": {
        "name": "Uptime Kuma",
        "category": "Core & Ingress",
        "desc": "Service uptime and health status monitoring",
        "access": "Local Network + MFA",
    },
    "dozzle": {
        "name": "Dozzle",
        "category": "Core & Ingress",
        "desc": "Real-time container log viewer and resource monitor",
        "access": "Local Network + MFA",
    },
    "renovate": {
        "name": "Renovate",
        "category": "Core & Ingress",
        "desc": "Automated container and dependency update bot",
        "access": "Internal Job",
    },
    "ntfy": {
        "name": "Ntfy",
        "category": "Core & Ingress",
        "desc": "Self-hosted push notification service for alerts",
        "access": "Local Network Only",
    },
    # Smart Home & IoT
    "homeassistant": {
        "name": "Home Assistant",
        "category": "Smart Home & IoT",
        "desc": "Central home automation and smart device coordinator",
        "access": "Local Network Only",
    },
    "zwave-js-ui": {
        "name": "Z-Wave JS UI",
        "category": "Smart Home & IoT",
        "desc": "Z-Wave device management panel and gateway",
        "access": "Local Network + MFA",
    },
    # Media & Streaming
    "plex": {
        "name": "Plex",
        "category": "Media & Streaming",
        "desc": "Central media server for movies, TV, and music streaming",
        "access": "Public / Local",
    },
    "tautulli": {
        "name": "Tautulli",
        "category": "Media & Streaming",
        "desc": "Plex monitoring, analytics, and watch history tracking",
        "access": "Local Network Only",
    },
    "seerr": {
        "name": "Seerr",
        "category": "Media & Streaming",
        "desc": "Media request management and content discovery",
        "access": "Public",
    },
    "sonarr": {
        "name": "Sonarr",
        "category": "Media & Streaming",
        "desc": "TV show collection manager and download automator",
        "access": "Local Network + MFA",
    },
    "radarr": {
        "name": "Radarr",
        "category": "Media & Streaming",
        "desc": "Movie collection manager and download automator",
        "access": "Local Network + MFA",
    },
    "radarr4k": {
        "name": "Radarr (4K)",
        "category": "Media & Streaming",
        "desc": "Dedicated 4K HDR movie collection manager",
        "access": "Local Network + MFA",
    },
    "lidarr": {
        "name": "Lidarr",
        "category": "Media & Streaming",
        "desc": "Music collection manager and download automator",
        "access": "Local Network + MFA",
    },
    "prowlarr": {
        "name": "Prowlarr",
        "category": "Media & Streaming",
        "desc": "Torrent indexer and Usenet tracker aggregator",
        "access": "Local Network + MFA",
    },
    "bazarr": {
        "name": "Bazarr",
        "category": "Media & Streaming",
        "desc": "Automated subtitle downloader for Sonarr and Radarr",
        "access": "Local Network + MFA",
    },
    "tdarr": {
        "name": "Tdarr",
        "category": "Media & Streaming",
        "desc": "Distributed media transcoding and library optimization",
        "access": "Local Network + MFA",
    },
    "gluetun": {
        "name": "Gluetun",
        "category": "Media & Streaming",
        "desc": "Secure VPN client container routing download traffic",
        "access": "Internal VPN Client",
    },
    "qbittorrent": {
        "name": "qBittorrent",
        "category": "Media & Streaming",
        "desc": "BitTorrent client routed through Gluetun VPN",
        "access": "Local Network + MFA",
    },
    "soulseek": {
        "name": "Slskd (Soulseek)",
        "category": "Media & Streaming",
        "desc": "Soulseek network client for music sharing",
        "access": "Local Network + MFA",
    },
    "soularr": {
        "name": "Soularr",
        "category": "Media & Streaming",
        "desc": "Bridge linking Lidarr requests to Soulseek downloads",
        "access": "Local Network + MFA",
    },
    "meloday": {
        "name": "Meloday",
        "category": "Media & Streaming",
        "desc": "Automated smart playlist generator for Plex music",
        "access": "Internal Service",
    },
    "maintainerr": {
        "name": "Maintainerr",
        "category": "Media & Streaming",
        "desc": "Rule-based automated media cleanup and library maintenance",
        "access": "Local Network + MFA",
    },
    "dispatcharr": {
        "name": "Dispatcharr",
        "category": "Media & Streaming",
        "desc": "IPTV stream and EPG guide management proxy",
        "access": "Local Network + MFA",
    },
    "recyclarr": {
        "name": "Recyclarr",
        "category": "Media & Streaming",
        "desc": "Automated TRaSH Guides syncing for Sonarr and Radarr",
        "access": "Internal Service",
    },
    # AI & Local LLM
    "ollama": {
        "name": "Ollama",
        "category": "AI & Local LLM",
        "desc": "Local LLM inference backend with NVIDIA GPU acceleration",
        "access": "Internal Service",
    },
    "open-webui": {
        "name": "Open-WebUI",
        "category": "AI & Local LLM",
        "desc": "Web chat interface and agent orchestration for local LLMs",
        "access": "Local Network Only",
    },
    # Productivity & Personal
    "actual_server": {
        "name": "Actual Budget",
        "category": "Productivity & Personal",
        "desc": "Privacy-focused personal budgeting application",
        "access": "Local Network Only",
    },
    "immich-server": {
        "name": "Immich",
        "category": "Productivity & Personal",
        "desc": "Self-hosted photo and video backup with AI search",
        "access": "Local Network Only",
    },
    "lubelogger": {
        "name": "LubeLogger",
        "category": "Productivity & Personal",
        "desc": "Vehicle service history, maintenance, and fuel tracker",
        "access": "Local Network + MFA",
    },
    "mealie": {
        "name": "Mealie",
        "category": "Productivity & Personal",
        "desc": "Recipe manager, meal planner, and grocery list organizer",
        "access": "Public (Rate-limited)",
    },
    "football-pool": {
        "name": "Football Pool",
        "category": "Productivity & Personal",
        "desc": "Custom sports prediction and league pool web app",
        "access": "Public",
    },
    "paperless": {
        "name": "Paperless-ngx",
        "category": "Productivity & Personal",
        "desc": "Document management and OCR archive system",
        "access": "Local Network + MFA",
    },
    "spigotserver": {
        "name": "Minecraft (Spigot)",
        "category": "Gaming",
        "desc": "Multiplayer Minecraft survival server",
        "access": "Public (Game Port)",
    },
}

# Backend support services to omit from top-level user service table
IGNORED_SERVICES = {
    "flaresolverr",
    "uptime-socket-proxy",
    "authelia-postgres-db",
    "football-pool-db",
    "immich-machine-learning",
    "redis",
    "database",
    "postgres",
    "mealie-postgres-db",
    "ntfy-postgres-db",
    "paperless-redis",
    "paperless-postgres",
}


def find_compose_files(compose_dir: Path) -> dict[str, str]:
    """Finds compose file relative paths for each service."""
    service_to_file: dict[str, str] = {}
    for cf in sorted(compose_dir.glob("*/*compose*.y*ml")):
        rel_path = f"./compose/{cf.parent.name}/{cf.name}"
        with open(cf, "r", encoding="utf-8") as f:
            content = f.read()
        # Simple extraction of top-level service names
        in_services = False
        for line in content.splitlines():
            if re.match(r"^services:\s*$", line):
                in_services = True
                continue
            if in_services:
                if re.match(r"^[a-zA-Z0-9_\-]+:\s*$", line) and not line.startswith("  "):
                    break  # reached next top-level block like volumes/networks
                svc_match = re.match(r"^  ([a-zA-Z0-9_\-]+):\s*$", line)
                if svc_match:
                    svc_name = svc_match.group(1)
                    if svc_name not in service_to_file:
                        service_to_file[svc_name] = rel_path
    return service_to_file


def generate_table(service_to_file: dict[str, str]) -> str:
    """Builds the Markdown table from known services."""
    lines = [
        "| Service | Category | Description | Access Level | Compose Stack |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    # Sort services by category then name
    categorized = []
    for svc_key, meta in SERVICE_METADATA.items():
        if svc_key in IGNORED_SERVICES:
            continue
        compose_link = (
            f"[`{Path(service_to_file[svc_key]).parent.name}`]({service_to_file[svc_key]})"
            if svc_key in service_to_file
            else "—"
        )
        categorized.append((meta["category"], meta["name"], meta["desc"], meta["access"], compose_link))

    categorized.sort(key=lambda x: (x[0], x[1]))

    for cat, name, desc, access, link in categorized:
        lines.append(f"| **{name}** | {cat} | {desc} | `{access}` | {link} |")

    return "\n".join(lines)


def update_readme(repo_dir: Path, table_md: str) -> None:
    """Inserts or replaces the service matrix table in README.md."""
    readme_path = repo_dir / "README.md"
    readme_content = readme_path.read_text(encoding="utf-8")

    block = f"{START_MARKER}\n{table_md}\n{END_MARKER}"

    if START_MARKER in readme_content and END_MARKER in readme_content:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        new_content = pattern.sub(block, readme_content)
    else:
        # Append before basic structure or at end of file
        section = f"\n# Hosted Services\n\n{block}\n"
        if "\n# Basic Structure" in readme_content:
            new_content = readme_content.replace("\n# Basic Structure", f"{section}\n# Basic Structure")
        else:
            new_content = readme_content + f"\n{section}"

    readme_path.write_text(new_content, encoding="utf-8")
    print(f"Successfully updated {readme_path}")


def main() -> None:
    repo_dir = Path(__file__).resolve().parent.parent
    compose_dir = repo_dir / "compose"
    svc_to_file = find_compose_files(compose_dir)
    table_md = generate_table(svc_to_file)
    update_readme(repo_dir, table_md)


if __name__ == "__main__":
    main()
