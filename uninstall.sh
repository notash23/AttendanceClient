#!/usr/bin/bash

# Remove LCD setup files
rm /etc/modules-load.d/fbtft.conf
rm /etc/modprobe.d/fbtft.conf
rm /usr/share/X11/xorg.conf.d/99-fbdev.conf

# Uninstall libraries
sudo apt purge -y libopencv-dev python3-opencv
pip uninstall numpy pyzbar OPi.GPIO

# Remove autostart files
rm /home/orangepi/.config/autostart/AttendanceClient.desktop

# Restart the device
sudo reboot
