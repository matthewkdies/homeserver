#!/bin/bash
set -e

RPCS3_BIN="/home/matthewkdies/Desktop/rpcs3/RPCS3.AppImage"
GAME_EBOOT="/home/matthewkdies/.config/rpcs3/dev_hdd0/disc/BLUS31159-[NCAA Football 14]/PS3_GAME/USRDIR/EBOOT.BIN"

if [ ! -f "$GAME_EBOOT" ]; then
	echo "Error: Game EBOOT not found at $GAME_EBOOT"
	exit 1
fi

export DISPLAY="${DISPLAY:-:0}"

# Wait briefly for Sunshine to initialize the virtual controller on stream start
for _ in $(seq 1 15); do
	if grep -q "Wireless Controller\|Microsoft X-Box" /proc/bus/input/devices 2>/dev/null; then
		break
	fi
	sleep 0.2
done

# Launch RPCS3 directly with the game
exec "$RPCS3_BIN" "$GAME_EBOOT"
