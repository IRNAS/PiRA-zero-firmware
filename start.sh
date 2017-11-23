#!/bin/bash

# Enable i2c - needed for the Display-O-Tron HAT
modprobe i2c-dev

# Enable camera driver.
modprobe bcm2835-v4l2

# Setup host DBUS socket location, which is needed for NetworkManager.
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket

# Power off HDMI.
tvservice -o

# Sync clock from RTC module.
./scripts/sync_time.sh

# Start the pigpio daemon.
systemctl start pigpiod

# Start the main application.
python -m pira.main
