#! /usr/bin/python



"""
================================================================================
TITLE:    controlPump

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     25.05.2016

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
LOGS_ADDRESS = "./stickLogs.txt"
NOW          = datetime.datetime.now()



class pump:

    # PUMP CHARACTERISTICS
    SERIAL_NUMBER       = 574180
    POWERUP_TIME        = 10     # Time (s) it takes for the pump to go online
    SESSION_TIME        = 15     # Time (m) for which pump will listen to RFs
    SUSPENSION_TIME     = 5      # Time (s) it takes to suspend pump activity
    TIME_BLOCK          = 30     # Time block (m) for temporary basal rates
    BOLUS_DELIVERY_RATE = 40     # Bolus delivery rate (s/U)
    BOLUS_BLOCK         = 10     # Bolus are splitted in blocks of 0.1U
    BOLUS_RATE_FACTOR   = 40     # Conversion of bolus rate to bytes
    BOLUS_EXTRA_TIME    = 7.5    # Ensure bolus was completely given
    BASAL_STROKES       = 10.0   # Size of basal strokes
    VOLTAGE_FACTOR      = 0.0001 # Conversion of battery voltage
    BUTTONS             = {"EASY":0, "ESC":1, "ACT":2, "UP":3, "DOWN":4}
    BATTERY_STATUS      = {0:"NORMAL", 1:"LOW"}



    def start(self, do_power_up = True, session_time = SESSION_TIME):

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

        # Give stick the serial number of the pump
        self.stick.pump_serial_number = self.SERIAL_NUMBER

        # Power up if needed
        if do_power_up:

            # Power up the pump
            self.powerUp(session_time)



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
        print "Powering up the pump for: " + str(duration) + "m"

        # Specify request parameters for command
        self.stick.pump_request_power = 85
        self.stick.pump_request_attempts = 0
        self.stick.pump_request_pages = 0
        self.stick.pump_request_code = 93
        self.stick.pump_request_parameters = [1,
            duration]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Sleeping until pump is powered up... " + \
              "(" + str(self.POWERUP_TIME) + "s)"

        # Wait
        time.sleep(self.POWERUP_TIME)

        # Give user info
        print "Pump powered up."



    def readBatteryLevel(self):

        """
        ========================================================================
        READBATTERYLEVEL
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Reading battery level..."

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 2
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 114
        self.stick.pump_request_parameters = []

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 15

        # Send request to pump
        self.stick.sendPumpRequest()

        # Get pump data
        self.stick.getPumpData()

        # Extract battery level from received data (voltages not very reliable,
        # rounding is necessary)
        self.battery_status = self.BATTERY_STATUS[self.stick.response[3]]
        self.battery_level = round(
            (lib.getByte(self.stick.response[4], 0) * 256
            | lib.getByte(self.stick.response[5], 0)) * self.VOLTAGE_FACTOR,
            1)

        # Give user info
        print "Battery status: " + self.battery_status # FIXME
        print "Battery level: " + str(self.battery_level) + "V" # FIXME



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
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 2
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 77
        self.stick.pump_request_parameters = [1]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Waiting for pump activity to be completely suspended... " + \
              "(" + str(self.SUSPENSION_TIME) + "s)"

        # Wait
        time.sleep(self.SUSPENSION_TIME)

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
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 2
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 77
        self.stick.pump_request_parameters = [0]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Pump activity resumed."



    def pushButton(self, button):

        """
        ========================================================================
        PUSHBUTTON
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Pushing button: " + button

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 1
        self.stick.pump_request_pages = 0
        self.stick.pump_request_code = 91
        self.stick.pump_request_parameters = [int(self.BUTTONS[button])]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Button pushed."



    def deliverBolus(self, bolus):

        """
        ========================================================================
        DELIVERBOLUS
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Sending bolus: " + str(bolus) + "U"

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 0
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 66
        self.stick.pump_request_parameters = [int(bolus * self.BOLUS_BLOCK)]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolus_time = self.BOLUS_DELIVERY_RATE * bolus + self.BOLUS_EXTRA_TIME

        # Give user info
        print "Waiting for bolus to be delivered... (" + str(bolus_time) + "s)"

        # Wait
        time.sleep(bolus_time)

        # Give user info
        print "Bolus sent."



    def setTemporaryBasalRate(self, rate, duration):

        """
        ========================================================================
        SETTEMPORARYBASALRATE
        ========================================================================

        Note: Make sure the temporary basal option is set to absolute (U/H) on
              the pump, or this command will not work!
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Set temporary basal rate: " + \
            str(rate) + "U/H " + \
            str(duration) + "m"

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 0
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 76
        self.stick.pump_request_parameters = [0,
            int(rate * self.BOLUS_RATE_FACTOR),
            int(duration / self.TIME_BLOCK)]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Temporary basal rate set."



    def setTemporaryBasalRatePercentage(self, rate, duration):

        """
        ========================================================================
        SETTEMPORARYBASALRATEPERCENTAGE
        ========================================================================

        Note: Make sure the temporary basal option is set to percentage on the
              pump, or this command will not work!
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Set temporary basal rate (in percentage): " + \
            str(rate) + "%, " + \
            str(duration) + "m"

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 0
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 105
        self.stick.pump_request_parameters = [int(rate),
            int(duration / self.TIME_BLOCK)]

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 0

        # Send request to pump
        self.stick.sendPumpRequest()

        # Give user info
        print "Temporary basal rate set."



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
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 2
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 141
        self.stick.pump_request_parameters = []

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 78

        # Send request to pump
        self.stick.sendPumpRequest()

        # Get pump data
        self.stick.getPumpData()

        # Extract pump model from received data
        self.model = int("".join(self.stick.response_str[14:17]))

        # Give user info
        print "Pump model obtained: " + str(self.model)



    def readRemainingInsulin(self):

        """
        ========================================================================
        READREMAININGINSULIN
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Give user info
        print "Reading amount of insulin left..."

        # Specify request parameters for command
        self.stick.pump_request_power = 0
        self.stick.pump_request_attempts = 2
        self.stick.pump_request_pages = 1
        self.stick.pump_request_code = 115
        self.stick.pump_request_parameters = []

        # Specify expected number of bytes as a response
        self.stick.expected_bytes = 78

        # Send request to pump
        self.stick.sendPumpRequest()

        # Get pump data
        self.stick.getPumpData()

        # Extract remaining amout of insulin
        self.insulin = ((lib.getByte(self.stick.response[13], 0) * 256
            | lib.getByte(self.stick.response[14], 0)) / self.BASAL_STROKES)

        # Give user info
        print "Amount of insulin left: " + str(self.insulin) + "U"



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
    my_pump.deliverBolus(0.3)

    # Send temporary basal rate to pump
    #my_pump.setTemporaryBasalRate(2, 60)
    #my_pump.setTemporaryBasalRatePercentage(50, 90)

    # Suspend pump activity
    my_pump.suspend()

    # Resume pump activity
    my_pump.resume()

    # Push button on pump
    my_pump.pushButton("DOWN")

    # Read battery level of pump
    my_pump.readBatteryLevel()

    # Read remaining amount of insulin in pump
    my_pump.readRemainingInsulin()

    # Stop my stick
    my_pump.stick.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
