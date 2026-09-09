SUMMARY = "Apex IVI Native Automotive Infotainment"
DESCRIPTION = "Native hardware-accelerated Qt 6 DRM/KMS In-Vehicle Infotainment application for Raspberry Pi 5"
LICENSE = "CLOSED"

SRC_URI = "file:///workspace/sources/Apex_MidEnd_IVI"
S = "${WORKDIR}/sources/Apex_MidEnd_IVI"

inherit qt6-cmake

DEPENDS += "qtbase qtdeclarative qtmultimedia"
RDEPENDS:${PN} += "qtbase qtdeclarative qtmultimedia"

FILES:${PN} += "${bindir}/ApexIVI"
