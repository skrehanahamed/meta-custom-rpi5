SUMMARY = "Apex IVI - Automotive In-Vehicle Infotainment System"
DESCRIPTION = "Apex IVI Infotainment System for Raspberry Pi 5"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=2e38a213692a61b05df72d516e45cfd1"

SRC_URI = "git:///workspace/sources/Apex_MidEnd_IVI;protocol=file;branch=main"
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

inherit qt6-cmake

DEPENDS += "qtbase qtdeclarative qtdeclarative-native qtmultimedia"
RDEPENDS:${PN} += "qtbase qtdeclarative qtmultimedia"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${B}/ApexIVI ${D}${bindir}/ApexIVI
}

FILES:${PN} += "${bindir}/ApexIVI"
