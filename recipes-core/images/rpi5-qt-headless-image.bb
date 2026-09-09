SUMMARY = "Raspberry Pi 5 Headless Qt6 IVI Image with TigerVNC, Auto-WiFi, Bluetooth, Touch & OpenSSH"
DESCRIPTION = "A fully featured, headless Linux image designed for Raspberry Pi 5 to run Qt6 IVI \
applications remotely over TigerVNC or locally on Touchscreens with Bluetooth, Audio, and CAN bus."
LICENSE = "MIT"

inherit core-image

# Image features
IMAGE_FEATURES += " \
    splash \
    ssh-server-openssh \
    package-management \
    debug-tweaks \
"

# Set hostname to 'raspberrypi5' so it advertises as 'raspberrypi5.local' via mDNS
hostname:pn-base-files = "raspberrypi5"

# Core packages
IMAGE_INSTALL:append = " \
    packagegroup-core-boot \
    linux-firmware-rpidistro-bcm43455 \
    linux-firmware-rpidistro-bcm43430 \
    bluez-firmware-rpidistro-bcm4345c0-hcd \
    bluez5 \
    bluez5-noinst-tools \
    iw \
    wpa-supplicant \
    rpi-wifi-autoconfig \
    openssh \
    openssh-sftp-server \
    avahi-daemon \
    avahi-utils \
    libnss-mdns \
    iproute2 \
    curl \
    wget \
    htop \
    tzdata \
    tslib \
    tslib-conf \
    tslib-calibrate \
    tslib-tests \
    libinput \
    libinput-bin \
    evtest \
    mtdev \
    tigervnc \
    rpi-tigervnc-service \
    openbox \
    xterm \
    xhost \
    xauth \
    xrandr \
    xorg-minimal-fonts \
    fontconfig \
    ttf-dejavu-sans \
    ttf-dejavu-sans-mono \
    alsa-utils \
    pipewire \
    wireplumber \
    pipewire-spa-plugins-bluez5 \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    faad2 \
    can-utils \
    qtbase \
    qtbase-plugins \
    qtbase-tools \
    qtdeclarative \
    qtdeclarative-tools \
    qtdeclarative-qmlplugins \
    qtquick3d \
    qtsvg \
    qtsvg-plugins \
    qtconnectivity \
    qtmultimedia \
    qtserialbus \
    qtvirtualkeyboard \
    qtvirtualkeyboard-plugins \
    qtvirtualkeyboard-qmlplugins \
    qtwayland \
    qtwayland-plugins \
    libxkbcommon \
    qt6-sample-app \
"

# Allocate extra rootfs space (approx 2GB free for user IVI apps and assets)
IMAGE_ROOTFS_EXTRA_SPACE = "2097152"
