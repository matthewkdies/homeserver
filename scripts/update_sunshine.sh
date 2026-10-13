#!/bin/bash
# --------------------------------------------------------------------------------------
# Sunshine & Streaming Dependencies Updater
# --------------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure sudo is used if not running as root
if [ "$EUID" -ne 0 ]; then
	SUDO="sudo"
else
	SUDO=""
fi

echo "=========================================="
echo " 1. Checking Sunshine Updates"
echo "=========================================="

source /etc/os-release 2>/dev/null || VERSION_ID="26.04"

# Get current version
installed_version=$(dpkg -s sunshine 2>/dev/null | grep -i '^version:' | awk '{print $2}' || echo "none")
echo "Currently installed Sunshine version: $installed_version"

# Fetch latest release info from GitHub API
echo "Fetching latest Sunshine release info from GitHub..."
latest_json=$(curl -s https://api.github.com/repos/LizardByte/Sunshine/releases/latest)
latest_tag=$(echo "$latest_json" | jq -r '.tag_name // empty')

if [[ -z "$latest_tag" || "$latest_tag" == "null" ]]; then
	echo "⚠️ Failed to fetch release info from GitHub API."
	exit 1
fi
echo "Latest available Sunshine release: $latest_tag"

# Match Ubuntu version specifically first, then generic ubuntu amd64 deb
asset_url=$(echo "$latest_json" | jq -r --arg ver "$VERSION_ID" '
	.assets[]
	| select(.name | test("ubuntu" + $ver + ".*amd64\\.deb$"))
	| .browser_download_url' | head -n 1)

if [[ -z "$asset_url" || "$asset_url" == "null" ]]; then
	asset_url=$(echo "$latest_json" | jq -r '
		.assets[]
		| select(.name | test("ubuntu.*amd64\\.deb$"))
		| .browser_download_url' | head -n 1)
fi

if [[ -z "$asset_url" || "$asset_url" == "null" ]]; then
	echo "⚠️ Cannot find an appropriate Ubuntu amd64 .deb in release $latest_tag."
	echo "Available assets:"
	echo "$latest_json" | jq -r '.assets[].name'
	exit 1
fi

filename=$(echo "$asset_url" | awk -F/ '{print $NF}' | sed 's/%2B/+/g')
echo "Found release asset: $filename"

was_running=false
if pgrep -x "sunshine" >/dev/null; then
	was_running=true
fi

clean_tag="${latest_tag#v}"
if [[ "$installed_version" == *"$clean_tag"* ]]; then
	echo "✅ Sunshine is already up-to-date ($installed_version)."
else
	echo "Downloading $filename..."
	curl -L "$asset_url" -o "/tmp/$filename"

	echo "Installing Sunshine package via apt..."
	$SUDO apt-get update
	$SUDO apt-get install -y "/tmp/$filename"

	rm -f "/tmp/$filename"
	echo "✅ Sunshine upgraded successfully!"
fi

echo ""
echo "=========================================="
echo " 2. Verifying Sunshine Capabilities"
echo "=========================================="
sunshine_bin=$(which sunshine 2>/dev/null || echo "/usr/bin/sunshine")
current_caps=$(getcap "$sunshine_bin" 2>/dev/null || echo "")

if [[ "$current_caps" == *"cap_sys_admin"* ]]; then
	echo "✅ Capabilities verified: $current_caps"
else
	echo "Setting cap_sys_admin,cap_sys_nice capabilities on $sunshine_bin..."
	$SUDO setcap cap_sys_admin,cap_sys_nice+p "$sunshine_bin"
	echo "✅ Capabilities set."
fi

echo ""
echo "=========================================="
echo " 3. Verifying GPU & Flatpak Compatibility"
echo "=========================================="
if command -v nvidia-smi >/dev/null 2>&1; then
	driver_ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n 1 | tr -d ' ')
	if [[ -n "$driver_ver" ]]; then
		driver_pkg="nvidia-${driver_ver//./-}"
		echo "Host NVIDIA driver detected: $driver_ver ($driver_pkg)"

		if command -v flatpak >/dev/null 2>&1; then
			echo "Checking Flatpak NVIDIA runtime..."
			if ! flatpak list | grep -q "$driver_pkg"; then
				echo "Installing matching Flatpak runtime $driver_pkg (64-bit and 32-bit)..."
				flatpak --user install -y flathub "org.freedesktop.Platform.GL.$driver_pkg" "org.freedesktop.Platform.GL32.$driver_pkg" || true
			else
				echo "✅ Flatpak NVIDIA GL runtimes match host driver ($driver_pkg)."
			fi

			echo "Updating user Flatpak runtimes and applications..."
			flatpak --user update -y || true
		fi
	fi
else
	echo "No NVIDIA GPU detected; skipping NVIDIA Flatpak runtime check."
fi

echo ""
echo "=========================================="
echo " 4. Verifying Input Device Permissions"
echo "=========================================="
if [ -w /dev/uinput ]; then
	echo "✅ /dev/uinput is writable by current user."
else
	echo "⚠️ /dev/uinput is not writable by $(whoami). Ensure user is in 'input' group."
fi

if [ -w /dev/uhid ]; then
	echo "✅ /dev/uhid is writable (DualSense/DS5 controller emulation enabled)."
else
	echo "ℹ️  /dev/uhid is not writable. DS5 controller emulation may require a udev rule."
fi

echo ""
if [ "$was_running" = true ]; then
	echo "Restarting Sunshine..."
	"${SCRIPT_DIR}/stop_sunshine.sh"
	sleep 1
	"${SCRIPT_DIR}/start_sunshine.sh"
	echo "✅ Sunshine restarted with updated version."
fi

echo ""
echo "🎉 Update & dependency check completed!"
