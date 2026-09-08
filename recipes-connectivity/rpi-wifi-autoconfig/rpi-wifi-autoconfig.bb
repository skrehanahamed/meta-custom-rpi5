SUMMARY = "Headless Auto-WiFi and Network Configuration for Raspberry Pi 5"
DESCRIPTION = "Enables automatic Wi-Fi setup and dynamic configuration from /boot/wpa_supplicant.conf"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://rpi-wifi-autoconfig.sh \
    file://rpi-wifi-autoconfig.service \
    file://wpa_supplicant.conf.template \
    file://25-wlan.network \
    file://20-wired.network \
"

inherit systemd

SYSTEMD_PACKAGES = "${PN}"
SYSTEMD_SERVICE:${PN} = "rpi-wifi-autoconfig.service"
SYSTEMD_AUTO_ENABLE = "enable"

RDEPENDS:${PN} += " \
    wpa-supplicant \
    rfkill \
    iproute2 \
    systemd \
"

do_install() {
    # Install helper script
    install -d ${D}${sbindir}
    install -m 0755 ${WORKDIR}/rpi-wifi-autoconfig.sh ${D}${sbindir}/rpi-wifi-autoconfig.sh

    # Install systemd service
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/rpi-wifi-autoconfig.service ${D}${systemd_system_unitdir}/rpi-wifi-autoconfig.service

    # Install default wpa_supplicant-wlan0.conf
    install -d ${D}${sysconfdir}/wpa_supplicant
    install -m 0600 ${WORKDIR}/wpa_supplicant.conf.template ${D}${sysconfdir}/wpa_supplicant/wpa_supplicant-wlan0.conf

    # Install systemd-networkd network configurations
    install -d ${D}${systemd_unitdir}/network
    install -m 0644 ${WORKDIR}/25-wlan.network ${D}${systemd_unitdir}/network/25-wlan.network
    install -m 0644 ${WORKDIR}/20-wired.network ${D}${systemd_unitdir}/network/20-wired.network
    # Enable wpa_supplicant@wlan0.service in multi-user.target.wants
    install -d ${D}${systemd_system_unitdir}/multi-user.target.wants
    ln -sf ../wpa_supplicant@.service ${D}${systemd_system_unitdir}/multi-user.target.wants/wpa_supplicant@wlan0.service
}

FILES:${PN} += " \
    ${sbindir}/rpi-wifi-autoconfig.sh \
    ${systemd_system_unitdir}/rpi-wifi-autoconfig.service \
    ${systemd_system_unitdir}/multi-user.target.wants/wpa_supplicant@wlan0.service \
    ${sysconfdir}/wpa_supplicant/wpa_supplicant-wlan0.conf \
    ${systemd_unitdir}/network/25-wlan.network \
    ${systemd_unitdir}/network/20-wired.network \
"
