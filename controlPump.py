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
    PUMP_SERIAL_NUMBER  = 574180
    POWERUP_TIME        = 10
    SLEEP_TIME          = 0.1



    def start(self):

        """
        ========================================================================
        START
        ========================================================================

        ...
        """

        # Instanciate a stick to communicate with the pump
        self.stick = controlStick.stick()

        # Start stick
        self.stick.start()

        # Get state of USB side of stick
        self.stick.getState()

        # Power up my pump
        self.powerUp()



    def powerUp(self):

        """
        ========================================================================
        POWERUP
        ========================================================================

        ...
        """

        # Specify packet parameters for command
        self.stick.packet_button = 85
        self.stick.packet_attempts = 0
        self.stick.packet_pages = 0
        self.stick.packet_code = 93
        self.stick.packet_parameters = [1, 10]

        # Send packet to pump
        self.stick.sendPumpPacket()

        # Wait for response from pump
        print "Sleep until pump is powered up... " + \
              "(" + str(self.POWERUP_TIME) + "s)"
        time.sleep(self.POWERUP_TIME)



    def readModel(self):

        """
        ========================================================================
        READMODEL
        ========================================================================

        ...
        """

        # Specify packet parameters for command
        self.stick.packet_button = 0
        self.stick.packet_attempts = 2
        self.stick.packet_pages = 1
        self.stick.packet_code = 141
        self.stick.packet_parameters = []

        # Send packet to pump
        self.stick.sendPumpPacket()

        # Wait for response from pump
        print "Sleep until pump responds... " + \
              "(" + str(self.SLEEP_TIME) + "s)"
        time.sleep(self.SLEEP_TIME)

        # Get data sent back from pump
        self.stick.getPumpData()



    def sendBolus(self, bolus):

        """
        ========================================================================
        SENDBOLUS
        ========================================================================

        ...
        """

        # Specify packet parameters for command
        self.stick.packet_button = 0
        self.stick.packet_attempts = 0
        self.stick.packet_pages = 1
        self.stick.packet_code = 66
        self.stick.packet_parameters = [
            int(bolus * 10) # Bolus are 0.1 units
            ]

        # Send packet to pump
        self.stick.sendPumpPacket()



    def setTemporaryBasalPercent(self, rate, duration):

        """
        ========================================================================
        SETTEMPORARYBASALPERCENT
        ========================================================================

        ...
        """

        # Specify packet parameters for command
        self.stick.packet_button = 0
        self.stick.packet_attempts = 0
        self.stick.packet_pages = 1
        self.stick.packet_code = 105
        self.stick.packet_parameters = [
            int(rate),          # Rate is set in percentage
            int(duration / 30)  # Duration is splitted in blocks of 30 minutes
            ]

        # Send packet to pump
        self.stick.sendPumpPacket()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a pump for me
    my_pump = pump()

    # Start pump
    my_pump.start()

    # Read pump model
    my_pump.readModel()

    # Send bolus to pump
    #my_pump.sendBolus(0.5)
    my_pump.setTemporaryBasalPercent(50, 90)

    # Stop my stick
    my_pump.stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
