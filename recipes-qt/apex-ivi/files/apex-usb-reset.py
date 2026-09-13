#!/usr/bin/env python3
"""
apex-usb-reset.py
Resets any connected Google Android Open Accessory (18d1:2d00 / 18d1:2d01)
or Android mobile device port via USBDEVFS_RESET ioctl.
This allows clean re-handshake and reconnect after software restarts or flashes
without having to physically unplug and replug the USB cable.
"""
import os
import glob
import fcntl
import sys
import time

USBDEVFS_RESET = 21780 # 0x5514

def reset_aoa_devices():
    resetted = 0
    # First search specifically for Google AOA (18d1) devices
    for dev_path in sorted(glob.glob("/sys/bus/usb/devices/*")):
        vendor_file = os.path.join(dev_path, "idVendor")
        if os.path.exists(vendor_file):
            try:
                with open(vendor_file, "r") as f:
                    vid = f.read().strip().lower()
                if vid == "18d1":
                    busnum_file = os.path.join(dev_path, "busnum")
                    devnum_file = os.path.join(dev_path, "devnum")
                    if os.path.exists(busnum_file) and os.path.exists(devnum_file):
                        b = open(busnum_file).read().strip().zfill(3)
                        d = open(devnum_file).read().strip().zfill(3)
                        node = f"/dev/bus/usb/{b}/{d}"
                        if os.path.exists(node):
                            print(f"[apex-usb-reset] Resetting orphaned AOA device at {node} ({dev_path})...")
                            with open(node, "wb") as dev_f:
                                fcntl.ioctl(dev_f, USBDEVFS_RESET)
                            resetted += 1
            except Exception as e:
                print(f"[apex-usb-reset] Warning checking {dev_path}: {e}")

    # If no 18d1 was found, check if there's any non-hub USB device that might be an Android phone
    # needing a bus reset
    if resetted == 0:
        print("[apex-usb-reset] No 18d1 AOA devices found needing reset.")
    else:
        print(f"[apex-usb-reset] Successfully reset {resetted} AOA device(s).")

if __name__ == "__main__":
    reset_aoa_devices()
