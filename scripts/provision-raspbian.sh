#!/bin/bash -e

work_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )

# Install needed system package dependencies.
apt-get update
apt-get install -y i2c-tools python-smbus pigpio libfreetype6-dev libjpeg-dev hostapd udhcpd python-rpi.gpio python-pigpio python-future python-serial python-dateutil python-picamera python-numpy python-crypto python-requests python-yaml

# Install services.
cp ${work_dir}/scripts/pira.service /lib/systemd/system/pira.service
systemctl --system daemon-reload
systemctl enable pira.service

