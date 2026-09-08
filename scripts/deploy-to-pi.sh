#!/usr/bin/env bash
# ==============================================================================
# Fast 1-Click Deployment Script for Raspberry Pi 5 Headless IVI
# Zero Compilation Needed - Deploys pre-built ARM64 binary over SSH
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"
BINARY_PATH="${REPO_DIR}/bin/rpi5/ApexIVI"
TARGET_IP="${1:-192.168.1.217}"
TARGET_USER="root"

if [ ! -f "${BINARY_PATH}" ]; then
    echo "Error: Pre-compiled binary not found at ${BINARY_PATH}"
    exit 1
fi

echo "========================================================"
echo "  Deploying Apex IVI to Raspberry Pi 5 ($TARGET_IP)"
echo "========================================================"

echo ">> 1. Stopping existing IVI instance..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_IP}" \
    "systemctl stop tigervnc.service; killall -9 ApexIVI 2>/dev/null || true"

echo ">> 2. Transferring pre-compiled ARM64 binary (15 MB)..."
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${BINARY_PATH}" "${TARGET_USER}@${TARGET_IP}:/usr/bin/ApexIVI"

echo ">> 3. Ensuring execution permissions and restarting TigerVNC..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_IP}" \
    "chmod +x /usr/bin/ApexIVI; systemctl restart tigervnc.service"

echo ">> 4. Verifying status..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TARGET_USER}@${TARGET_IP}" \
    "systemctl is-active tigervnc"

echo "========================================================"
echo "  Deployment Complete! Apex IVI is live on display :1"
echo "  Connect via: open vnc://${TARGET_IP}:5901"
echo "========================================================"
