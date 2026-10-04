Below is a **Ubuntu Server–equivalent version** of your friend’s Fedora instructions. I’ll keep the structure the same, note where things differ, and point out Ubuntu-specific gotchas. This is written assuming **Ubuntu Server 22.04 or 24.04 LTS**, headless, with NVIDIA GPU (which matches your usual setup style).

---

# Sunshine Setup (Ubuntu)

## Operating System

* Ubuntu Server 22.04 LTS or 24.04 LTS

  * Minimal installation is fine
  * Headless (no desktop environment by default)

---

## NVIDIA Driver Installation (Ubuntu)

> **Secure Boot**: Same warning applies. Proprietary NVIDIA drivers + Secure Boot can be painful. Disable Secure Boot unless you *really* want to manage MOK signing.

### Verify GPU detection

```bash
lspci | grep -E "VGA|3D"
```

### Install NVIDIA drivers

Ubuntu handles this via `apt` instead of RPM Fusion.

```bash
sudo apt update
sudo apt install -y ubuntu-drivers-common
```

List recommended driver:

```bash
ubuntu-drivers devices
```

Install the recommended proprietary driver (example uses `nvidia-driver-535`, adjust if different):

```bash
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
```

Reboot after installation:

```bash
sudo reboot
```

After reboot, verify:

```bash
modinfo -F version nvidia
nvidia-smi
```

Both should succeed and correctly detect your GPU.

---

## Sunshine Setup

> Ubuntu follows the same **headless Sunshine over SSH** approach.

