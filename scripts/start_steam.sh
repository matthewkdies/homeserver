#!/bin/bash
set -e

export DISPLAY=:0

# Ensure X server is running on :0
if ! pgrep -x "Xorg" >/dev/null; then
	echo "X server is not running on :0. Please ensure headless-xorg service is running."
	exit 1
fi

# Ensure Openbox window manager is running on :0
if ! pgrep -x "openbox" >/dev/null; then
	echo "Starting Openbox window manager on :0..."
	setsid openbox --sm-disable >/dev/null 2>&1 &
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
setsid flatpak run --user com.valvesoftware.Steam -no-sandbox >>"${LOGFILE_PATH}" 2>&1 &
sleep 2

if pgrep -x "steam" >/dev/null || flatpak ps --columns=application 2>/dev/null | grep -qx "com.valvesoftware.Steam"; then
	echo "Steam started successfully."
	echo "Logs: ${LOGFILE_PATH}"
else
	echo "ERROR: Steam failed to start. Check logs at ${LOGFILE_PATH}."
	exit 1
fi
