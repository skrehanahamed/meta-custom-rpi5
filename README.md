# meta-custom-rpi5: Headless Qt 6.7 IVI & BSP for Raspberry Pi 5

Custom Yocto Scarthgap (5.0.x) BSP layer and deployment toolkit for Raspberry Pi 5 (`raspberrypi5`, ARM64 / aarch64).

Pre-configured with Qt 6.7 LTS, TigerVNC remote desktop, Openbox kiosk window manager, Bluetooth 5.0, multi-touch touchscreen input, automatic Wi-Fi association, and the Apex Mid-End In-Vehicle Infotainment (IVI) system.

---

## Quick Start: 1-Click SSH Deployment (Zero Compilation)

If the Raspberry Pi 5 is already running the Yocto image on the local network, compiling from source is not required. The pre-compiled ARM64 binary is bundled in this repository.

### Deployment Command:

```bash
# Clone this repository
git clone git@github.com:skrehanahamed/meta-custom-rpi5.git
cd meta-custom-rpi5

# Deploy to Raspberry Pi 5 target IP
chmod +x scripts/deploy-to-pi.sh
./scripts/deploy-to-pi.sh 192.168.1.217
```

This procedure performs the following:
1. Terminates any active IVI application processes.
2. Transfers the optimized `bin/ApexIVI` binary into `/usr/bin/ApexIVI`.
3. Restarts `tigervnc.service` directly into frameless fullscreen touchscreen kiosk mode.

---

## MicroSD OS Image Installation (Zero Compilation)

The complete compressed production OS disk image is tracked in this repository under `deploy/image/`.

### 1. Reassemble the image parts:
```bash
./scripts/assemble-image.sh
```
This command verifies SHA256 integrity and generates `deploy/image/rpi5-qt-headless-image.wic.bz2`.

### 2. Write to MicroSD Card:
- Open Raspberry Pi Imager or BalenaEtcher.
- Select "Use Custom" and choose `rpi5-qt-headless-image.wic.bz2`.
- Target the MicroSD card and write the image.
- Insert the card into the Raspberry Pi 5 and power on. The system connects automatically to configured Wi-Fi networks and launches the IVI service.

---

## Remote Display and VNC Access

The system boots headlessly and renders the IVI interface at 1280x720 24-bit color on display `:1` (port `5901`).

### macOS Connection:
- Terminal:
  ```bash
  open vnc://192.168.1.217:5901
  ```
- Finder: Press Cmd + K and connect to `vnc://192.168.1.217:5901`.
- VNC Password: `raspberry` (Username may remain blank).

### Linux and Windows Connection:
- Connect using any standard VNC client (TigerVNC Viewer, RealVNC, Remmina) to `<PI_IP>:5901`.

---

## Repository Structure

```
meta-custom-rpi5/
├── bin/
│   └── ApexIVI                     # Pre-compiled ARM64 binary (fullscreen kiosk, blank cursor)
├── scripts/
│   ├── deploy-to-pi.sh             # SSH deployment script
│   └── assemble-image.sh           # Image part reassembly script
├── deploy/
│   └── image/                      # Multi-part production disk image and checksums
├── conf/
│   └── layer.conf                  # Yocto layer configuration
├── recipes-connectivity/
│   └── rpi-wifi-autoconfig/        # Automated Wi-Fi association service
├── recipes-core/
│   └── images/
│       └── rpi5-qt-headless-image.bb # Bootable OS image recipe
├── recipes-qt/
│   ├── apex-ivi/                   # BitBake recipe for Apex Mid-End IVI
│   └── qt6-sample-app/             # BitBake recipe for Qt 6 test application
├── recipes-remote/
│   └── rpi-tigervnc-service/       # TigerVNC service and display startup configs
├── docker/
│   └── Dockerfile                  # Containerized Yocto build environment
├── docker-build.sh                 # Docker execution wrapper
└── setup-workspace.sh              # Workspace dependency initialization script
```

---

## Source Build Instructions (Optional)

To modify system packages or rebuild the full operating system image:

### Prerequisites:
- Docker Desktop with at least 50 GB available disk space.

### Commands:
```bash
# 1. Initialize workspace layers
./docker-build.sh setup

# 2. Build full bootable disk image
./docker-build.sh build

# 3. Or compile individual recipes inside build shell
./docker-build.sh shell
source /workspace/sources/poky/oe-init-build-env /workspace/build
bitbake apex-ivi
```

---

## System Configuration and Defaults

- Root Login: `ssh root@192.168.1.217` (Passwordless)
- VNC Port: `5901` (Display `:1`)
- VNC Password: `raspberry`
- Kernel: Linux 6.6.63 LTS (BCM2712 aarch64)
- Framework: Qt 6.7.3 LTS
