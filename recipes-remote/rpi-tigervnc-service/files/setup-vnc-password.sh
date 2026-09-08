#!/bin/sh
# ==============================================================================
# Helper to set TigerVNC password and enforce authentication
# ==============================================================================
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <new_password>"
    echo "Example: $0 secret123"
    exit 1
fi

PASSWORD="$1"

mkdir -p /root/.vnc
echo "$PASSWORD" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd

# Update systemd unit to enforce VncAuth instead of None
if [ -f /lib/systemd/system/tigervnc.service ]; then
    sed -i 's/-SecurityTypes None/-SecurityTypes VncAuth -PasswordFile \/root\/.vnc\/passwd/' /lib/systemd/system/tigervnc.service
    systemctl daemon-reload
    systemctl restart tigervnc.service
    echo "[VNC] Password set successfully and TigerVNC service restarted with authentication enabled."
fi
