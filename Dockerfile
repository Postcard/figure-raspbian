FROM resin/rpi-raspbian:wheezy-2015-01-15
MAINTAINER Benoit Guigal <benoit@postcardgroup.com>
RUN apt-get update 
RUN apt-get install python-dev
RUN apt-get install git

