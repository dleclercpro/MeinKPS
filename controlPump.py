#! /usr/bin/python



"""
================================================================================
TITLE:    controlPump

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     24.05.2016

LICENSE:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

OVERVIEW: ...

NOTES:    ...
================================================================================
"""



# LIBRARIES
import os
import sys
import time
import datetime
import numpy as np



# USER LIBRARIES
import lib
import controlStick



# DEFINITIONS
LOGS_ADDRESS                = "./stickLogs.txt"
NOW                         = datetime.datetime.now()



class pump:

    # PUMP CHARACTERISTICS
    SERIAL_NUMBER           = 574180
    SLEEP_TIME              = 12



    def getStick(self):

        """
        ========================================================================
        GETSTICK
        ========================================================================

        ...
        """

        # Instanciate a stick
        stick = controlStick.stick()



    def preparePacket(self):

        """
        ========================================================================
        PREPAREPACKET
        ========================================================================

        ...
        """

        # Initialize packet to send to pump
        self.packet = []

        # Evaluate some parts of packet based on input
        self.packet_head = [1, 0, 167, 1]
        self.packet_serial_number = [ord(x) for x in \
                                     str(self.SERIAL_NUMBER).decode("hex")]
        self.packet_parameters_info = [128 |
                                       getByte(len(self.packet_parameters), 1),
                                       getByte(len(self.packet_parameters), 0)]

        # Build said packet
        self.packet.extend(self.packet_head)
        self.packet.extend(self.packet_serial_number)
        self.packet.extend(self.packet_parameters_info)
        self.packet.append(self.packet_button)
        self.packet.append(self.packet_attempts)
        self.packet.append(self.packet_pages)
        self.packet.append(0)
        self.packet.append(self.packet_code)
        self.packet.append(lib.computeCRC8(self.packet))
        self.packet.extend(self.packet_parameters)
        self.packet.append(lib.computeCRC8(self.packet_parameters))



    def sendPacket(self):

        """
        ========================================================================
        SENDPACKET
        ========================================================================

        ...
        """

        # Prepare packet to send to pump
        self.preparePacket()

        # Send packet through stick
        self.stick.sendRequest(self.packet)



    def powerUp(self):

        """
        ========================================================================
        POWERUP
        ========================================================================

        ...
        """

        # Power up the pump
        self.packet_button = 85
        self.packet_attempts = 0
        self.packet_pages = 0
        self.packet_code = 93
        self.packet_parameters = [1, 10]

        # Send packet to pump
        self.sendPacket()

        # Sleep until pump is powered up
        time.sleep(self.SLEEP_TIME)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a pump for me
    my_pump = pump()

    # Start my stick
    my_pump.powerUp()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
