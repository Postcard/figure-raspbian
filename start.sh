#!/bin/bash

echo 'Starting Figure app'


# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev


# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/pictures

# Make sure $HOSTNAME is present in /etc/hosts
grep -q "$HOSTNAME" /etc/hosts || echo "127.0.0.1 $HOSTNAME" >> /etc/hosts

mkdir -p /data/log && touch /data/log/figure.log && touch /data/log/wifi-connect.log

# Start Xvfb
/etc/init.d/xvfb start

# Start Wifi Access Point if WIFI_ON
if [ "$WIFI_ON" = 1 ]; then

    node /usr/src/wifi-connect/src/app.js --clear=false >> /data/log/wifi-connect.log 2>&1 &
fi

if [  -f /var/run/supervisor.sock ]
then
    unlink /var/run/supervisor.sock
fi

# lock supervisor update by default
#lockfile /data/resin-updates.lock

# mount RAM disk
mkdir -p /mnt/ramdisk
mount -t tmpfs -o size=2m tmpfs /mnt/ramdisk

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf