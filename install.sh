#!/usr/bin/bash

# Check if the correct Kernel version is installed
KERNEL_VERSION=$(hostnamectl | grep 'Kernel:' | sed 's/^.*: //' | awk -F- '{print$1}' | awk -F. 'OFS="." { print $1, $2 }')
if [[ $KERNEL_VERSION != "Linux 4.9" ]]; then
  echo 'Linux Version Error: Should be using kernel version 4.9'
  exit
fi

# LCD screen setup
echo "fbtft_device" >/etc/modules-load.d/fbtft.conf
echo "options fbtft_device custom name=fb_ili9488 busnum=1 cs=1 gpios=reset:73,dc:70,led:69 rotate=270 speed=65000000 bgr=1 txbuflen=65536" >/etc/modprobe.d/fbtft.conf
echo "Section \"Device\"
	Identifier \"myfb\"
	Driver \"fbdev\"
	Option \"fbdev\" \"/dev/fb1\"
EndSection" >/usr/share/X11/xorg.conf.d/99-fbdev.conf

# Change apt sources
cp /etc/apt/sources.list /etc/apt/sources.list.bak
echo "deb http://deb.debian.org/debian buster main contrib non-free
deb-src http://deb.debian.org/debian buster main contrib non-free

deb http://deb.debian.org/debian buster-updates main contrib non-free
deb-src http://deb.debian.org/debian buster-updates main contrib non-free

deb http://archive.debian.org/debian buster-backports main contrib non-free
deb-src http://archive.debian.org/debian buster-backports main contrib non-free

deb http://security.debian.org/debian-security/ buster/updates main contrib non-free
deb-src http://security.debian.org/debian-security/ buster/updates main contrib non-free" >/etc/apt/sources.list

# Python library installations
apt update
apt install -y python3-pip libopencv-dev python3-opencv libzbar0
pip3 install numpy pyzbar

# Start app up on boot
echo "[Desktop Entry]
Encoding=UTF-8
Type=Application
Name=Attendance Client
Comment=
Exec=python3 $(pwd)/main.py
StartupNotify=false
Terminal=true
Hidden=false" >/home/orangepi/.config/autostart/AttendanceClient.desktop # or /etc/xdg/autostart/AttendanceClient.desktop

# Hide mouse cursor
cp /etc/lightdm/lightdm.conf.d/11-orangepi.conf /etc/lightdm/lightdm.conf.d/11-orangepi.conf.bak
echo "xserver-command=X -bs -core -nocursor" >>/etc/lightdm/lightdm.conf.d/11-orangepi.conf

# Create dialog box to input authentication details
OUTPUT=$(zenity --forms --title="Authentication Data" --text="Enter Auth Details for the Attendance Client" --separator="|" --add-entry="ID" --add-entry="Auth Token")

accepted=$?
if ((accepted != 0)); then
    echo "WARNING: The Attendance Client might not work without the authentication data. Create it using the admin app."
    exit 1
fi

awk -F"|" '{ OFS="" } { print "{\n  \"id\": \"", $1, "\",\n  \"authToken\": \"", $2, "\"\n}" }' <<< "$OUTPUT" > "$PWD"/resources/authData.json

# Restart the device
shutdown now
