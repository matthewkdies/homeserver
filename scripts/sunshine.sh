#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
stop)
	"${SCRIPT_DIR}/stop_sunshine.sh"
	;;
status)
	if systemctl --user is-active --quiet sunshine.service; then
		echo "✅ Sunshine service is running (systemd --user: active)."
	elif pgrep -x sunshine >/dev/null; then
		echo "✅ Sunshine process is running (PID: $(pgrep -x sunshine))."
	else
		echo "❌ Sunshine is not running."
	fi
	if systemctl is-active --quiet lightdm.service 2>/dev/null; then
		echo "✅ LightDM display manager is active."
	else
		echo "❌ LightDM display manager is not active."
	fi
	if pgrep -x Xorg >/dev/null; then
		echo "✅ Xorg server is running (PID: $(pgrep -x Xorg))."
	else
		echo "❌ Xorg server is not running."
	fi
	if pgrep -x xfwm4 >/dev/null; then
		echo "✅ Xfce desktop is active (WM PID: $(pgrep -x xfwm4))."
	else
		echo "❌ Xfce window manager is not running."
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
restart)
	"${SCRIPT_DIR}/stop_sunshine.sh"
	sleep 1
	"${SCRIPT_DIR}/start_sunshine.sh" "$2"
	;;
steam)
	"${SCRIPT_DIR}/start_steam.sh"
	;;
cfbr | ncaa)
	"${SCRIPT_DIR}/start_cfbr.sh"
	;;
update)
	"${SCRIPT_DIR}/update_sunshine.sh"
	;;
setup)
	sudo "${SCRIPT_DIR}/sunshine-setup.sh"
	;;
*)
	echo "Usage: $0 {start [--steam]|stop|restart [--steam]|status|steam|cfbr|update|setup}"
	exit 1
	;;
esac
