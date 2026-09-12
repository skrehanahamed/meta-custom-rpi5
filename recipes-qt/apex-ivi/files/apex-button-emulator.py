#!/usr/bin/env python3
"""
============================================================================
Project: Apex IVI - Automotive In-Vehicle Infotainment System
Component: Physical Button, Vehicle Controls & Bluetooth Device Emulator Form
Author: Sk Rehan Ahamed
Description:
  Automotive hardware button emulator, vehicle dynamics controller, and
  Bluetooth device manager. Allows controlling physical steering wheel buttons,
  transmission shifter, master sound volume, and pairing/connecting new or
  disconnected Bluetooth input devices (mice, keyboards, controllers).
============================================================================
"""

import http.server
import socketserver
import json
import os
import re
import fcntl
import struct
import time
import threading
import subprocess

PORT = 8080

# Linux input event constants
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

EV_SYN = 0x00
EV_KEY = 0x01
SYN_REPORT = 0

KEY_MAP = {
    # Steering Wheel Controls
    "vol_up": 103,       # KEY_UP
    "vol_down": 108,     # KEY_DOWN
    "play_pause": 10,    # KEY_9 (Toggles Radio playback in Apex IVI)
    "mute": 10,          # KEY_9
    "power": 11,         # KEY_0 (Media power off / stop)
    "media_off": 11,     # KEY_0
    "reverse": 19,       # KEY_R (Toggles Reverse Gear / DRVM Camera)
    "reverse_gear": 19,
    
    # Navigation / Direct Keys
    "key_up": 103,
    "key_down": 108,
    "key_9": 10,
    "key_0": 11,
    "key_r": 19,
}

class UInputKeyboard:
    def __init__(self):
        self.fd = None
        self.lock = threading.Lock()
        self.init_device()

    def init_device(self):
        try:
            self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
            fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
            for k in range(1, 256):
                try:
                    fcntl.ioctl(self.fd, UI_SET_KEYBIT, k)
                except Exception:
                    pass
            name = b"Apex_Remote_Keyboard".ljust(80, b"\x00")
            # 80sHHHHi + 1024 bytes padding for abs
            data = struct.pack("80sHHHHi", name, 0x03, 0x1234, 0x5678, 1, 0) + (b"\x00" * 1024)
            os.write(self.fd, data)
            fcntl.ioctl(self.fd, UI_DEV_CREATE)
            print("[UInput] Apex_Remote_Keyboard virtual input device created.")
        except Exception as e:
            print(f"[UInput] ERROR creating virtual input device: {e}")

    def emit_key(self, code, hold_time=0.04):
        with self.lock:
            if not self.fd:
                return False
            try:
                now = time.time()
                s = int(now)
                us = int((now - s) * 1000000)
                # Key Down
                os.write(self.fd, struct.pack("qqHHi", s, us, EV_KEY, code, 1))
                os.write(self.fd, struct.pack("qqHHi", s, us, EV_SYN, SYN_REPORT, 0))
                time.sleep(hold_time)
                # Key Up
                now = time.time()
                s = int(now)
                us = int((now - s) * 1000000)
                os.write(self.fd, struct.pack("qqHHi", s, us, EV_KEY, code, 0))
                os.write(self.fd, struct.pack("qqHHi", s, us, EV_SYN, SYN_REPORT, 0))
                return True
            except Exception as e:
                print(f"[UInput] Failed to emit key {code}: {e}")
                return False

    def close(self):
        if self.fd:
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None

uinput = UInputKeyboard()

# System State Tracker
state = {
    "reverse_active": False,
    "current_gear": "P",
    "volume": 28,
    "media_active": True,
    "last_key": None,
    "last_key_time": None
}

# Bluetooth Manager Functions
is_scanning = False

def sync_alsa_volume(volume):
    try:
        norm = max(0.0, min(1.0, volume / 45.0))
        gain = norm * 0.30 + (norm ** 0.70) * 0.70
        pct = max(0, min(100, int(gain * 100)))
        subprocess.Popen(["amixer", "-c", "1", "sset", "PCM", f"{pct}%"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_bluetooth_devices():
    devices = []
    try:
        res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=4)
        for line in res.stdout.strip().split("\n"):
            if not line or not line.startswith("Device"):
                continue
            parts = line.split(" ", 2)
            if len(parts) >= 2:
                mac = parts[1].strip()
                name = parts[2].strip() if len(parts) > 2 else mac
                
                info_res = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=2)
                info_txt = info_res.stdout
                paired = "Paired: yes" in info_txt
                connected = "Connected: yes" in info_txt
                trusted = "Trusted: yes" in info_txt
                
                icon_match = re.search(r"Icon:\s*([\w\-]+)", info_txt)
                icon = icon_match.group(1) if icon_match else "generic"
                
                bat_match = re.search(r"Battery Percentage:.*\((\d+)\)", info_txt)
                bat = int(bat_match.group(1)) if bat_match else None
                
                devices.append({
                    "mac": mac,
                    "name": name,
                    "paired": paired,
                    "connected": connected,
                    "trusted": trusted,
                    "icon": icon,
                    "battery": bat
                })
    except Exception as e:
        print("[Bluetooth] Error querying devices:", e)
    
    # Sort: Connected first, then Paired, then by name
    devices.sort(key=lambda d: (not d["connected"], not d["paired"], d["name"].lower()))
    return devices

