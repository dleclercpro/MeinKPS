#! /bin/bash

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    Title:    reset
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

# Raspberry Pi 1 on Raspbian Wheezy
FILE=/sys/devices/platform/bcm2708_usb/buspower

# Raspberry Pi 2 on Raspbian Jessie
if [ ! -e $FILE ]; then
    FILE=/sys/devices/platform/soc/3f980000.usb/buspower
fi

# Raspberry Pi 1 on Raspbian Jessie
if [ ! -e $FILE ]; then
    FILE=/sys/devices/platform/soc/20980000.usb/buspower
fi

# If power bus found
if [ -e $FILE ]; then

    # Info
    echo "Power-cycling USB devices..."

    # Info
    echo "Powering off..."

    # Power off
    sudo echo 0 > $FILE

    # Wait...
    sleep 1

    # Info
    echo "Powering on..."

    # Power on
    sudo echo 1 > $FILE

    # Wait...
    sleep 2

# Otherwise
else

    # Info
    echo "Could not find a known USB power control device."

fi
