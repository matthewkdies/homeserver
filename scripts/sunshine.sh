#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
stop)
	"${SCRIPT_DIR}/stop_sunshine.sh"
	;;
status)
	if pgrep -x sunshine >/dev/null; then
		echo "✅ Sunshine is running (PID: $(pgrep -x sunshine))."
	else
		echo "❌ Sunshine is not running."
	fi
	if pgrep -x openbox >/dev/null; then
		echo "✅ Openbox window manager is running (PID: $(pgrep -x openbox))."
	else
		echo "❌ Openbox is not running."
	fi
	if pgrep -x Xorg >/dev/null; then
		echo "✅ Xorg server is running (PID: $(pgrep -x Xorg))."
	else
		echo "❌ Xorg server is not running."
	fi
	if pgrep -x steam >/dev/null; then
		echo "✅ Steam is running (PID: $(pgrep -x steam | head -n 1))."
	elif flatpak ps --columns=application 2>/dev/null | grep -qx "com.valvesoftware.Steam"; then
		flatpak_pid=$(flatpak ps --columns=application,pid 2>/dev/null | awk '$1 == "com.valvesoftware.Steam" {print $2}' | head -n 1)
		echo "✅ Steam is running (Flatpak PID: ${flatpak_pid})."
	else
		echo "❌ Steam is not running."
	fi
	;;
start | "")
	"${SCRIPT_DIR}/start_sunshine.sh" "$2"
	;;
steam)
	"${SCRIPT_DIR}/start_steam.sh"
	;;
restart)
	"${SCRIPT_DIR}/stop_sunshine.sh"
	sleep 1
	"${SCRIPT_DIR}/start_sunshine.sh" "$2"
	;;
update)
	"${SCRIPT_DIR}/update_sunshine.sh"
	;;
*)
	echo "Usage: $0 {start [--steam]|stop|restart [--steam]|status|steam|update}"
	exit 1
	;;
esac
