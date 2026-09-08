SUMMARY = "Qt 6 Demonstration Application for Raspberry Pi 5 Headless System"
DESCRIPTION = "Interactive Qt6 GUI dashboard verifying TigerVNC remote rendering"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://CMakeLists.txt \
    file://main.cpp \
"

S = "${WORKDIR}"

inherit qt6-cmake

DEPENDS += "qtbase"
RDEPENDS:${PN} += "qtbase qtbase-plugins libxkbcommon"

FILES:${PN} += "${bindir}/qt6-sample-app"
