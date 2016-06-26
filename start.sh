#!/bin/bash

echo 'Starting Figure app'


# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev

# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/snapshots

# Mount USB storage
mount /dev/sda1 /mnt && chmod 775 /mnt

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf