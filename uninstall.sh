#!/usr/bin/bash

# Remove LCD setup files
rm /etc/modules-load.d/fbtft.conf
rm /etc/modprobe.d/fbtft.conf
rm /usr/share/X11/xorg.conf.d/99-fbdev.conf

# Restart the device
sudo reboot
