#!/usr/bin/bash

# Remove LCD setup files
rm /etc/modules-load.d/fbtft.conf
rm /etc/modprobe.d/fbtft.conf
rm /usr/share/X11/xorg.conf.d/99-fbdev.conf

# Change apt sources
cp /etc/apt/sources.list.bak /etc/apt/sources.list
rm /etc/apt/sources.list.bak

# Uninstall libraries
apt purge -y python3-pip libopencv-dev python3-opencv libzbar0
pip3 uninstall numpy pyzbar

# Remove autostart files
rm /home/orangepi/.config/autostart/AttendanceClient.desktop

# Show mouse cursor
cp /etc/lightdm/lightdm.conf.d/11-orangepi.conf.bak /etc/lightdm/lightdm.conf.d/11-orangepi.conf
rm /etc/lightdm/lightdm.conf.d/11-orangepi.conf.bak

# Remove authentication details
rm "$PWD"/resources/authData.json

# Restart the device
shutdown now
