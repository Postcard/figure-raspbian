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

# Make sure $HOSTNAME is present in /etc/hosts
if ! grep -q "$HOSTNAME" /etc/hosts ; then echo "127.0.0.1 $HOSTNAME" >> /etc/hosts; fi

# Start Wifi Access Point for three minutes if WIFI_ON
if [ "$WIFI_ON" = 1 ]; then
    cd /usr/src/app && timeout 3m npm start
fi

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf