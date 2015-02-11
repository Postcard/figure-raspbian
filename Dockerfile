# Base image 
FROM resin/rpi-raspbian:wheezy-2015-01-15

MAINTAINER Benoit Guigal <benoit@postcardgroup.com>

# Make sure installation is not asking for prompt 
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python \
    python-dev \
    python-setuptools \
    wget \
    bzip2 \
    gcc \
    g++ \
    make \
    pkg-config

RUN wget --no-check-certificate https://github.com/gonzalo/gphoto2-updater/releases/download/2.5.5/gphoto2-updater.sh && \
    chmod +x gphoto2-updater.sh && \
    ./gphoto2-updater.sh


RUN apt-get install -y unzip tar libfreetype6 libfontconfig
RUN wget --no-check-certificate https://github.com/aeberhardo/phantomjs-linux-armv6l/archive/master.zip && \
    unzip master.zip && \
    cd phantomjs-linux-armv6l-master && \
    bunzip2 *.bz2 && \
    tar xf *.tar

RUN mkdir /figure

RUN apt-get install -y libjpeg-dev zlib1g-dev libpng12-dev unzip

RUN apt-get install -y python-pip
RUN pip install requests==2.5.1
RUN pip install selenium==2.44.0
RUN pip install gphoto2==0.11.0

RUN apt-get install -y usbutils

RUN wget --no-check-certificate https://github.com/benoitguigal/python-epson-printer/archive/v1.5.zip
RUN unzip v1.5.zip
RUN cd python-epson-printer-1.5 && python setup.py install

RUN wget --no-check-certificate https://github.com/piface/pifacecommon/archive/v4.1.2.zip
RUN unzip v4.1.2.zip
RUN cd pifacecommon-4.1.2 && python setup.py install

RUN wget --no-check-certificate https://github.com/piface/pifacedigitalio/archive/v3.0.4.zip
RUN unzip v3.0.4.zip
RUN cd pifacedigitalio-3.0.4 && python setup.py install


ADD figureraspbian /figure/figureraspbian
WORKDIR /figure
RUN mkdir -p var/snapshots
RUN touch var/ticket.png

CMD modprobe i2c-dev && python -m figureraspbian.trigger














