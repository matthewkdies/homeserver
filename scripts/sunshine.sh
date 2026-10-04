#!/bin/bash
set -e

export DISPLAY=:0

is_running() {
    pgrep -x "$1" >/dev/null 2>&1
}

start_bg() {
    local name="$1"
    shift

    echo "Starting $name..."
    "$@" >/dev/null 2>&1 &
}

# -----------------------------
# Ensure X server is running
# -----------------------------
if is_running Xorg; then
    echo "X server already running"
else
    echo "Starting X server..."
    startx >/dev/null 2>&1 &

    # Give it a moment to come up
    sleep 2

    if is_running Xorg; then
        echo "X server started successfully"
    else
        echo "ERROR: X server failed to start"
        exit 1
    fi
fi

# -----------------------------
# Start Sunshine
# -----------------------------
if is_running sunshine; then
    echo "Sunshine already running"
else
    echo "Running Sunshine setup..."
    sudo "${SCRIPTS_DIR}/sunshine-setup.sh"

    start_bg sunshine sunshine
    #sunshine &

    sleep 1
    if is_running sunshine; then
        echo "Sunshine started successfully"
    else
        echo "ERROR: Sunshine failed to start"
        exit 1
    fi
fi

# -----------------------------
# Optional autostart apps
# -----------------------------
if ! is_running steam; then
    start_bg steam steam
    sleep 1
    if is_running steam; then
        echo "Steam started successfully"
    else
        echo "ERROR: Steam failed to start"
        exit 1
    fi
fi

# firefox &> /dev/null &
# kdeconnect-app &> /dev/null &



#!/usr/bin/env bash

# Ensure the script exits if any command fails unexpectedly
set -e

echo "Starting virtual Xorg server on :0..."
# Launch Xorg in the background. Requires sudo.
sudo Xorg :0 -noreset -sharevts +extension GLX +extension RENDER -logfile /tmp/xorg.log &

# Capture the Xorg PID so we can clean it up later if needed
XORG_PID=$!

# Give Xorg a moment to initialize the virtual display context
sleep 1.5

echo "Launching Sunshine..."

# Execute Sunshine. Using 'exec' hands control over to Sunshine completely.
exec sunshine
