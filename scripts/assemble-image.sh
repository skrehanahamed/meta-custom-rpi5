#!/usr/bin/env bash
# ==============================================================================
# Helper to reassemble multi-part compressed image from GitHub
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"
IMAGE_DIR="${REPO_DIR}/deploy/image"
OUTPUT_FILE="${IMAGE_DIR}/rpi5-qt-headless-image.wic.bz2"

echo ">> Reassembling ${OUTPUT_FILE} from git parts..."
cat "${IMAGE_DIR}"/rpi5-qt-headless-image.wic.bz2.part-* > "${OUTPUT_FILE}"

echo ">> Verifying SHA256 checksum..."
ACTUAL_HASH=$(shasum -a 256 "${OUTPUT_FILE}" | awk '{print $1}')
EXPECTED_HASH=$(awk '{print $1}' "${IMAGE_DIR}/original.sha256")

if [ "${ACTUAL_HASH}" = "${EXPECTED_HASH}" ]; then
    echo ">> [SUCCESS] Checksum verified: ${ACTUAL_HASH}"
    echo ">> Ready to flash with Raspberry Pi Imager or bunzip2!"
else
    echo ">> [ERROR] Checksum mismatch!"
    exit 1
fi
