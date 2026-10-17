#!/bin/bash
set -e

# Device permissions & wireless state
chown matthewkdies:matthewkdies /dev/uinput 2>/dev/null || true
rfkill block 1 2>/dev/null || true

# Ensure autologin group exists and user is a member
if ! getent group autologin >/dev/null; then
	groupadd -r autologin
fi
usermod -aG autologin matthewkdies

# Configure LightDM for autologin into Xfce on boot
mkdir -p /etc/lightdm/lightdm.conf.d
cat >/etc/lightdm/lightdm.conf.d/50-autologin.conf <<'EOF'
[Seat:*]
autologin-user=matthewkdies
autologin-user-timeout=0
user-session=xfce
xserver-command=X -s 0 -dpms -core
EOF

# Stop and disable headless-xorg service
if systemctl is-active --quiet headless-xorg.service; then
	systemctl stop headless-xorg.service || true
fi
if systemctl is-enabled --quiet headless-xorg.service 2>/dev/null; then
	systemctl disable headless-xorg.service || true
fi

# Set LightDM as default display manager and enable
echo "/usr/sbin/lightdm" >/etc/X11/default-display-manager
systemctl disable gdm3.service 2>/dev/null || true
systemctl enable --force lightdm.service
systemctl restart lightdm.service

echo "LightDM headed desktop setup complete."
