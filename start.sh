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
mkdir -p /data/static /data/media/tickets /data/media/images /data/media/snapshots

# Make sure $HOSTNAME is present in /etc/hosts
grep -q "$HOSTNAME" /etc/hosts || echo "127.0.0.1 $HOSTNAME" >> /etc/hosts


# Start Wifi Access Point if WIFI_ON
if [ "$WIFI_ON" = 1 ]; then
    cd /usr/src/app && npm start &
fi

if [  -f /var/run/supervisor.sock ]
then
    unlink /var/run/supervisor.sock
fi

# tune redis configuration file to store data in /data directory
sed -i -e '/dir / s, /var/lib/redis/6379*, /data,' /etc/redis/6379.conf

# Launch supervisor in the foreground
echo 'Starting supervisor'
supervisord --nodaemon --configuration /etc/supervisord.conf