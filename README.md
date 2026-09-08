# meta-custom-rpi5: Headless Qt 6.7 IVI & BSP for Raspberry Pi 5

Custom **Yocto Scarthgap (5.0.x)** BSP layer and deployment toolkit for **Raspberry Pi 5 (`raspberrypi5`, ARM64 / aarch64)**.

Pre-configured with full **Qt 6.7 LTS**, **TigerVNC remote desktop**, **Openbox kiosk window manager**, **Bluetooth 5.0**, **multi-touch touchscreen input**, **out-of-the-box Wi-Fi autoconfiguration**, and the **Apex Mid-End In-Vehicle Infotainment (IVI)** system.

---

## 🚀 Quick Start: 1-Click SSH Deployment (Zero Compilation)

If your Raspberry Pi 5 is already running the Yocto image on your network, you do **not** need to compile anything. The pre-compiled ARM64 binary is bundled in this repository.

### Deploy to your Pi in 3 seconds:

```bash
# Clone this repository
git clone git@github.com:skrehanahamed/meta-custom-rpi5.git
cd meta-custom-rpi5

# Deploy to Raspberry Pi 5 IP (e.g. 192.168.1.217)
chmod +x scripts/deploy-to-pi.sh
./scripts/deploy-to-pi.sh 192.168.1.217
```

This automatically:
1. Stops any existing IVI instances.
2. Transfers the optimized `bin/ApexIVI` binary into `/usr/bin/ApexIVI`.
3. Restarts `tigervnc.service` directly into pure fullscreen touchscreen kiosk mode.

---

## 🖥️ Viewing the IVI Interface (TigerVNC / Screen Sharing)

The Raspberry Pi 5 boots headlessly and renders the IVI at **1280x720 24-bit** color on display `:1` (port `5901`).

### Connect from macOS:
- In Terminal:
  ```bash
  open vnc://192.168.1.217:5901
  ```
- Or in **Finder**: Press <kbd>Cmd</kbd> + <kbd>K</kbd> and enter `vnc://192.168.1.217:5901`.
- **Default VNC Password**: `raspberry` (or leave username blank).

### Connect from Linux / Windows:
- Use any standard VNC client (TigerVNC Viewer, RealVNC, Remmina) pointing to `<PI_IP>:5901`.

---

## 📂 Repository Structure

```
meta-custom-rpi5/
├── bin/
│   └── ApexIVI                     # Pre-compiled ARM64 binary (fullscreen kiosk + blank cursor)
├── scripts/
│   └── deploy-to-pi.sh             # 1-click SSH deployment script
├── conf/
│   └── layer.conf                  # Yocto layer definition
├── recipes-connectivity/
│   └── rpi-wifi-autoconfig/        # Dual-band automatic Wi-Fi association on boot
├── recipes-core/
│   └── images/
│       └── rpi5-qt-headless-image.bb # Full production IVI bootable image recipe
├── recipes-qt/
│   ├── apex-ivi/                   # BitBake recipe for Apex Mid-End IVI
│   └── qt6-sample-app/             # BitBake recipe for Qt 6 test application
├── recipes-remote/
│   └── rpi-tigervnc-service/       # TigerVNC systemd service & xstartup configs
├── docker/
│   └── Dockerfile                  # Containerized Yocto Scarthgap build environment
├── docker-build.sh                 # Docker runner helper script
└── setup-workspace.sh              # Layer cloner and workspace initializer
```

---

## 🛠️ Building from Scratch (Optional)

If you ever wish to modify recipes or rebuild the full bootable microSD OS disk image:

### Prerequisites
- Docker Desktop (macOS or Linux) with at least 50 GB free disk space.

### Steps:
```bash
# 1. Setup Yocto workspace layers
./docker-build.sh setup

# 2. Build the complete bootable disk image
./docker-build.sh build

# 3. Or compile only the Apex IVI recipe
./docker-build.sh shell
source /workspace/sources/poky/oe-init-build-env /workspace/build
bitbake apex-ivi
```

---

## 🔑 Default Credentials & System Info

- **Root Login**: `ssh root@192.168.1.217` (Passwordless)
- **VNC Display**: `:1` (Port `5901`)
- **VNC Password**: `raspberry`
- **Linux Kernel**: 6.6.63 LTS (RPi 5 BCM2712 optimized, 64-bit ARM64)
- **Qt Version**: Qt 6.7.3 LTS (`qtbase`, `qtdeclarative`, `qtmultimedia`, `qtquick3d`)
