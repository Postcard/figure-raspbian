#!/bin/bash

echo 'Starting Figure app'

if [[ $DD_API_KEY ]];
then
    sed -i -e "s/^.*api_key:.*$/api_key: ${DD_API_KEY}/" ~/.datadog-agent/agent/datadog.conf
    # The agent needs to be executed with the current working directory set datadog-agent directory
    unlink /root/.datadog-agent/run/agent-supervisor.sock
    cd /root/.datadog-agent
    ./bin/agent start &
else
    echo "You must set DD_API_KEY environment variable to run the Datadog Agent container"
fi


# Enable I2C. See http://docs.resin.io/#/pages/i2c-and-spi.md for more details
modprobe i2c-dev


# create data directories
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/snapshots

# Make sure $HOSTNAME is present in /etc/hosts
grep -q "$HOSTNAME" /etc/hosts || echo "127.0.0.1 $HOSTNAME" >> /etc/hosts


# Start Wifi Access Point for three minutes if WIFI_ON
if [ "$WIFI_ON" = 1 ]; then
    cd /usr/src/app && timeout 3m npm start
fi

unlink /var/run/supervisor.sock

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf