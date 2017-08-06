#! /bin/bash

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    Title:    plug
#
#    Author:   David Leclerc
#
#    Version:  0.1
#
#    Date:     19.06.2017
#
#    License:  GNU General Public License, Version 3
#              (http://www.gnu.org/licenses/gpl.html)
#
#    Overview: This script can be used to plug the stick.
#
#    Notes:    ...
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Unplugging usb-serial devices
sudo modprobe -r usbserial

# Give user info
echo "Plugging stick..."

# Plug stick
sudo modprobe usbserial vendor=0x0a21 product=0x8001
