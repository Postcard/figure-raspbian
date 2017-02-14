#!/bin/bash

echo 'Starting Figure app'

if [[ $DD_API_KEY ]];
then
    sed -i -e "s/^.*api_key:.*$/api_key: ${DD_API_KEY}/" ~/.datadog-agent/agent/datadog.conf
    if [  -f /root/.datadog-agent/run/agent-supervisor.sock ]
    then
        unlink /root/.datadog-agent/run/agent-supervisor.sock
    fi
    # The agent needs to be executed with the current working directory set datadog-agent directory
    cd /root/.datadog-agent
    ./bin/agent start &
else
    echo "You must set DD_API_KEY environment variable to run the Datadog Agent container"
fi


# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev


# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/pictures

# Make sure $HOSTNAME is present in /etc/hosts
grep -q "$HOSTNAME" /etc/hosts || echo "127.0.0.1 $HOSTNAME" >> /etc/hosts


# Start Wifi Access Point if WIFI_ON
if [ "$WIFI_ON" = 1 ]; then

    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket

    sleep 1 # Delay needed to avoid DBUS introspection errors

    node /usr/src/wifi-connect/src/app.js --clear=false &
fi

if [  -f /var/run/supervisor.sock ]
then
    unlink /var/run/supervisor.sock
fi

# lock supervisor update by default
lockfile /data/resin-updates.lock

mkdir -p /data/log && touch /data/log/figure.log

# mount RAM disk
mkdir -p /mnt/ramdisk
mount -t tmpfs -o size=2m tmpfs /mnt/ramdisk

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf