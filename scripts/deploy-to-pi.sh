#!/usr/bin/env bash
# ==============================================================================
# Generic Deployment Script for Raspberry Pi 5 Qt 6 Applications
# Deploys any compiled ARM64 Qt binary over SSH to run natively on hardware GPU
# ==============================================================================
set -euo pipefail

BINARY_PATH="${1:-}"
TARGET_HOST="${2:-raspberrypi5.local}"
TARGET_USER="root"

if [ -z "${BINARY_PATH}" ]; then
    echo "========================================================================"
    echo "  Raspberry Pi 5 Qt 6 Generic Application Deployer"
    echo "========================================================================"
    echo "Usage: $0 <path_to_arm64_qt_binary> [target_ip_or_hostname]"
    echo ""
    echo "Example:"
    echo "  $0 ./build/my-qt-app 192.168.1.50"
    echo "  $0 ./my-dashboard raspberrypi5.local"
    echo "========================================================================"
    exit 1
fi

if [ ! -f "${BINARY_PATH}" ]; then
    echo "Error: Binary not found at '${BINARY_PATH}'"
    exit 1
fi

APP_NAME="$(basename "${BINARY_PATH}")"

echo "========================================================"
echo "  Deploying ${APP_NAME} to Raspberry Pi 5 (${TARGET_HOST})"
echo "========================================================"

echo ">> 1. Transferring binary to /usr/bin/${APP_NAME}..."
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "${BINARY_PATH}" "${TARGET_USER}@${TARGET_HOST}:/usr/bin/${APP_NAME}"

echo ">> 2. Setting executable permissions..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_HOST}" \
    "chmod +x /usr/bin/${APP_NAME}"

echo ">> 3. Configuring and launching systemd service (qt-app.service)..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_HOST}" "cat << 'EOF' > /etc/systemd/system/qt-app.service
[Unit]
Description=Qt 6 Native Hardware-Accelerated Application (DRM/KMS EGLFS)
After=systemd-udev-settle.service
Wants=systemd-udev-settle.service

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=HOME=/root
Environment=QT_QPA_PLATFORM=eglfs
Environment=QT_QPA_EGLFS_INTEGRATION=eglfs_kms
Environment=QT_QPA_EGLFS_KMS_CONFIG=/etc/kms.conf
Environment=QT_QPA_EGLFS_KMS_ATOMIC=1
Environment=QT_QPA_EGLFS_HIDECURSOR=0
Environment=QSG_INFO=1
ExecStartPre=-/bin/sh -c 'echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_min_interval 2>/dev/null; echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_max_interval 2>/dev/null; echo 0 > /sys/kernel/debug/bluetooth/hci0/conn_latency 2>/dev/null || true'
ExecStart=/usr/bin/${APP_NAME}
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now qt-app.service
"

echo ">> 4. Verifying service status on target..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_HOST}" \
    "systemctl is-active qt-app.service"

echo "========================================================"
echo "  Deployment Complete! ${APP_NAME} is live on HDMI (60 FPS GPU)"
echo "  Check live logs: ssh ${TARGET_USER}@${TARGET_HOST} 'journalctl -u qt-app.service -f'"
echo "========================================================"
