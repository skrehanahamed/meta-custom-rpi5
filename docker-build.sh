#!/usr/bin/env bash
# ==============================================================================
# Docker Runner for Raspberry Pi 5 Yocto Build
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="rpi5-yocto-scarthgap-builder"

# Check if Docker is installed and running
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed or not in PATH."
    echo "Please install Docker Desktop for Mac from https://www.docker.com/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Build Docker image if not present
if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo ">> Building Docker container image '${IMAGE_NAME}'..."
    docker build \
        --build-arg USER_ID="$(id -u)" \
        --build-arg GROUP_ID="$(id -g)" \
        -t "${IMAGE_NAME}" \
        "${SCRIPT_DIR}/docker"
fi

# Ensure high-performance case-sensitive volume exists for tmp directory (mandatory for macOS Docker)
docker volume create yocto-tmp >/dev/null 2>&1 || true

INTERACTIVE_FLAG=""
if [ -t 0 ]; then
    INTERACTIVE_FLAG="-it"
fi

DOCKER_CMD="docker run --rm ${INTERACTIVE_FLAG} \
    -v ${SCRIPT_DIR}:/workspace \
    -v yocto-tmp:/workspace/build/tmp \
    ${IMAGE_NAME}"

COMMAND="${1:-shell}"

case "${COMMAND}" in
    setup)
        echo ">> Setting up Yocto layers and repositories..."
        ${DOCKER_CMD} bash -c "sudo chown \$(id -u):\$(id -g) /workspace/build/tmp 2>/dev/null || true; /workspace/setup-workspace.sh"
        ;;
    build)
        echo ">> Starting BitBake build for rpi5-qt-headless-image..."
        ${DOCKER_CMD} bash -c "sudo chown \$(id -u):\$(id -g) /workspace/build/tmp 2>/dev/null || true; source /workspace/sources/poky/oe-init-build-env /workspace/build && bitbake rpi5-qt-headless-image"
        ;;
    shell)
        echo ">> Entering Yocto Build Shell..."
        ${DOCKER_CMD} bash -c "sudo chown \$(id -u):\$(id -g) /workspace/build/tmp 2>/dev/null || true; exec bash"
        ;;
    *)
        echo "Usage: $0 {setup|build|shell}"
        echo "  setup  : Clones poky, meta-raspberrypi, meta-qt6, meta-oe and initializes build/conf"
        echo "  build  : Executes 'bitbake rpi5-qt-headless-image' inside container"
        echo "  shell  : Starts an interactive bash terminal inside container"
        exit 1
        ;;
esac
