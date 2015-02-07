# Base image 
FROM resin/rpi-raspbian:wheezy-2015-01-15

MAINTAINER Benoit Guigal <benoit@postcardgroup.com>

# Make sure installation is not asking for prompt 
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update 

RUN apt-get -y install python-dev
RUN apt-get -y install python-pip 


# Install phantomJS
RUN wget https://github.com/aeberhardo/phantomjs-linux-armv6l/archive/master.zip
RUN unzip master.zip
RUN cd phantomjs-linux-armv6l-master 
RUN bunzip2 *.bz2 && tar xf *.tar 


RUN apt-get -y install git