def trigger_bluetooth_scan(duration=8):
    global is_scanning
    if is_scanning:
        return
    def _scan_worker():
        global is_scanning
        is_scanning = True
        try:
            subprocess.run(["bluetoothctl", "--timeout", str(duration), "scan", "on"],
                           capture_output=True, timeout=duration + 3)
        except Exception:
            pass
        finally:
            is_scanning = False
    t = threading.Thread(target=_scan_worker, daemon=True)
    t.start()

def connect_bt_device(mac):
    try:
        subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=4)
        res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True, timeout=8)
        return "Connection successful" in res.stdout or "connected: yes" in res.stdout.lower()
    except Exception as e:
        print(f"[Bluetooth] Error connecting {mac}:", e)
        return False

def pair_and_connect_bt_device(mac):
    try:
        subprocess.run(["bluetoothctl", "pair", mac], capture_output=True, timeout=12)
        subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=4)
        res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True, timeout=8)
        return "Connection successful" in res.stdout or "connected: yes" in res.stdout.lower()
    except Exception as e:
        print(f"[Bluetooth] Error pairing {mac}:", e)
        return False

def disconnect_bt_device(mac):
    try:
        res = subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, text=True, timeout=6)
        return "Successful disconnected" in res.stdout or "disconnected" in res.stdout.lower()
    except Exception as e:
        print(f"[Bluetooth] Error disconnecting {mac}:", e)
        return False

