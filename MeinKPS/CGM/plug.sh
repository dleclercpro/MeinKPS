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
#    Overview: This script can be used to plug the CGM.
#
#    Notes:    ...
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Unplugging USB serial devices
sudo modprobe -r usbserial

# Give user info
echo "Plugging CGM..."

# Plug CGM
sudo modprobe usbserial vendor=0x22A3 product=0x0047