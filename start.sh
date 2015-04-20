#!/bin/bash

# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev

#Check local variables are set
locale

# build directory tree in data folder
mkdir -p /data && cd /data && mkdir -p db images snapshots tickets rabbitmq

# Mount USB storage
mount /dev/sda1 /mnt && chmod 775 /mnt

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf