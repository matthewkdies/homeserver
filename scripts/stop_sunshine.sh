#!/bin/bash

stopped_any=false

if pgrep -x "sunshine" >/dev/null; then
	pkill -x sunshine
	echo "Sunshine stopped."
	stopped_any=true
else
	echo "Sunshine is not running."
fi

# Stop Steam if running
if pgrep -f "com.valvesoftware.Steam" >/dev/null || pgrep -x "steam" >/dev/null; then
	echo "Stopping Steam..."
	flatpak kill com.valvesoftware.Steam 2>/dev/null || true
	pkill -x steam 2>/dev/null || true
	stopped_any=true
fi

# Stop Openbox if running
if pgrep -x "openbox" >/dev/null; then
	echo "Stopping Openbox..."
	pkill -x openbox 2>/dev/null || true
	stopped_any=true
fi

if [ "$stopped_any" = true ]; then
	echo "All streaming processes stopped."
fi
