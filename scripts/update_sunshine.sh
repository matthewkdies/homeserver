#!/usr/bin/bash

# --------------------------------------------------------------------------------------
# https://docs.lizardbyte.dev/projects/sunshine/latest/md_docs_2getting__started.html#install-2
# https://docs.lizardbyte.dev/projects/sunshine/latest/md_docs_2getting__started.html#initial-setup

# --------------------------------------------------------------------------------------

set -e

# Fetch latest release info from GitHub API
echo "Fetching latest Sunshine release info..."
latest_json=$(curl -s https://api.github.com/repos/LizardByte/Sunshine/releases/latest)

# Identify the asset matching ubuntu-24.04-amd64.deb (or generic amd64)
asset_url=$(echo "$latest_json" \
  | jq -r '.assets[]
      | select(.name | test("ubuntu-24\\.04-amd64\\.deb$"))
      | .browser_download_url')

if [[ -z "$asset_url" || "$asset_url" == "null" ]]; then
  echo "⚠️ Cannot find the ubuntu‑24.04‑amd64 deb in the latest release."
  echo "Available assets:"
  echo "$latest_json" | jq -r '.assets[].name'
  exit 1
fi

echo "Found asset: $asset_url"
filename=${asset_url##*/}

# Download it
echo "Downloading $filename ..."
curl -L "$asset_url" -o "/tmp/$filename"

# Install via apt to handle dependencies
echo "Installing Sunshine package..."
sudo apt update
sudo apt install -y "/tmp/$filename"

echo "✅ Installed Sunshine successfully!"

# Cleanup
rm "/tmp/$filename"
echo "Done installing. Restart or start sunshine to use the latest version."
