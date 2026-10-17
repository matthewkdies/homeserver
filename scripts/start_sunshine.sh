#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start Sunshine via systemd user service
systemctl --user start sunshine.service

if systemctl --user is-active --quiet sunshine.service; then
	echo "✅ Sunshine service is active."
	echo "Web UI: https://sunshine.mattdies.com (or https://10.144.88.102:47990)"
else
	echo "❌ Sunshine service failed to start. Check: journalctl --user -u sunshine -n 30"
	exit 1
fi

if [ "$1" = "--steam" ] || [ "$1" = "-s" ]; then
	"${SCRIPT_DIR}/start_steam.sh"
fi