Reference guide still applies:
[https://app.lizardbyte.dev/2023-09-14-remote-ssh-headless-sunshine-setup/](https://app.lizardbyte.dev/2023-09-14-remote-ssh-headless-sunshine-setup/)

---

## Setup SSH (Ubuntu)

OpenSSH server is usually installed by default, but verify:

```bash
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

### Update SSH config

Edit:

```bash
sudo nano /etc/ssh/sshd_config
```

Ensure this line is **uncommented**:

```text
UsePAM no
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

---

## Virtual Display Setup (Ubuntu)

### Identify connected display

Same as Fedora:

```bash
ls /sys/class/drm
cat /sys/class/drm/<candidate>/status
```

Look for `connected`.

---

### Install X11 + lightweight WM

Ubuntu package names differ slightly:

```bash
sudo apt install -y \
  xserver-xorg \
  xinit \
  xterm \
  openbox \
  x11-xserver-utils
```

---

### Create `/etc/X11/xorg.conf`

```bash
sudo nano /etc/X11/xorg.conf
```

Use the same content (replace `<your_connected_monitor_here>`):

```conf
Section "ServerLayout"
    Identifier "TwinLayout"
    Screen 0 "metaScreen" 0 0
EndSection

Section "Monitor"
    Identifier "Monitor0"
    Option "Enable" "true"
EndSection

Section "Device"
    Identifier "Card0"
    Driver "nvidia"
    VendorName "NVIDIA Corporation"
    Option "MetaModes" "1920x1080"
    Option "ConnectedMonitor" "<your_connected_monitor_here>"
    Option "ModeValidation" "NoDFPNativeResolutionCheck,NoVirtualSizeCheck,NoMaxPClkCheck,NoHorizSyncCheck,NoVertRefreshCheck,NoWidthAlignmentCheck"
EndSection

Section "Screen"
    Identifier "metaScreen"
    Device "Card0"
    Monitor "Monitor0"
    DefaultDepth 24
    Option "TwinView" "True"
    SubSection "Display"
        Modes "1920x1080"
    EndSubSection
EndSection
```

---

## Permissions (Ubuntu)

### uinput ownership workaround

Same workaround applies:

```bash
echo "chown $(id -un):$(id -gn) /dev/uinput" > ~/sunshine-setup.sh
chmod +x ~/sunshine-setup.sh
```

Add yourself to the `input` group:

```bash
sudo usermod -aG input $USER
```

Log out and back in (or reboot) for group changes to apply.

---

### Passwordless sudo for setup script

Create a sudoers file:

```bash
sudo nano /etc/sudoers.d/$USER
```

Add:

```text
${USER} ALL=(ALL:ALL) ALL, NOPASSWD: /home/${USER}/sunshine-setup.sh
```

---

### (Optional) Force Ethernet only

Same command works on Ubuntu:

```bash
echo "rfkill block $(rfkill list | grep 'Wireless LAN' | sed 's/^\([[:digit:]]\).*/\1/')" >> ~/sunshine-setup.sh
```

---

## Launch Script (Ubuntu)

Create `~/sunshine.sh`:

```bash
nano ~/sunshine.sh
chmod +x ~/sunshine.sh
```

```bash
#!/bin/bash
set -e

export DISPLAY=:0

LOGFILE="$HOME/startx.log"
SUNSHINE_LOGFILE="$HOME/sunshine.log"

# Start X if not running
if ! pgrep -x Xorg > /dev/null; then
    echo "Starting X Server"
    startx > "$LOGFILE" 2>&1 &
    sleep 2
fi

# Start Sunshine if not running
if ! pgrep -x sunshine > /dev/null; then
    sudo ~/sunshine-setup.sh
    echo "Starting Sunshine"
    sunshine > "$SUNSHINE_LOGFILE" 2>&1 &
    sleep 2
fi

steam &> /dev/null &
```

---

## Allow Xorg over SSH (Ubuntu)

Edit:

```bash
sudo nano /etc/X11/Xwrapper.config
```

Set:

```text
allowed_users=anybody
```

---

## Install Sunshine & Steam (Ubuntu)

### Sunshine (official APT repo)

```bash
sudo apt install -y curl gpg
curl -fsSL https://repo.lizardbyte.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/lizardbyte.gpg
echo "deb [signed-by=/usr/share/keyrings/lizardbyte.gpg] https://repo.lizardbyte.dev/ stable main" | sudo tee /etc/apt/sources.list.d/lizardbyte.list

sudo apt update
sudo apt install -y sunshine
```

### Steam (headless-friendly)

```bash
sudo apt install -y steam
```

### pgrep (usually installed, but just in case)

```bash
sudo apt install -y procps
```

---

## `.xinitrc` (same as Fedora)

Create:

```bash
nano ~/.xinitrc
```

```bash
xset off
xset -dpms
xset s noblank
xsetroot -solid black

export XCURSOR_SIZE=10

exec openbox-session
```

---

## Testing (Ubuntu)

With a monitor attached:

```bash
ssh user@server
~/sunshine.sh
```

Expected output:

```text
Starting X Server
Starting Sunshine
Sunshine started successfully
```

Kill processes:

```bash
pkill X
pkill sunshine
```

Disconnect the monitor and repeat. Output should be identical.

---

## Firewall (Ubuntu – UFW)

Ubuntu uses **ufw**, not firewalld.

```bash
sudo ufw allow 47984:47990/tcp
sudo ufw allow 47998:48000/udp
sudo ufw allow 48010/tcp
sudo ufw allow 48010/udp
sudo ufw reload
```

Restart Sunshine:

```bash
pkill sunshine
~/sunshine.sh
```

---

## Moonlight (Client Setup)

Same as Fedora:

1. Install Moonlight on client
2. Manually add server IP
3. Visit:

   ```
   http://<server-ip>:47990
   ```
4. Create Sunshine admin account
5. Enter PIN from Moonlight
6. Launch **Desktop**

You should see:

* Openbox desktop
* Steam auto-launched

---

## Optional Improvements

Highly recommended:

* Dynamic resolution & refresh rate:
  [https://docs.lizardbyte.dev/projects/sunshine/master/md_docs_2app__examples.html#changing-resolution-and-refresh-rate](https://docs.lizardbyte.dev/projects/sunshine/master/md_docs_2app__examples.html#changing-resolution-and-refresh-rate)

Audio hiccups are common; fully exiting Moonlight and reconnecting usually fixes it.

---

If you want, I can:

* Convert this into a **single Ubuntu checklist**
* Turn it into a **systemd service** (no manual script running)
* Adapt it for **Wayland-free NVIDIA setups only**
* Harden it for **LAN-only streaming** (iptables / ufw rules)

Just tell me.
