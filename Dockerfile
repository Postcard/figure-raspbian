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


RUN mkdir /figure
WORKDIR /figure

ADD setup.py /figure/setup.py
ADD figureraspbian /figure/figureraspbian

RUN python setup.py install












