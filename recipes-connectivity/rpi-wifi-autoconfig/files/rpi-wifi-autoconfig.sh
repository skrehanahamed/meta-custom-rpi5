#!/bin/sh
# ==============================================================================
# Auto-WiFi Boot Script for Raspberry Pi 5
# Allows dropping wpa_supplicant.conf directly onto the FAT boot partition!
# ==============================================================================

TARGET_CONF="/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
BOOT_CONF=""

# Search common Raspberry Pi boot mountpoints
for loc in /boot/firmware/wpa_supplicant.conf /boot/wpa_supplicant.conf /media/boot/wpa_supplicant.conf; do
    if [ -f "$loc" ]; then
        BOOT_CONF="$loc"
        break
    fi
done

if [ -n "$BOOT_CONF" ]; then
    echo "[Auto-WiFi] Found user Wi-Fi configuration at $BOOT_CONF. Applying..."
    cp "$BOOT_CONF" "$TARGET_CONF"
    chmod 600 "$TARGET_CONF"
fi

# Unblock radio devices if blocked by rfkill
if command -v rfkill >/dev/null 2>&1; then
    rfkill unblock wifi || true
    rfkill unblock all || true
fi

# Ensure wlan0 interface is up
ip link set wlan0 up 2>/dev/null || true

echo "[Auto-WiFi] Initialization completed."
