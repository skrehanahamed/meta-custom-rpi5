SUMMARY = "Apex IVI Native Automotive Infotainment"
DESCRIPTION = "Native hardware-accelerated Qt 6 DRM/KMS In-Vehicle Infotainment application with Android Auto for Raspberry Pi 5"
LICENSE = "CLOSED"

SRC_URI = " \
    file:///workspace/sources/Apex_MidEnd_IVI \
    file://apex-ivi.service \
    file://kms.json \
    file://asound.conf \
    file://apex-button-emulator.py \
    file://apex-button-emulator.service \
    file://apex-usb-reset.py \
    file://10-audio-stability.conf \
    file://20-ivi-hdmi.conf \
    file://10-bluez-ofono.conf \
    file://30-pipewire-audio.conf \
"
S = "${WORKDIR}/workspace/sources/Apex_MidEnd_IVI"

inherit qt6-cmake systemd

SYSTEMD_SERVICE:${PN} = "apex-ivi.service apex-button-emulator.service"
SYSTEMD_AUTO_ENABLE = "enable"

DEPENDS += "qtbase qtdeclarative qtdeclarative-native qtmultimedia libusb1 openssl protobuf protobuf-native boost"
RDEPENDS:${PN} += "qtbase qtdeclarative qtmultimedia pipewire wireplumber python3-core python3-io python3-netserver python3-json"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/apex-ivi.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/apex-button-emulator.service ${D}${systemd_system_unitdir}/

    install -d ${D}${systemd_system_unitdir}/apex-ivi.service.d
    install -m 0644 ${WORKDIR}/30-pipewire-audio.conf ${D}${systemd_system_unitdir}/apex-ivi.service.d/30-pipewire-audio.conf

    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/apex-button-emulator.py ${D}${bindir}/apex-button-emulator.py
    install -m 0755 ${WORKDIR}/apex-usb-reset.py ${D}${bindir}/apex-usb-reset.py

    install -d ${D}${sysconfdir}
    install -m 0644 ${WORKDIR}/kms.json ${D}${sysconfdir}/
    install -m 0644 ${WORKDIR}/asound.conf ${D}${sysconfdir}/

    install -d ${D}${sysconfdir}/pipewire/pipewire.conf.d
    install -m 0644 ${WORKDIR}/10-audio-stability.conf ${D}${sysconfdir}/pipewire/pipewire.conf.d/10-audio-stability.conf
    install -m 0644 ${WORKDIR}/20-ivi-hdmi.conf ${D}${sysconfdir}/pipewire/pipewire.conf.d/20-ivi-hdmi.conf

    install -d ${D}${sysconfdir}/wireplumber/wireplumber.conf.d
    install -m 0644 ${WORKDIR}/10-bluez-ofono.conf ${D}${sysconfdir}/wireplumber/wireplumber.conf.d/10-bluez-ofono.conf
}

FILES:${PN} += " \
    ${bindir}/ApexIVI \
    ${bindir}/apex-button-emulator.py \
    ${bindir}/apex-usb-reset.py \
    ${sysconfdir}/kms.json \
    ${sysconfdir}/asound.conf \
    ${sysconfdir}/pipewire/pipewire.conf.d/10-audio-stability.conf \
    ${sysconfdir}/pipewire/pipewire.conf.d/20-ivi-hdmi.conf \
    ${sysconfdir}/wireplumber/wireplumber.conf.d/10-bluez-ofono.conf \
    ${systemd_system_unitdir}/apex-ivi.service \
    ${systemd_system_unitdir}/apex-ivi.service.d/30-pipewire-audio.conf \
    ${systemd_system_unitdir}/apex-button-emulator.service \
"
