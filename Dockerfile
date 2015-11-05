# Base image 
FROM resin/rpi-raspbian:wheezy-2015-09-02

MAINTAINER Benoit Guigal <benoit@postcardgroup.com>

# Make sure installation is not asking for prompt 
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python \
    python-dev \
    python-setuptools \
    python-pip \
    pkg-config \
    gcc \
    g++ \
    make \
    unzip \
    tar \
    wget \
    bzip2 \
    rabbitmq-server \
    libjpeg-dev \
    zlib1g-dev \
    libpng12-dev \
    usbutils \
    libfreetype6 \
    libfontconfig \
    python-numpy \
    ntp \
    ntpdate

RUN wget --no-check-certificate https://github.com/gonzalo/gphoto2-updater/releases/download/2.5.8/gphoto2-updater.sh && \
    chmod +x gphoto2-updater.sh && \
    ./gphoto2-updater.sh

RUN wget --no-check-certificate https://github.com/aeberhardo/phantomjs-linux-armv6l/archive/master.zip && \
    unzip master.zip && \
    rm master.zip && \
    cd phantomjs-linux-armv6l-master && \
    bunzip2 *.bz2 && \
    tar xf *.tar

RUN wget --no-check-certificate https://github.com/benoitguigal/python-epson-printer/archive/v1.7.1.zip && \
    unzip v1.7.1.zip && \
    rm v1.7.1.zip && \
    cd python-epson-printer-1.7.1 && \
    python setup.py install

RUN pip install gphoto2==1.2.1 \
    requests==2.5.1 \
    Pillow==2.6.0 \
    pifacecommon==4.1.2 \
    pifacedigitalio==3.0.5 \
    jinja2==2.7.3 \
    persistent==4.0.8 \
    ZEO==4.1.0 \
    ZODB==4.1.0 \
    ZODB3==3.11.0 \
    pytz==2015.2 \
    celery==3.1.17 \
    Flask==0.10.1 \
    supervisor==3.1.3 \
    Django==1.8 \
    gunicorn==19.3.0 \
    python-dateutil==2.4.2 \
    hashids==1.1.0

RUN apt-get install -y git

RUN git clone https://github.com/petrkutalek/png2pos.git && \
    cd png2pos && \
    git submodule init && \
    git submodule update && \
    make install

ENV LANG C.UTF-8
ENV C_FORCE_ROOT true
ENV FIGURE_DIR /figure/figureraspbian
ENV IMAGE_DIR /data/images
ENV PHANTOMJS_PATH /phantomjs-linux-armv6l-master/phantomjs-1.9.0-linux-armv6l/bin/phantomjs
ENV STATIC_ROOT /data/static
ENV MEDIA_ROOT /data/media
ENV ZEO_SOCKET /var/run/zeo.sock
ENV PNG2POS_PRINTER_MAX_WIDTH 576

COPY figureraspbian /figureraspbian
COPY ./start.sh /
COPY ./supervisord.conf /etc/

RUN mkdir -p /var/log /var/run && chmod 755 /start.sh

CMD ["/bin/bash", "/start.sh"]