def remove_bt_device(mac):
    try:
        res = subprocess.run(["bluetoothctl", "remove", mac], capture_output=True, text=True, timeout=4)
        return res.returncode == 0
    except Exception as e:
        print(f"[Bluetooth] Error removing {mac}:", e)
        return False

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Apex IVI - Vehicle & Device Controller</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #090c14;
      --card-bg: rgba(18, 24, 38, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #00e5ff;
      --accent-blue: #2979ff;
      --accent-red: #ff1744;
      --accent-green: #00e676;
      --accent-amber: #ff9100;
      --text-main: #f0f4f8;
      --text-dim: #8ba2b5;
      --btn-bg: rgba(28, 36, 56, 0.9);
      --btn-active: rgba(0, 229, 255, 0.2);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }

    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.07) 0%, transparent 60%),
        radial-gradient(circle at 100% 100%, rgba(41, 121, 255, 0.05) 0%, transparent 50%),
        linear-gradient(to bottom, #07090e, #0c111a);
      color: var(--text-main);
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 14px 14px 36px;
    }

    .container {
      width: 100%;
      max-width: 520px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* HEADER */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 18px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      width: 34px;
      height: 34px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      border-radius: 9px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 17px;
      color: #000;
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.4);
    }

    .brand-title {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .brand-sub {
      font-size: 11px;
      color: var(--text-dim);
      letter-spacing: 0.3px;
    }

    .status-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 5px 12px;
      background: rgba(0, 230, 118, 0.1);
      border: 1px solid rgba(0, 230, 118, 0.3);
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      color: var(--accent-green);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      background-color: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.8); }
    }

    /* SECTION CARDS */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 20px;
      padding: 16px 18px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
      position: relative;
      overflow: hidden;
    }

    .card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }

    .card-title {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .card-title svg {
      width: 15px;
      height: 15px;
      fill: var(--accent-cyan);
    }

    /* BUTTON STYLING */
    .btn {
      position: relative;
      background: var(--btn-bg);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 14px;
      color: var(--text-main);
      font-family: inherit;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: all 0.12s cubic-bezier(0.2, 0.9, 0.3, 1);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .btn:active, .btn.active {
      transform: scale(0.96);
      background: var(--btn-active);
      border-color: var(--accent-cyan);
      box-shadow: 0 0 20px rgba(0, 229, 255, 0.3), inset 0 0 12px rgba(0, 229, 255, 0.2);
    }

    .btn-label {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }

    .btn-sub {
      font-size: 10px;
      color: var(--text-dim);
      font-family: 'JetBrains Mono', monospace;
    }

    /* BLUETOOTH RESCUE MANAGER */
    .bt-active-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 14px;
      background: rgba(0, 229, 255, 0.08);
      border: 1px solid rgba(0, 229, 255, 0.25);
      border-radius: 14px;
      margin-bottom: 12px;
    }

    .bt-active-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .bt-device-icon {
      font-size: 22px;
    }

    .bt-active-name {
      font-size: 14px;
      font-weight: 700;
      color: #fff;
    }

    .bt-active-status {
      font-size: 11px;
      color: var(--accent-green);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .bt-toolbar {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
    }

    .bt-scan-btn {
      flex: 1;
      height: 40px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      flex-direction: row;
      gap: 8px;
      background: linear-gradient(135deg, rgba(0, 229, 255, 0.2), rgba(41, 121, 255, 0.2));
      border-color: rgba(0, 229, 255, 0.4);
    }

    .bt-scan-btn.scanning {
      background: rgba(255, 145, 0, 0.2);
      border-color: var(--accent-amber);
      color: var(--accent-amber);
    }

    .bt-device-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 240px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .bt-device-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: rgba(14, 19, 31, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      transition: all 0.15s;
    }

    .bt-device-item:hover {
      border-color: rgba(255, 255, 255, 0.15);
      background: rgba(18, 26, 42, 0.9);
    }

    .bt-device-item.connected {
      border-color: rgba(0, 230, 118, 0.3);
      background: rgba(0, 230, 118, 0.06);
    }

    .bt-dev-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      overflow: hidden;
    }

    .bt-dev-texts {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .bt-dev-title {
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 190px;
    }

    .bt-dev-mac {
      font-size: 10px;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-dim);
    }

    .bt-dev-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .bt-act-btn {
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
      cursor: pointer;
      background: var(--btn-bg);
      color: #fff;
    }

    .bt-act-btn.connect {
      background: rgba(0, 229, 255, 0.18);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }

    .bt-act-btn.disconnect {
      background: rgba(255, 23, 68, 0.15);
      border-color: rgba(255, 23, 68, 0.4);
      color: var(--accent-red);
    }

    .bt-act-btn.remove {
      padding: 6px 8px;
      color: var(--text-dim);
      background: transparent;
      border-color: transparent;
    }

    .bt-manual-connect {
      display: flex;
      gap: 8px;
      margin-top: 10px;
    }

    .bt-input {
      flex: 1;
      height: 36px;
      background: rgba(10, 14, 22, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: #fff;
      padding: 0 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
    }

    .bt-input:focus {
      outline: none;
      border-color: var(--accent-cyan);
    }

    /* VOLUME CONTROLS */
    .volume-hud {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .volume-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .volume-display {
      display: flex;
      align-items: baseline;
      gap: 6px;
    }

    .volume-number {
      font-size: 30px;
      font-weight: 800;
      color: var(--accent-cyan);
      line-height: 1;
    }

    .volume-max {
      font-size: 13px;
      color: var(--text-dim);
      font-weight: 600;
    }

    .volume-bar-container {
      position: relative;
      height: 10px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 5px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .volume-bar-fill {
      height: 100%;
      width: 62%;
      background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
      border-radius: 5px;
      transition: width 0.15s cubic-bezier(0.2, 0.8, 0.25, 1);
      box-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
    }

    .volume-presets {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 6px;
    }

    .preset-btn {
      padding: 6px 0;
      border-radius: 8px;
      font-size: 10px;
      font-weight: 600;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-dim);
    }

    .preset-btn:hover, .preset-btn:active {
      color: #fff;
      background: rgba(0, 229, 255, 0.15);
      border-color: var(--accent-cyan);
    }

    /* STEERING CONTROLS GRID */
    .steering-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .volume-rocker {
      display: flex;
      flex-direction: column;
      gap: 8px;
      background: rgba(14, 19, 31, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 16px;
      padding: 8px;
    }

    .vol-btn {
      height: 56px;
      border-radius: 12px;
    }

    .action-column {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .action-btn {
      flex: 1;
      min-height: 56px;
      border-radius: 14px;
    }

    .action-btn.power {
      border-color: rgba(255, 23, 68, 0.3);
    }
    .action-btn.power:active, .action-btn.power.active {
      border-color: var(--accent-red);
      background: rgba(255, 23, 68, 0.2);
      box-shadow: 0 0 20px rgba(255, 23, 68, 0.4);
    }

    .action-btn.play {
      border-color: rgba(0, 229, 255, 0.3);
    }

    /* TRANSMISSION GEAR SELECTOR */
    .prnd-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      background: rgba(12, 17, 27, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 16px;
      padding: 6px;
      margin-bottom: 10px;
    }

    .gear-btn {
      height: 48px;
      border-radius: 10px;
      font-size: 17px;
      font-weight: 800;
      color: var(--text-dim);
      background: transparent;
      border: 1px solid transparent;
      box-shadow: none;
    }

    .gear-btn.selected {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-main);
      border-color: rgba(255, 255, 255, 0.15);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    .gear-btn.gear-r.selected {
      background: rgba(255, 23, 68, 0.2);
      color: var(--accent-red);
      border-color: var(--accent-red);
      box-shadow: 0 0 20px rgba(255, 23, 68, 0.5);
    }

    .reverse-toggle-btn {
      width: 100%;
      height: 58px;
      border-radius: 14px;
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: center;
      gap: 12px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.5px;
      background: linear-gradient(135deg, rgba(255, 23, 68, 0.15), rgba(41, 121, 255, 0.08));
      border: 1px solid rgba(255, 23, 68, 0.4);
    }

    .reverse-toggle-btn.engaged {
      background: linear-gradient(135deg, rgba(255, 23, 68, 0.4), rgba(255, 23, 68, 0.15));
      border-color: var(--accent-red);
      box-shadow: 0 0 24px rgba(255, 23, 68, 0.6);
      color: #fff;
    }

    .reverse-indicator {
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: #444;
      transition: all 0.2s;
    }

    .reverse-toggle-btn.engaged .reverse-indicator {
      background: var(--accent-red);
      box-shadow: 0 0 14px var(--accent-red);
      animation: pulse 1s infinite;
    }

    /* TELEMETRY CONSOLE */
    .telemetry-box {
      background: #06090e;
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 12px;
      padding: 8px 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: var(--text-dim);
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 80px;
      overflow-y: auto;
    }

    .telemetry-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .telemetry-key {
      color: var(--accent-cyan);
      font-weight: 600;
    }

    .telemetry-latency {
      color: var(--accent-green);
    }

    /* KEYBOARD HINTS */
    .hints {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: center;
      font-size: 11px;
      color: var(--text-dim);
      margin-top: 2px;
    }

    .kbd {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 6px;
      padding: 2px 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      color: var(--text-main);
    }
  </style>
</head>
<body>

  <div class="container">
    
    <!-- HEADER -->
    <header class="header">
      <div class="brand">
        <div class="brand-logo">A</div>
        <div>
          <div class="brand-title">Apex IVI Controller</div>
          <div class="brand-sub">Controls & Bluetooth Recovery</div>
        </div>
      </div>
      <div class="status-pill" id="statusPill">
        <div class="status-dot"></div>
        <span>ONLINE</span>
      </div>
    </header>

    <!-- BLUETOOTH DEVICE MANAGER & RESCUE -->
    <section class="card">
      <div class="card-header">
        <div class="card-title">
          <svg viewBox="0 0 24 24"><path d="M17.71 7.71L12 2h-1v7.59L6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 11 14.41V22h1l5.71-5.71-4.3-4.29 4.3-4.29zM13 5.83l1.88 1.88L13 9.59V5.83zm1.88 10.46L13 18.17v-3.76l1.88 1.88z"/></svg>
          Bluetooth Device Manager
        </div>
        <div id="btStatusBadge" style="font-size: 11px; font-weight: 600; color: var(--accent-green);">PEBBLE CONNECTED</div>
      </div>

      <!-- ACTIVE DEVICE QUICK BANNER -->
      <div class="bt-active-banner" id="btActiveBanner">
        <div class="bt-active-info">
          <div class="bt-device-icon" id="btActiveIcon">🖱️</div>
          <div>
            <div class="bt-active-name" id="btActiveName">Logitech Pebble</div>
            <div class="bt-active-status" id="btActiveStatus">
              <span class="status-dot" style="width: 6px; height: 6px;"></span>
              Connected & Ready (100% Bat)
            </div>
          </div>
        </div>
        <button class="bt-act-btn" id="btQuickActionBtn" onclick="quickReconnect()">⚡ Reconnect</button>
      </div>

      <!-- SCAN & REFRESH TOOLBAR -->
      <div class="bt-toolbar">
        <button class="btn bt-scan-btn" id="btnScan" onclick="scanBtDevices()">
          <span id="scanIcon">🔍</span>
          <span id="scanLabel">SCAN FOR NEW DEVICES</span>
        </button>
        <button class="btn bt-scan-btn" style="flex: 0 0 90px;" onclick="refreshBtList()">
          REFRESH
        </button>
      </div>

      <!-- DEVICE LIST -->
      <div class="bt-device-list" id="btDeviceList">
        <div style="font-size: 11px; color: var(--text-dim); text-align: center; padding: 10px;">Loading Bluetooth devices...</div>
      </div>

      <!-- DIRECT MAC PAIRING -->
      <div class="bt-manual-connect">
        <input type="text" class="bt-input" id="manualMacInput" placeholder="MAC Address (e.g. EE:0F:AF:4A:EB:9C)">
        <button class="bt-act-btn connect" onclick="connectManualMac()">Connect</button>
      </div>
    </section>


    <!-- STEERING WHEEL CONTROLS -->
    <section class="card">
      <div class="card-header">
        <div class="card-title">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8 0-.55.45-1 1-1h3.13c.47 1.74 1.7 3.16 3.32 3.82V19c0 .55.45 1 1 1s1-.45 1-1v-2.18c1.62-.66 2.85-2.08 3.32-3.82H21c.55 0 1 .45 1 1 0 4.41-3.59 8-8 8z"/></svg>
          Steering Wheel Cluster
        </div>
        <div style="font-size: 11px; color: var(--text-dim);">Hold to repeat</div>
      </div>

      <div class="steering-grid">
        <!-- VOLUME ROCKER -->
        <div class="volume-rocker">
          <button class="btn vol-btn vol-up" id="btnVolUp">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 15l-6-6-6 6"/></svg>
            <div class="btn-label">VOL +</div>
            <div class="btn-sub">[Key &uarr;]</div>
          </button>
          
          <button class="btn vol-btn vol-down" id="btnVolDown">
            <div class="btn-label">VOL -</div>
            <div class="btn-sub">[Key &darr;]</div>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
          </button>
        </div>

        <!-- ACTION BUTTONS -->
        <div class="action-column">
          <button class="btn action-btn play" id="btnPlay" onclick="sendKey('play_pause')">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            <div class="btn-label">PLAY / MUTE</div>
            <div class="btn-sub">[Key 9]</div>
          </button>

          <button class="btn action-btn power" id="btnPower" onclick="sendKey('power')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10"/></svg>
            <div class="btn-label">MEDIA OFF</div>
            <div class="btn-sub">[Key 0]</div>
          </button>
        </div>
      </div>
    </section>

    <!-- TRANSMISSION / GEAR SHIFTER -->
    <section class="card">
      <div class="card-header">
        <div class="card-title">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg>
          Vehicle Transmission
        </div>
        <div style="font-size: 11px; color: var(--text-dim);">Gear Selector</div>
      </div>

      <div class="prnd-bar">
        <button class="btn gear-btn selected" id="gearP" onclick="selectGear('P')">P</button>
        <button class="btn gear-btn gear-r" id="gearR" onclick="selectGear('R')">R</button>
        <button class="btn gear-btn" id="gearN" onclick="selectGear('N')">N</button>
        <button class="btn gear-btn" id="gearD" onclick="selectGear('D')">D</button>
      </div>

      <button class="btn reverse-toggle-btn" id="revToggleBtn" onclick="toggleReverse()">
        <div class="reverse-indicator"></div>
        <span>TOGGLE REVERSE GEAR (DRVM)</span>
        <span class="btn-sub" style="font-size: 11px;">[Key R]</span>
      </button>
    </section>

    <!-- LIVE TELEMETRY & EVENT LOG -->
    <section class="card" style="padding: 14px 18px;">
      <div class="card-header" style="margin-bottom: 8px;">
        <div class="card-title">Event Telemetry Log</div>
        <div id="pingBadge" style="font-family: 'JetBrains Mono'; font-size: 11px; color: var(--accent-green);">&lt; 2ms</div>
      </div>
      <div class="telemetry-box" id="telemetryBox">
        <div class="telemetry-row">
          <span>[SYSTEM READY] Listening for inputs</span>
          <span class="telemetry-latency">ONLINE</span>
        </div>
      </div>
    </section>

    <!-- PHYSICAL KEYBOARD HINTS -->
    <div class="hints">
      <span>Keyboard Shortcuts:</span>
      <span class="kbd">&uarr; Vol+</span>
      <span class="kbd">&darr; Vol-</span>
      <span class="kbd">9 Play/Pause</span>
      <span class="kbd">0 Media Off</span>
      <span class="kbd">R Reverse Gear</span>
    </div>

  </div>

  <script>
    let currentVolume = 28;
    let isReverse = false;
    let audioCtx = null;
    let knownDevices = [];

    function playClickSound() {
      try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(320, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(120, audioCtx.currentTime + 0.035);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.035);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.04);
      } catch (e) {}
    }

    function logEvent(action, code, latency) {
      const box = document.getElementById('telemetryBox');
      const row = document.createElement('div');
      row.className = 'telemetry-row';
      const timeStr = new Date().toTimeString().split(' ')[0];
      row.innerHTML = `<span>[${timeStr}] <span class="telemetry-key">${action}</span> (${code})</span><span class="telemetry-latency">${latency}ms</span>`;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;
      while (box.children.length > 15) box.removeChild(box.firstChild);
    }

    function updateVolumeUI(vol) {
      currentVolume = Math.max(0, Math.min(45, vol));
      document.getElementById('volNumber').innerText = currentVolume;
      const pct = Math.round((currentVolume / 45) * 100);
      document.getElementById('volBarFill').style.width = pct + '%';
      document.getElementById('volumeGainBadge').innerText = pct + '% GAIN';
    }

    async function sendKey(keyName) {
      playClickSound();
      if (navigator.vibrate) navigator.vibrate(15);
      const t0 = performance.now();
      try {
        const res = await fetch('/api/key', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ key: keyName })
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        logEvent(data.key.toUpperCase(), data.code, latency);
        document.getElementById('pingBadge').innerText = latency + 'ms';
        if (data.volume !== undefined) {
          updateVolumeUI(data.volume);
        }
      } catch (e) {
        logEvent(keyName.toUpperCase(), 'FAIL', 'ERR');
      }
    }

    async function setDirectVolume(vol) {
      playClickSound();
      if (navigator.vibrate) navigator.vibrate(20);
      const t0 = performance.now();
      try {
        const res = await fetch('/api/volume', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ volume: vol })
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        updateVolumeUI(data.volume);
        logEvent('SET_VOL', data.volume, latency);
      } catch (e) {}
    }

    async function toggleReverse() {
      await sendKey('reverse');
      isReverse = !isReverse;
      updateGearUI(isReverse ? 'R' : 'P');
    }

    function selectGear(gear) {
      if (gear === 'R') {
        if (!isReverse) toggleReverse();
      } else {
        if (isReverse) toggleReverse();
        else updateGearUI(gear);
      }
    }

    function updateGearUI(gear) {
      ['P', 'R', 'N', 'D'].forEach(g => {
        const btn = document.getElementById('gear' + g);
        if (btn) btn.classList.toggle('selected', g === gear);
      });
      const revBtn = document.getElementById('revToggleBtn');
      if (revBtn) revBtn.classList.toggle('engaged', gear === 'R');
    }

    // Hold-to-repeat for Volume Buttons
    function setupHoldToRepeat(elementId, keyName) {
      const el = document.getElementById(elementId);
      let timeoutId = null;
      let intervalId = null;

      function start() {
        sendKey(keyName);
        timeoutId = setTimeout(() => {
          intervalId = setInterval(() => sendKey(keyName), 110);
        }, 300);
      }

      function stop() {
        clearTimeout(timeoutId);
        clearInterval(intervalId);
      }

      el.addEventListener('mousedown', (e) => { e.preventDefault(); start(); });
      el.addEventListener('mouseup', stop);
      el.addEventListener('mouseleave', stop);
      el.addEventListener('touchstart', (e) => { e.preventDefault(); start(); }, {passive: false});
      el.addEventListener('touchend', stop);
      el.addEventListener('touchcancel', stop);
    }

    setupHoldToRepeat('btnVolUp', 'vol_up');
    setupHoldToRepeat('btnVolDown', 'vol_down');

    // =========================================================================
    // BLUETOOTH RESCUE MANAGER JAVASCRIPT
    // =========================================================================
    function getDeviceIcon(icon, name) {
      const n = (name + ' ' + icon).toLowerCase();
      if (n.includes('mouse') || n.includes('pebble')) return '🖱️';
      if (n.includes('keyboard')) return '⌨️';
      if (n.includes('phone') || n.includes('edge') || n.includes('iphone') || n.includes('samsung')) return '📱';
      if (n.includes('headset') || n.includes('audio') || n.includes('ear') || n.includes('bud')) return '🎧';
      return 'ᛒ';
    }

    async function refreshBtList() {
      try {
        const res = await fetch('/api/bluetooth/devices');
        const list = await res.json();
        knownDevices = list;
        renderBtDevices(list);
      } catch (e) {
        document.getElementById('btDeviceList').innerHTML = '<div style="font-size:11px;color:#ff1744;text-align:center;">Failed to load Bluetooth devices</div>';
      }
    }

    function renderBtDevices(devices) {
      const listEl = document.getElementById('btDeviceList');
      if (!devices || devices.length === 0) {
        listEl.innerHTML = '<div style="font-size:11px;color:var(--text-dim);text-align:center;padding:12px;">No Bluetooth devices found. Click "Scan for New Devices".</div>';
        return;
      }

      let activeDevice = devices.find(d => d.connected);
      const bannerEl = document.getElementById('btActiveBanner');
      const badgeEl = document.getElementById('btStatusBadge');

      if (activeDevice) {
        document.getElementById('btActiveIcon').innerText = getDeviceIcon(activeDevice.icon, activeDevice.name);
        document.getElementById('btActiveName').innerText = activeDevice.name;
        document.getElementById('btActiveStatus').innerHTML = `<span class="status-dot" style="width:6px;height:6px;"></span> Connected ${activeDevice.battery ? '('+activeDevice.battery+'% Bat)' : ''}`;
        badgeEl.innerText = activeDevice.name.toUpperCase() + ' ACTIVE';
        badgeEl.style.color = 'var(--accent-green)';
        document.getElementById('btQuickActionBtn').innerText = 'Disconnect';
        document.getElementById('btQuickActionBtn').className = 'bt-act-btn disconnect';
        document.getElementById('btQuickActionBtn').onclick = () => disconnectDevice(activeDevice.mac);
      } else {
        document.getElementById('btActiveIcon').innerText = '⚠️';
        document.getElementById('btActiveName').innerText = 'No Mouse Connected';
        document.getElementById('btActiveStatus').innerHTML = '<span style="color:var(--accent-amber);">Hardware cursor inactive</span>';
        badgeEl.innerText = 'DISCONNECTED';
        badgeEl.style.color = 'var(--accent-amber)';
        
        // Find if pebble is known
        const pebble = devices.find(d => d.name.toLowerCase().includes('pebble'));
        document.getElementById('btQuickActionBtn').innerText = pebble ? '⚡ Reconnect Pebble' : 'Scan Now';
        document.getElementById('btQuickActionBtn').className = 'bt-act-btn connect';
        document.getElementById('btQuickActionBtn').onclick = pebble ? () => connectDevice(pebble.mac) : scanBtDevices;
      }

      listEl.innerHTML = '';
      devices.forEach(dev => {
        const item = document.createElement('div');
        item.className = 'bt-device-item' + (dev.connected ? ' connected' : '');
        
        const iconChar = getDeviceIcon(dev.icon, dev.name);
        const statusBadge = dev.connected 
          ? '<span style="color:var(--accent-green);font-size:10px;font-weight:600;">CONNECTED</span>'
          : dev.paired 
            ? '<span style="color:var(--accent-cyan);font-size:10px;">PAIRED</span>'
            : '<span style="color:var(--accent-amber);font-size:10px;">DISCOVERED</span>';

        let actionBtn = '';
        if (dev.connected) {
          actionBtn = `<button class="bt-act-btn disconnect" onclick="disconnectDevice('${dev.mac}')">Disconnect</button>`;
        } else if (dev.paired) {
          actionBtn = `<button class="bt-act-btn connect" onclick="connectDevice('${dev.mac}')">Connect</button>`;
        } else {
          actionBtn = `<button class="bt-act-btn connect" onclick="pairDevice('${dev.mac}')">Pair</button>`;
        }

        item.innerHTML = `
          <div class="bt-dev-meta">
            <span style="font-size:18px;">${iconChar}</span>
            <div class="bt-dev-texts">
              <div class="bt-dev-title">${dev.name}</div>
              <div class="bt-dev-mac">${dev.mac} &bull; ${statusBadge}</div>
            </div>
          </div>
          <div class="bt-dev-actions">
            ${actionBtn}
            <button class="bt-act-btn remove" title="Forget Device" onclick="removeDevice('${dev.mac}')">✕</button>
          </div>
        `;
        listEl.appendChild(item);
      });
    }

    async function scanBtDevices() {
      const btn = document.getElementById('btnScan');
      btn.classList.add('scanning');
      document.getElementById('scanIcon').innerText = '📡';
      document.getElementById('scanLabel').innerText = 'SCANNING (8s)...';
      logEvent('BT_SCAN', 'DISCOVERY_ON', 0);

      try {
        await fetch('/api/bluetooth/scan', {method: 'POST'});
      } catch (e) {}

      // Poll refreshed devices every 2s during scan
      let elapsed = 0;
      const interval = setInterval(async () => {
        elapsed += 2;
        await refreshBtList();
        if (elapsed >= 9) {
          clearInterval(interval);
          btn.classList.remove('scanning');
          document.getElementById('scanIcon').innerText = '🔍';
          document.getElementById('scanLabel').innerText = 'SCAN FOR NEW DEVICES';
          logEvent('BT_SCAN', 'COMPLETE', 9000);
        }
      }, 2000);
    }

    async function connectDevice(mac) {
      logEvent('BT_CONNECT', mac, 0);
      const t0 = performance.now();
      try {
        const res = await fetch('/api/bluetooth/connect', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mac: mac })
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        logEvent(data.success ? 'CONNECTED' : 'CONN_FAIL', mac, latency);
        refreshBtList();
      } catch (e) {
        logEvent('CONN_ERR', mac, 0);
      }
    }

    async function pairDevice(mac) {
      logEvent('BT_PAIR', mac, 0);
      const t0 = performance.now();
      try {
        const res = await fetch('/api/bluetooth/pair', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mac: mac })
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        logEvent(data.success ? 'PAIRED_OK' : 'PAIR_FAIL', mac, latency);
        refreshBtList();
      } catch (e) {
        logEvent('PAIR_ERR', mac, 0);
      }
    }

    async function disconnectDevice(mac) {
      logEvent('BT_DISCONNECT', mac, 0);
      try {
        await fetch('/api/bluetooth/disconnect', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mac: mac })
        });
        refreshBtList();
      } catch (e) {}
    }

    async function removeDevice(mac) {
      if (!confirm('Forget Bluetooth device ' + mac + '?')) return;
      try {
        await fetch('/api/bluetooth/remove', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mac: mac })
        });
        refreshBtList();
      } catch (e) {}
    }

    function connectManualMac() {
      const input = document.getElementById('manualMacInput');
      const mac = input.value.trim();
      if (!mac) return;
      pairDevice(mac);
      input.value = '';
    }

    function quickReconnect() {
      const pebble = knownDevices.find(d => d.name.toLowerCase().includes('pebble'));
      if (pebble) {
        connectDevice(pebble.mac);
      } else {
        scanBtDevices();
      }
    }

    // Physical Keyboard Listener
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;
      if (e.repeat) return;
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        sendKey('vol_up');
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        sendKey('vol_down');
      } else if (e.key === '9') {
        e.preventDefault();
        sendKey('play_pause');
      } else if (e.key === '0') {
        e.preventDefault();
        sendKey('power');
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        toggleReverse();
      }
    });

    // Periodic sync
    refreshBtList();
    setInterval(refreshBtList, 4000);

    async function syncStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.volume !== undefined && data.volume !== currentVolume) {
          updateVolumeUI(data.volume);
        }
        if (data.reverse_active !== isReverse) {
          isReverse = data.reverse_active;
          updateGearUI(isReverse ? 'R' : 'P');
        }
      } catch (e) {}
    }
    syncStatus();
    setInterval(syncStatus, 1500);
  </script>
