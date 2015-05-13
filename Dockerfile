# Base image 
FROM resin/rpi-raspbian:wheezy-2015-05-06

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
    nginx \
    libjpeg-dev \
    zlib1g-dev \
    libpng12-dev \
    usbutils \
    libfreetype6 \
    libfontconfig

RUN wget --no-check-certificate https://github.com/Postcard/gphoto2-updater/releases/download/2.5.8/gphoto2-updater.sh && \
    chmod +x gphoto2-updater.sh && \
    ./gphoto2-updater.sh

RUN wget --no-check-certificate https://github.com/aeberhardo/phantomjs-linux-armv6l/archive/master.zip && \
    unzip master.zip && \
    rm master.zip && \
    cd phantomjs-linux-armv6l-master && \
    bunzip2 *.bz2 && \
    tar xf *.tar

RUN wget --no-check-certificate https://github.com/benoitguigal/python-epson-printer/archive/v1.6.zip && \
    unzip v1.6.zip && \
    rm v1.6.zip && \
    cd python-epson-printer-1.6 && \
    python setup.py install

RUN pip install gphoto2==1.1.0 \
    requests==2.5.1 \
    Pillow==2.6.0 \
    selenium==2.44.0 \
    pifacecommon==4.1.2 \
    pifacedigitalio==3.0.5 \
    jinja2==2.7.3 \
    persistent==4.0.8 \
    ZODB==4.1.0 \
    ZODB3==3.11.0 \
    pytz==2015.2 \
    celery==3.1.17 \
    Flask==0.10.1 \
    supervisor==3.1.3 \
    Django==1.8

ENV LANG C.UTF-8
ENV C_FORCE_ROOT true
ENV FIGURE_DIR /figure/figureraspbian
ENV IMAGE_DIR /data/images
ENV PHANTOMJS_PATH /phantomjs-linux-armv6l-master/phantomjs-1.9.0-linux-armv6l/bin/phantomjs
ENV RESOURCE_DIR /data/resources
ENV SNAPSHOT_DIR /data/snapshots
ENV TICKET_DIR /data/tickets
ENV ZEO_SOCKET /var/run/zeo.sock
ENV TICKET_CSS_URL http://localhost/ticket.css
ENV TICKET_HTML_URL http://localhost/ticket.html

COPY figureraspbian /figureraspbian
COPY ./start.sh /
COPY ./supervisord.conf /etc/
RUN rm -v /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN mkdir -p /var/log /var/run && chmod 755 /start.sh

CMD ["/bin/bash", "/start.sh"]











