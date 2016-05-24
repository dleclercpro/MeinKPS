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
    BOLUS_SPEED         = 40 # 1U takes 40 seconds to be enacted



    def start(self, do_power_up = True):

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

        # Power up if needed
        if do_power_up:

            # Power up the pump
            self.powerUp(10)



    def powerUp(self, duration):

        """
        ========================================================================
        POWERUP
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Powering up the pump..."

        # Specify request parameters for command
        self.stick.request_button = 85
        self.stick.request_attempts = 0
        self.stick.request_pages = 0
        self.stick.request_code = 93
        self.stick.request_parameters = [
            1,       # Default byte
            duration # Duration of RF session
            ]

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = False)

        # Wait for response from pump
        print "Sleeping until pump is powered up... " + \
              "(" + str(self.POWERUP_TIME) + "s)"

        time.sleep(self.POWERUP_TIME)

        # Give user info
        print "Pump powered up."



    def suspend(self):

        """
        ========================================================================
        SUSPEND
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Suspending pump activity..."

        # Specify request parameters for command
        self.stick.request_button = 0
        self.stick.request_attempts = 2
        self.stick.request_pages = 1
        self.stick.request_code = 77
        self.stick.request_parameters = []

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = False)

        # Give user info
        print "Pump activity suspended."



    def resume(self):

        """
        ========================================================================
        RESUME
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Resuming pump activity..."

        # Specify request parameters for command
        self.stick.request_button = 0
        self.stick.request_attempts = 2
        self.stick.request_pages = 1
        self.stick.request_code = 77
        self.stick.request_parameters = []

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = False)

        # Give user info
        print "Pump activity resumed."



    def readModel(self):

        """
        ========================================================================
        READMODEL
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Reading pump model..."

        # Specify request parameters for command
        self.stick.request_button = 0
        self.stick.request_attempts = 2
        self.stick.request_pages = 1
        self.stick.request_code = 141
        self.stick.request_parameters = []

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = True)

        # Extract pump model from received data
        self.model = int("".join(self.stick.response_str[14:17]))

        # Give user info
        print "Pump model obtained: " + str(self.model)



    def sendBolus(self, bolus):

        """
        ========================================================================
        SENDBOLUS
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Sending bolus: " + str(bolus) + "U"

        # Specify request parameters for command
        self.stick.request_button = 0
        self.stick.request_attempts = 0
        self.stick.request_pages = 1
        self.stick.request_code = 66
        self.stick.request_parameters = [
            int(bolus * 10) # Bolus are 0.1 units
            ]

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = False)

        # Evaluating time required for bolus to be enacted
        bolus_time = self.BOLUS_SPEED * bolus \
                     + 10 # Give it 10 more seconds to be safe

        # Give user info
        print "Waiting for bolus to be enacted... (" + \
              str(bolus_time) + "s)"

        time.sleep(bolus_time)

        # Give user info
        print "Bolus sent."



    def setTemporaryBasalPercent(self, rate, duration):

        """
        ========================================================================
        SETTEMPORARYBASALPERCENT
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Set temporary basal rate (in percentage): " + \
            str(rate) + "%, " + \
            str(duration) + "m"

        # Specify request parameters for command
        self.stick.request_button = 0
        self.stick.request_attempts = 0
        self.stick.request_pages = 1
        self.stick.request_code = 105
        self.stick.request_parameters = [
            int(rate),         # Rate is set in percentage
            int(duration / 30) # Duration is splitted in blocks of 30 minutes
            ]

        # Send request to pump
        self.stick.sendPumpRequest(expecting_data = False)

        # Give user info
        print "Temporary basal rate set."



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
    my_pump.start(do_power_up = True)

    # Read pump model
    my_pump.readModel()

    # Send bolus to pump
    my_pump.sendBolus(0.5)

    # Send temporary basal rate to pump
    my_pump.setTemporaryBasalPercent(50, 90)

    # Suspend pump activity
    #my_pump.suspend()

    # Resume pump activity
    #my_pump.resume()

    # Stop my stick
    my_pump.stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
