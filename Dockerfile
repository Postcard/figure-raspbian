# Base image 
FROM resin/rpi-raspbian:wheezy-2015-01-15

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
    wget


RUN wget --no-check-certificate https://github.com/Postcard/gphoto2-updater/archive/master.zip && \
    unzip master.zip && \
    rm master.zip && \
    cd gphoto2-updater-master && \
    chmod +x gphoto2-updater.sh && \
    ./gphoto2-updater.sh


RUN pip install gphoto2==1.1.0

RUN apt-get install -y \
    bzip2 \
    rabbitmq-server \
    libjpeg-dev \
    zlib1g-dev \
    libpng12-dev \
    usbutils \
    libfreetype6 \
    libfontconfig


RUN wget --no-check-certificate https://github.com/aeberhardo/phantomjs-linux-armv6l/archive/master.zip && \
    unzip master.zip && \
    cd phantomjs-linux-armv6l-master && \
    bunzip2 *.bz2 && \
    tar xf *.tar

RUN mkdir /figure

RUN pip install requests==2.5.1
RUN pip install Pillow==2.7.0
RUN pip install selenium==2.44.0
RUN pip install pifacecommon==4.1.2
RUN pip install pifacedigitalio==3.0.5
RUN pip install jinja2==2.7.3
RUN pip install hashids==1.0.3
RUN pip install persistent==4.0.8
RUN pip install ZODB==4.1.0
RUN pip install ZODB3==3.11.0
RUN pip install pytz==2015.2
RUN pip install celery==3.1.17

RUN wget --no-check-certificate https://github.com/benoitguigal/python-epson-printer/archive/v1.6.zip
RUN unzip v1.6.zip
RUN cd python-epson-printer-1.6 && python setup.py install


ADD figureraspbian /figure/figureraspbian
WORKDIR /figure
RUN mkdir -p media/images media/snapshots media/tickets resources 
RUN mkdir -p /var
RUN cd /var && mkdir -p run log data images snapshots tickets

RUN pip install supervisor

ADD ./start.sh /start.sh
RUN chmod 755 /start.sh

ADD ./supervisord.conf /etc/supervisord.conf

CMD ["/bin/bash", "/start.sh"]











