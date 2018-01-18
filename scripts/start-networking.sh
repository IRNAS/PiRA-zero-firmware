#!/bin/bash

# Start networking services.
systemctl start dhcpcd.service
systemctl start networking.service
systemctl start avahi-daemon.service
systemctl start ssh.service
systemctl start hostapd.service
systemctl start udhcpd.service
