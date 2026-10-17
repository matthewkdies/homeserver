#!/bin/bash
set -e

stopped_any=false

if systemctl --user is-active --quiet sunshine.service; then
	systemctl --user stop sunshine.service
	echo "Sunshine service stopped."
	stopped_any=true
elif pgrep -x "sunshine" >/dev/null; then
	pkill -x sunshine
	echo "Sunshine process stopped."
	stopped_any=true
fi

# Stop Steam if running
if pgrep -x "steam" >/dev/null || flatpak ps --columns=application 2>/dev/null | grep -qx "com.valvesoftware.Steam"; then
	echo "Stopping Steam..."
	flatpak kill com.valvesoftware.Steam 2>/dev/null || true
	pkill -x steam 2>/dev/null || true
	stopped_any=true
fi

if [ "$stopped_any" = false ]; then
	echo "Sunshine is not running."
fi
