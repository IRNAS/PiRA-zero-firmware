#!/bin/bash

# Generate WiFi AP configuration.
HOSTAPD_CONFIG="/etc/hostapd/hostapd.conf"
HOSTAPD_DEFAULTS_CONFIG="/etc/default/hostapd"
UDHCPD_CONFIG="/etc/udhcpd.conf"
UDHCPD_DEFAULTS_CONFIG="/etc/default/udhcpd"
INTERFACE_CONFIG="/etc/network/interfaces.d/wlan0"

# Hostapd config.
echo "interface=wlan0
driver=nl80211
ssid=${WIFI_SSID}
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${WIFI_PASSWORD}
wpa_key_mgmt=WPA-PSK
" > ${HOSTAPD_CONFIG}

echo "DAEMON_CONF=\"${HOSTAPD_CONFIG}\"" > ${HOSTAPD_DEFAULTS_CONFIG}

# Udhcpd config.
echo "start 172.22.0.10
end 172.22.0.254
interface wlan0
remaining yes
opt dns 8.8.8.8 4.2.2.2
opt subnet 255.255.255.0
opt router 172.22.0.1
opt lease 86400
" > ${UDHCPD_CONFIG}

echo "DHCPD_OPTS=\"-S\"" > ${UDHCPD_DEFAULTS_CONFIG}

# Interfaces config.
echo "allow-hotplug wlan0
iface wlan0 inet static
    address 172.22.0.1
    netmask 255.255.255.0
" > ${INTERFACE_CONFIG}

# Start networking services.
systemctl start dhcpcd.service
systemctl start networking.service
systemctl start avahi-daemon.service
systemctl start ssh.service
systemctl start hostapd.service
systemctl start udhcpd.service
