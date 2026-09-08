# ==============================================================================
# Dockerfile for Yocto Scarthgap Build Environment on macOS / Linux
# ==============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install all standard Yocto Project host build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    chrpath \
    cpio \
    curl \
    diffstat \
    file \
    gawk \
    gcc \
    git \
    iputils-ping \
    libegl1-mesa \
    liblz4-tool \
    libsdl1.2-dev \
    locales \
    mesa-common-dev \
    pylint \
    python3 \
    python3-git \
    python3-jinja2 \
    python3-pexpect \
    python3-pip \
    python3-subunit \
    rsync \
    socat \
    sudo \
    texinfo \
    tmux \
    unzip \
    vim \
    wget \
    xterm \
    xz-utils \
    zstd \
    bc \
    libncurses5-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up UTF-8 locale (mandatory for BitBake)
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Create build user with sudo access (BitBake refuses to run as root)
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN (getent group ${GROUP_ID} || groupadd -g ${GROUP_ID} yocto) && \
    (getent passwd ${USER_ID} || useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash yocto) && \
    echo "yocto ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER yocto
WORKDIR /workspace

CMD ["/bin/bash"]
