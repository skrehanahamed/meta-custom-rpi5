SUMMARY = "TigerVNC Remote Desktop service for headless Raspberry Pi 5"
DESCRIPTION = "Launches an Xvnc server on display :1 (port 5901) with Openbox window manager"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://tigervnc.service \
    file://xstartup \
    file://setup-vnc-password.sh \
"

inherit systemd

SYSTEMD_PACKAGES = "${PN}"
SYSTEMD_SERVICE:${PN} = "tigervnc.service"
SYSTEMD_AUTO_ENABLE = "enable"

RDEPENDS:${PN} += " \
    tigervnc \
    openbox \
    xterm \
    xhost \
    xrandr \
    xauth \
    xorg-minimal-fonts \
    systemd \
"

do_install() {
    # Install systemd service
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/tigervnc.service ${D}${systemd_system_unitdir}/tigervnc.service

    # Install xstartup template in /etc/skel/.vnc and /root/.vnc
    install -d ${D}${sysconfdir}/skel/.vnc
    install -m 0755 ${WORKDIR}/xstartup ${D}${sysconfdir}/skel/.vnc/xstartup

    install -d ${D}/root/.vnc
    install -m 0755 ${WORKDIR}/xstartup ${D}/root/.vnc/xstartup

    # Install password configuration script
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/setup-vnc-password.sh ${D}${bindir}/setup-vnc-password.sh

    # Export DISPLAY=:1 and QT_QPA_PLATFORM=xcb for interactive shells
    install -d ${D}${sysconfdir}/profile.d
    cat << 'EOF' > ${D}${sysconfdir}/profile.d/vnc-display.sh
export DISPLAY=:1
export QT_QPA_PLATFORM=xcb
EOF
    chmod 0755 ${D}${sysconfdir}/profile.d/vnc-display.sh
}

FILES:${PN} += " \
    ${systemd_system_unitdir}/tigervnc.service \
    ${sysconfdir}/skel/.vnc/xstartup \
    /root/.vnc/xstartup \
    ${bindir}/setup-vnc-password.sh \
    ${sysconfdir}/profile.d/vnc-display.sh \
"
