#!/bin/bash

# Enable i2c - needed for the Display-O-Tron HAT
modprobe i2c-dev

# Start resin-wifi-connect
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
./wifi-connect --clear=false &

echo ds1307 0x68 | tee /sys/class/i2c-adapter/i2c-1/new_device

./syncTime.sh &

echo "wifi script started, running gpio"

# At this point the WiFi connection has been configured and the device has
# internet - unless the configured WiFi connection is no longer available.

# Start the main application
python src/main.py

wait
