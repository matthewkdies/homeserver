#!/bin/bash
set -e

RPCS3_BIN="/home/matthewkdies/Desktop/rpcs3/RPCS3.AppImage"
GAME_EBOOT="/home/matthewkdies/.config/rpcs3/dev_hdd0/disc/BLUS31159-[NCAA Football 14]/PS3_GAME/USRDIR/EBOOT.BIN"

if [ ! -f "$GAME_EBOOT" ]; then
	echo "Error: Game EBOOT not found at $GAME_EBOOT"
	exit 1
fi

export DISPLAY="${DISPLAY:-:0}"

# Ensure no stale RPCS3 instance is holding the single-instance lock
pkill -9 -f "RPCS3\.AppImage|AppRun\.wrapped" 2>/dev/null || true

# Fix SDL3 evdev mapping for Sunshine's virtual Bluetooth DualSense (054c:0ce6 v8111)
export SDL_GAMECONTROLLERCONFIG="050000004c050000e60c000011810000,PS5 Controller,a:b0,b:b1,back:b8,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,dpup:h0.1,guide:b10,leftshoulder:b4,leftstick:b11,lefttrigger:a2,leftx:a0,lefty:a1,rightshoulder:b5,rightstick:b12,righttrigger:a5,rightx:a3,righty:a4,start:b9,x:b3,y:b2,platform:Linux,"

# Wait briefly for Sunshine to initialize the virtual controller on stream start
for _ in $(seq 1 15); do
	if grep -q "Wireless Controller\|Microsoft X-Box" /proc/bus/input/devices 2>/dev/null; then
		break
	fi
	sleep 0.2
done

# Launch RPCS3 directly with the game
exec "$RPCS3_BIN" "$GAME_EBOOT"
