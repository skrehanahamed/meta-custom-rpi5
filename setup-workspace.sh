#!/usr/bin/env bash
# ==============================================================================
# Setup Workspace for Raspberry Pi 5 Yocto Build with Qt6, WiFi, SSH, & TigerVNC
# Yocto Version: Scarthgap (5.0 LTS)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

YOCTO_BRANCH="scarthgap"

echo "================================================================="
echo " Setting up Yocto Scarthgap Environment for Raspberry Pi 5..."
echo "================================================================="

# Create sources directory if not exists
mkdir -p sources

# 1. Clone Poky
if [ ! -d "sources/poky" ]; then
    echo ">> Cloning poky (${YOCTO_BRANCH})..."
    git clone --depth 1 -b "${YOCTO_BRANCH}" https://git.yoctoproject.org/poky sources/poky
else
    echo ">> sources/poky already exists. Skipping clone."
fi

# 2. Clone meta-openembedded
if [ ! -d "sources/meta-openembedded" ]; then
    echo ">> Cloning meta-openembedded (${YOCTO_BRANCH})..."
    git clone --depth 1 -b "${YOCTO_BRANCH}" https://git.openembedded.org/meta-openembedded sources/meta-openembedded
else
    echo ">> sources/meta-openembedded already exists. Skipping clone."
fi

# 3. Clone meta-raspberrypi
if [ ! -d "sources/meta-raspberrypi" ]; then
    echo ">> Cloning meta-raspberrypi (${YOCTO_BRANCH})..."
    git clone --depth 1 -b "${YOCTO_BRANCH}" https://git.yoctoproject.org/meta-raspberrypi sources/meta-raspberrypi
else
    echo ">> sources/meta-raspberrypi already exists. Skipping clone."
fi

# 4. Clone meta-qt6
QT6_BRANCH="6.7"
if [ ! -d "sources/meta-qt6" ]; then
    echo ">> Cloning meta-qt6 (${QT6_BRANCH})..."
    git clone --depth 1 -b "${QT6_BRANCH}" https://code.qt.io/yocto/meta-qt6.git sources/meta-qt6
else
    echo ">> sources/meta-qt6 already exists. Skipping clone."
fi

# 5. Link or copy custom layer
if [ ! -e "sources/meta-custom-rpi5" ]; then
    echo ">> Linking meta-custom-rpi5 into sources..."
    if [ -f "${SCRIPT_DIR}/conf/layer.conf" ]; then
        # SCRIPT_DIR is the meta-custom-rpi5 repository itself (e.g. GitHub Actions runner)
        ln -sfn "${SCRIPT_DIR}" sources/meta-custom-rpi5
    elif [ -d "${SCRIPT_DIR}/meta-custom-rpi5" ]; then
        ln -sfn "${SCRIPT_DIR}/meta-custom-rpi5" sources/meta-custom-rpi5
    fi
fi

# 6. Initialize Build Directory
echo ">> Initializing build directory configuration..."
mkdir -p build/conf

# Copy sample configurations if not already present
if [ ! -f "build/conf/local.conf" ]; then
    echo ">> Installing conf/local.conf..."
    cp "${SCRIPT_DIR}/conf/local.conf.sample" build/conf/local.conf
fi

if [ ! -f "build/conf/bblayers.conf" ]; then
    echo ">> Installing conf/bblayers.conf..."
    cp "${SCRIPT_DIR}/conf/bblayers.conf.sample" build/conf/bblayers.conf
fi

# Preserve disk space in GitHub Actions / CI runners
if [ "${CI:-false}" = "true" ] || [ "${GITHUB_ACTIONS:-false}" = "true" ]; then
    echo ">> Running in CI environment: enabling rm_work for disk space preservation..."
    sed -i 's/# INHERIT += "rm_work"/INHERIT += "rm_work"/' build/conf/local.conf
fi

echo "================================================================="
echo " Workspace setup complete!"
echo " Next step:"
echo "   source sources/poky/oe-init-build-env build"
echo "   bitbake rpi5-qt-headless-image"
echo "================================================================="
