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
#    Overview: This script can be used to power-cycle the Raspberry Pi USB bus
#              in order to reset the attached USB devices.
#
#    Notes:    ...
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Plug stick
sudo modprobe usbserial vendor=0x0a21 product=0x8001