</body>
</html>
"""

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))

        elif self.path == "/api/bluetooth/devices":
            devs = get_bluetooth_devices()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(devs).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        t0 = time.time()
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}

        if self.path == "/api/key":
            key = data.get("key", "").lower()
            code = data.get("code")
            if not code and key in KEY_MAP:
                code = KEY_MAP[key]

            success = False
            if code:
                success = uinput.emit_key(code)
                state["last_key"] = key or str(code)
                state["last_key_time"] = time.time()
                
                # Volume state adjustment
                if key in ["vol_up", "volume_up", "key_up"]:
                    state["volume"] = min(45, state["volume"] + 1)
                    sync_alsa_volume(state["volume"])
                elif key in ["vol_down", "volume_down", "key_down"]:
                    state["volume"] = max(0, state["volume"] - 1)
                    sync_alsa_volume(state["volume"])
                elif key in ["reverse", "reverse_gear"]:
                    state["reverse_active"] = not state["reverse_active"]
                    state["current_gear"] = "R" if state["reverse_active"] else "P"

            elapsed_ms = round((time.time() - t0) * 1000, 2)
            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            resp = {
                "success": success,
                "key": key or str(code),
                "code": code,
                "volume": state["volume"],
                "elapsed_ms": elapsed_ms
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif self.path == "/api/volume":
            target_vol = data.get("volume", state["volume"])
            target_vol = max(0, min(45, int(target_vol)))
            diff = target_vol - state["volume"]
            state["volume"] = target_vol
            sync_alsa_volume(state["volume"])

            if diff > 0:
                uinput.emit_key(103)
            elif diff < 0:
                uinput.emit_key(108)

            elapsed_ms = round((time.time() - t0) * 1000, 2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            resp = {
                "success": True,
                "volume": state["volume"],
                "elapsed_ms": elapsed_ms
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif self.path == "/api/bluetooth/scan":
            trigger_bluetooth_scan(8)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "scanning", "duration": 8}).encode("utf-8"))

        elif self.path == "/api/bluetooth/connect":
            mac = data.get("mac", "")
            ok = connect_bt_device(mac) if mac else False
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": ok, "mac": mac}).encode("utf-8"))

        elif self.path == "/api/bluetooth/pair":
            mac = data.get("mac", "")
            ok = pair_and_connect_bt_device(mac) if mac else False
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": ok, "mac": mac}).encode("utf-8"))

        elif self.path == "/api/bluetooth/disconnect":
            mac = data.get("mac", "")
            ok = disconnect_bt_device(mac) if mac else False
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": ok, "mac": mac}).encode("utf-8"))

        elif self.path == "/api/bluetooth/remove":
            mac = data.get("mac", "")
            ok = remove_bt_device(mac) if mac else False
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": ok, "mac": mac}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def main():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"[Apex IVI] Button & Bluetooth Emulator listening on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        uinput.close()
        server.server_close()

if __name__ == "__main__":
    main()
