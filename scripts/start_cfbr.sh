#!/bin/bash
set -e

RPCS3_BIN="/home/matthewkdies/Desktop/rpcs3/RPCS3.AppImage"
GAME_EBOOT="/home/matthewkdies/.config/rpcs3/dev_hdd0/disc/BLUS31159-[NCAA Football 14]/PS3_GAME/USRDIR/EBOOT.BIN"

if [ ! -f "$GAME_EBOOT" ]; then
	echo "Error: Game EBOOT not found at $GAME_EBOOT"
	exit 1
fi

export DISPLAY="${DISPLAY:-:0}"

# Launch RPCS3 directly with the game
exec "$RPCS3_BIN" "$GAME_EBOOT"
