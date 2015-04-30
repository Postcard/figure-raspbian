#!/bin/bash

# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev

# create data directories
mkdir -p /data/tickets /data/images /data/snapshots /data/resources

# Install Real Time Clock
chmod +x /install-piface-real-time-clock.sh
/install-piface-real-time-clock.sh
lsmod
hwclock -r
date

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf