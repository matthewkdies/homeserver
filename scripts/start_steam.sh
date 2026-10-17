#!/bin/bash
set -e

export PATH="$HOME/.local/bin:$PATH"
export DISPLAY=:0

# Ensure X server is running on :0
if ! pgrep -x "Xorg" >/dev/null; then
	echo "X server is not running on :0. Please ensure headless-xorg service is running."
	exit 1
fi

# Set default 1080p resolution on virtual display
xrandr --output HDMI-0 --mode 1920x1080 2>/dev/null || true

# Ensure Openbox window manager is running on :0
if ! pgrep -x "openbox" >/dev/null; then
	echo "Starting Openbox window manager on :0..."
	setsid openbox --sm-disable >/dev/null 2>&1 &
	sleep 1
fi

# Ensure Picom compositor is running on :0
if ! pgrep -x "picom" >/dev/null; then
	echo "Starting Picom compositor on :0..."
	setsid picom -b --backend xrender >/dev/null 2>&1 &
	sleep 1
fi

# Check if Steam is already running
if pgrep -x "steam" >/dev/null || flatpak ps --columns=application 2>/dev/null | grep -qx "com.valvesoftware.Steam"; then
	echo "Steam is already running."
	exit 0
fi

LOG_DIR="${DOCUMENTS_DIR:-$HOME/Documents}/sunshine"
mkdir -p "$LOG_DIR"
LOGFILE_PATH="${LOG_DIR}/steam.log"

echo "Starting Steam..."
export PULSE_LATENCY_MSEC="${PULSE_LATENCY_MSEC:-60}"
setsid flatpak run --user com.valvesoftware.Steam -no-sandbox -forcedesktopscaling "${STEAM_SCALING:-1.5}" >>"${LOGFILE_PATH}" 2>&1 &
sleep 2

if pgrep -x "steam" >/dev/null || flatpak ps --columns=application 2>/dev/null | grep -qx "com.valvesoftware.Steam"; then
	echo "Steam started successfully."
	echo "Logs: ${LOGFILE_PATH}"
else
	echo "ERROR: Steam failed to start. Check logs at ${LOGFILE_PATH}."
	exit 1
fi
