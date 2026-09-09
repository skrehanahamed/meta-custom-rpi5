FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://50-default-volume.conf"

do_install:append() {
    install -d ${D}${sysconfdir}/wireplumber/wireplumber.conf.d
    install -m 0644 ${WORKDIR}/50-default-volume.conf ${D}${sysconfdir}/wireplumber/wireplumber.conf.d/50-default-volume.conf
}

FILES:${PN} += "${sysconfdir}/wireplumber/wireplumber.conf.d/50-default-volume.conf"
