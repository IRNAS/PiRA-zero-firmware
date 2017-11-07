#!/bin/bash

# Enable i2c - needed for the Display-O-Tron HAT
modprobe i2c-dev && python src/main.py &

# Start resin-wifi-connect
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
./wifi-connect --clear=false

echo "test"

# At this point the WiFi connection has been configured and the device has
# internet - unless the configured WiFi connection is no longer available.
