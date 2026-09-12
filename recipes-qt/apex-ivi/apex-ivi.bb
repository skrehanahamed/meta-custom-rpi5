SUMMARY = "Apex IVI Native Automotive Infotainment"
DESCRIPTION = "Native hardware-accelerated Qt 6 DRM/KMS In-Vehicle Infotainment application for Raspberry Pi 5"
LICENSE = "CLOSED"

SRC_URI = " \
    file:///workspace/sources/Apex_MidEnd_IVI \
    file://apex-ivi.service \
    file://kms.json \
    file://asound.conf \
    file://apex-button-emulator.py \
    file://apex-button-emulator.service \
"
S = "${WORKDIR}/workspace/sources/Apex_MidEnd_IVI"

inherit qt6-cmake systemd

SYSTEMD_SERVICE:${PN} = "apex-ivi.service apex-button-emulator.service"
SYSTEMD_AUTO_ENABLE = "enable"

DEPENDS += "qtbase qtdeclarative qtdeclarative-native qtmultimedia"
RDEPENDS:${PN} += "qtbase qtdeclarative qtmultimedia python3-core python3-io python3-netserver python3-json"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/apex-ivi.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/apex-button-emulator.service ${D}${systemd_system_unitdir}/

    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/apex-button-emulator.py ${D}${bindir}/apex-button-emulator.py

    install -d ${D}${sysconfdir}
    install -m 0644 ${WORKDIR}/kms.json ${D}${sysconfdir}/
    install -m 0644 ${WORKDIR}/asound.conf ${D}${sysconfdir}/
}

FILES:${PN} += " \
    ${bindir}/ApexIVI \
    ${bindir}/apex-button-emulator.py \
    ${sysconfdir}/kms.json \
    ${sysconfdir}/asound.conf \
    ${systemd_system_unitdir}/apex-ivi.service \
    ${systemd_system_unitdir}/apex-button-emulator.service \
"

