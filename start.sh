#!/bin/bash

# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev

# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/snapshots

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf