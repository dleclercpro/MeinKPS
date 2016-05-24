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
LOGS_ADDRESS    = "./stickLogs.txt"
NOW             = datetime.datetime.now()



class pump:

    # PUMP CHARACTERISTICS
    SERIAL_NUMBER   = 574180
    SLEEP_TIME      = 12



    def getStick(self):

        """
        ========================================================================
        GETSTICK
        ========================================================================

        ...
        """

        # Instanciate a stick
        self.stick = controlStick.stick()



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
        self.packet_serial_number = [ord(x) for x in
            str(self.SERIAL_NUMBER).decode("hex")]
        self.packet_parameters_info = [128 |
            lib.getByte(len(self.packet_parameters), 1),
            lib.getByte(len(self.packet_parameters), 0)]

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

        # Specify packet parameters for command
        self.packet_button = 85
        self.packet_attempts = 0
        self.packet_pages = 0
        self.packet_code = 93
        self.packet_parameters = [1, 10]

        # Send packet to pump
        self.sendPacket()

        # Sleep until pump is powered up
        print "Sleeping until pump is powered up..."

        time.sleep(self.SLEEP_TIME)

        # Get data sent back from pump
        self.stick.getData()



    def getModel(self):

        """
        ========================================================================
        GETMODEL
        ========================================================================

        ...
        """

        # Specify packet parameters for command
        self.packet_button = 85
        self.packet_attempts = 0
        self.packet_pages = 0
        self.packet_code = 93
        self.packet_parameters = [1, 10]

        # Send packet to pump
        self.sendPacket()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a pump for me
    my_pump = pump()

    # Instanciate a stick for my pump
    my_pump.getStick()

    # Start stick
    my_pump.stick.start()

    # Get state of USB side of stick
    my_pump.stick.getUSBState()

    # Get state of radio transmitter side of stick
    my_pump.stick.getRFState()

    # Power up my pump
    my_pump.powerUp()

    # Stop my stick
    my_pump.stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
