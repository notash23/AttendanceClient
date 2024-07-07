#!/usr/bin/bash

echo "fbtft_device" > /etc/modules-load.d/fbtft.conf
echo "options fbtft_device custom name=fb_ili9488 busnum=1 cs=1 gpios=reset:73,dc:70,led:69 rotate=90 speed=65000000 bgr=1 txbuflen=65536" > /etc/modprobe.d/fbtft.conf
echo "Section \"Device\"
	Identifier \"myfb\"
	Driver \"fbdev\"
	Option \"fbdev\" \"/dev/fb1\"
EndSection" > /usr/share/X11/xorg.conf.d/99-fbdev.conf

sudo apt update
sudo apt install -y python3-pip libopencv-dev python3-opencv
pip install numpy pyzbar OPi.GPIO
