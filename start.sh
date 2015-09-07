#!/bin/bash

# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev

# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/snapshots

# Mount USB stick if BACKUP is activated
if [ "$BACKUP_ON" = 1 ] ; then
    mount /dev/sda1 /mnt && chmod 775 /mnt
fi

# Grap the correct time
/etc/init.d/ntp stop
ntpdate -s time.nist.gov
/etc/init.d/ntp start

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf