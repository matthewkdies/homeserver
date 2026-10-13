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

# Check if Sunshine is already running
if pgrep -x "sunshine" >/dev/null; then
	echo "Sunshine is already running."
	exit 0
fi

LOG_DIR="${DOCUMENTS_DIR:-$HOME/Documents}/sunshine"
mkdir -p "$LOG_DIR"
LOGFILE_PATH="${LOG_DIR}/sunshine.log"

echo "Starting Sunshine..."
setsid sunshine >>"${LOGFILE_PATH}" 2>&1 &
sleep 2

if pgrep -x "sunshine" >/dev/null; then
	echo "Sunshine started successfully (PID: $(pgrep -x sunshine))."
	echo "Logs: ${LOGFILE_PATH}"
	echo "Web UI: https://sunshine.mattdies.com (or https://10.144.88.102:47990)"
else
	echo "ERROR: Sunshine failed to start. Check logs at ${LOGFILE_PATH}."
	exit 1
fi
