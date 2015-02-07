FROM resin/rpi-raspbian:wheezy-2015-01-15
MAINTAINER Benoit Guigal <benoit@postcardgroup.com>
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update 
RUN apt-get -y install python-dev
RUN apt-get -y install python-pip 
RUN apt-get -y install git

