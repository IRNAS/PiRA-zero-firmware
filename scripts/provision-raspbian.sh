#!/bin/bash -e

work_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )

# Install needed system package dependencies.
apt-get update
apt-get install -y i2c-tools python-smbus pigpio libfreetype6-dev libjpeg-dev hostapd udhcpd python-rpi.gpio python-pigpio python-future python-serial python-dateutil python-picamera python-numpy python-crypto python-requests python-yaml python-pip

# Install needed Python dependencies.
pip install astral

# Install services.
cp ${work_dir}/scripts/pira.service /lib/systemd/system/pira.service
systemctl --system daemon-reload
systemctl reenable pira.service

# Optimize boot time by disabling some services.
systemctl disable dhcpcd.service
systemctl disable networking.service
systemctl disable keyboard-setup.service
systemctl disable avahi-daemon.service
systemctl disable ssh.service
systemctl disable bluetooth.service
systemctl disable hostapd.service
systemctl disable udhcpd.service
systemctl disable hciuart
