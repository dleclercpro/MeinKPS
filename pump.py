#! /usr/bin/python



"""
================================================================================
Title:    pump
Author:   David Leclerc
Version:  0.1
Date:     25.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: ...
Notes:    ...
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
import stick



# DEFINITIONS
LOGS_ADDRESS = "./stickLogs.txt"
NOW          = datetime.datetime.now()



class Request:

    # PUMP REQUEST CONSTANTS
    TALKATIVE             = True
    HEAD                  = [1, 0, 167, 1]
    SERIAL_NUMBER         = 574180
    ENCODED_SERIAL_NUMBER = lib.encodeSerialNumber(SERIAL_NUMBER)



    def link(self, stick):

        """
        ========================================================================
        LINK
        ========================================================================
        """

        # Link pump request with previously generated stick instance
        self.stick = stick



    def define(self, info, power, attempts, pages, code, parameters,
               n_bytes_expected, sleep, sleep_reason):

        """
        ========================================================================
        DEFINE
        ========================================================================
        """

        # Store input definition of pump request
        self.info = info
        self.power = power
        self.attempts = attempts
        self.pages = pages
        self.code = code
        self.parameters = parameters
        self.parameter_count = [128 | lib.getByte(len(parameters), 1),
                                      lib.getByte(len(parameters), 0)]
        self.n_bytes_expected = n_bytes_expected
        self.sleep = sleep
        self.sleep_reason = sleep_reason



    def build(self):

        """
        ========================================================================
        BUILD
        ========================================================================
        """

        # Initialize pump request corresponding packet
        self.packet = []

        # Build said packet
        self.packet.extend(self.HEAD)
        self.packet.extend(self.ENCODED_SERIAL_NUMBER)
        self.packet.extend(self.parameter_count)
        self.packet.append(self.power)
        self.packet.append(self.attempts)
        self.packet.append(self.pages)
        self.packet.append(0)
        self.packet.append(self.code)
        self.packet.append(lib.computeCRC8(self.packet))
        self.packet.extend(self.parameters)
        self.packet.append(lib.computeCRC8(self.parameters))



    def send(self):

        """
        ========================================================================
        SEND
        ========================================================================

        Send request to pump
        """

        # Send pump request over stick
        self.stick.sendRequest(self.packet)



    def ask(self):

        """
        ========================================================================
        ASK
        ========================================================================
        """

        # Reset number of bytes received
        self.n_bytes_received = 0

        # Define asking attempt variable
        n = 0

        # Ask stick if pump data is ready
        while self.n_bytes_received == 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts
            if self.TALKATIVE:
                print "Ask if data from pump was received: " + str(n) + "/-"

            # Send request
            self.stick.sendRequest([3, 0, 0])

            # Get size of response waiting in radio buffer
            self.n_bytes_received = self.stick.response[7]



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Verify if received data is as expected. If not, resend pump request
        # until data it is
        while self.n_bytes_received != self.n_bytes_expected:

            # Verify connection with pump, quit if inexistent
            if self.n_bytes_received == 14:
                sys.exit("Pump seems out of range... :-(")

            # Give user info
            if self.TALKATIVE:
                print "Resending pump request..."

            # Resend pump request to stick
            self.send()

            # Ask pump if data is now ready to be read
            self.ask()

            # Give user info
            if self.TALKATIVE:
                print "Number of bytes found: " + str(self.n_bytes_received)
                print "Expected number of bytes: " + str(self.n_bytes_expected)



    def retrieve(self):

        """
        ========================================================================
        RETRIEVE
        ========================================================================
        """

        # Ask for pump data
        self.ask()

        # Verify pump data
        self.verify()

        # Give user info
        if self.TALKATIVE:
            print "Retrieving pump data on stick..."

        # Initialize packet to retrieve pump data on stick
        self.packet = []

        # Build said packet
        self.packet.extend([12,
                            0,
                            lib.getByte(self.n_bytes_received, 1),
                            lib.getByte(self.n_bytes_received, 0)])
        self.packet.append(lib.computeCRC8(self.packet))

        # Send request
        self.stick.sendRequest(self.packet)

        # Store pump data in all formats
        self.response = self.stick.response
        self.response_hex = self.stick.response_hex
        self.response_str = self.stick.response_str



    def make(self):

        """
        ========================================================================
        MAKE
        ========================================================================
        """

        # Print pump request info
        print self.info

        # Build request associated packet
        self.build()

        # Send said packet over stick to pump
        self.send()

        # If data was request, retrieve it
        if self.n_bytes_expected > 0:

            # Retrieve pump data
            self.retrieve()

        # Give pump time to execute request if needed
        if self.sleep > 0:

            # Give sleep reason
            print self.sleep_reason

            # Sleep
            time.sleep(self.sleep)



class Pump:

    # PUMP CHARACTERISTICS
    POWERUP_TIME        = 10     # Time (s) needed for pump to go online
    SESSION_TIME        = 10     # Time (m) for which pump will listen to RFs
    EXECUTION_TIME      = 5      # Time (s) needed for pump command execution
    BASAL_STROKES       = 10.0   # Size of basal strokes
    BASAL_TIME_BLOCK    = 30     # Time block (m) for temporary basal rates
    BOLUS_DELIVERY_RATE = 40     # Bolus delivery rate (s/U)
    BOLUS_BLOCK         = 10     # Bolus are splitted in blocks of 0.1U
    BOLUS_RATE_FACTOR   = 40.0   # Conversion of bolus rate to bytes
    BOLUS_EXTRA_TIME    = 7.5    # Ensure bolus was completely given
    VOLTAGE_FACTOR      = 0.0001 # Conversion of battery voltage
    BUTTONS             = {"EASY":0, "ESC":1, "ACT":2, "UP":3, "DOWN":4}
    BATTERY_STATUS      = {0:"Normal", 1:"Low"}



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Instanciate a stick to communicate with the pump
        self.stick = stick.Stick()

        # Start stick and give it the pump serial number
        self.stick.start()

        # Power up pump's RF transmitter
        self.powerUp()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        """

        # Stop my stick
        self.stick.stop()



    def powerUp(self):

        """
        ========================================================================
        POWERUP
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Powering up the pump for: " +
                                   str(self.SESSION_TIME) + "m",
                            power = 85,
                            attempts = 0,
                            pages = 0,
                            code = 93,
                            parameters = [1, self.SESSION_TIME],
                            n_bytes_expected = 0,
                            sleep = self.POWERUP_TIME,
                            sleep_reason = "Sleeping until pump is powered " +
                                           "up... " + "(" +
                                           str(self.POWERUP_TIME) + "s)")

        # Make pump request
        self.request.make()



    def readModel(self):

        """
        ========================================================================
        READMODEL
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading pump model...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 141,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump model from received data
        self.model = int("".join(self.request.response_str[14:17]))

        # Give user info
        print "Pump model: " + str(self.model)



    def readFirmwareVersion(self):

        """
        ========================================================================
        READFIRMWAREVERSION
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading pump firmware version...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 116,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump firmware from received data
        self.firmware = ("".join(self.request.response_str[17:21]) +
                         " " +
                         "".join(self.request.response_str[21:24]))

        # Give user info
        print "Pump firmware version: " + self.firmware



    def readBatteryLevel(self):

        """
        ========================================================================
        READBATTERYLEVEL
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading battery level...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 114,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract battery level from received data
        self.battery_status = self.BATTERY_STATUS[self.request.response[3]]
        self.battery_level = ((lib.getByte(self.request.response[4], 0) * 256 |
                               lib.getByte(self.request.response[5], 0)) *
                               self.VOLTAGE_FACTOR)

        # Voltages are not very reliable, rounding is necessary! # FIXME
        self.battery_level = round(self.battery_level, 1)

        # Give user info
        print "Battery status: " + self.battery_status
        print "Battery level: " + str(self.battery_level) + "V"



    def readTime(self):

        """
        ========================================================================
        READTIME
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading pump time...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 112,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump time from received data
        self.second = self.request.response[15]
        self.minute = self.request.response[14]
        self.hour = self.request.response[13]
        self.day = self.request.response[19]
        self.month = self.request.response[18]
        self.year = (lib.getByte(self.request.response[16], 0) * 256 |
                     lib.getByte(self.request.response[17], 0))

        # Give user info
        print "Pump time: " + (str(self.day).zfill(2) + "." +
                               str(self.month).zfill(2) + "." +
                               str(self.year).zfill(2) + " " +
                               str(self.hour).zfill(2) + ":" +
                               str(self.minute).zfill(2) + ":" +
                               str(self.second).zfill(2))



    def readReservoir(self):

        """
        ========================================================================
        READRESERVOIR
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading amount of insulin left...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 115,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract remaining amout of insulin
        self.reservoir = ((lib.getByte(self.request.response[13], 0) * 256 |
                         lib.getByte(self.request.response[14], 0)) /
                         self.BASAL_STROKES)

        # Give user info
        print "Amount of insulin in reservoir: " + str(self.reservoir) + "U"



    def readTemporaryBasalRate(self):

        """
        ========================================================================
        READTEMPORARYBASALRATE
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading temporary basal rate...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 152,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract type of temporary basal rate (TBR)
        self.read_TBR_type = self.request.response[13]

        # Extract absolute TBR
        if self.read_TBR_type == 0:
            self.read_TBR_units = "U/H"
            self.TBR = (
                (lib.getByte(self.request.response[15], 0) * 256 |
                 lib.getByte(self.request.response[16], 0)) /
                 self.BOLUS_RATE_FACTOR)

        # Extract percent TBR
        elif self.read_TBR_type == 1:
            self.read_TBR_units = "%"
            self.TBR = self.request.response[14]

        # Extract TBR remaining time
        self.read_TBR_duration = (
            (lib.getByte(self.request.response[17], 0) * 256 |
             lib.getByte(self.request.response[18], 0)))

        # Give user info
        print ("Temporary basal rate: " + str(self.TBR) + " " +
               self.read_TBR_units + " (" + str(self.read_TBR_duration) + "m)")



    def suspend(self):

        """
        ========================================================================
        SUSPEND
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Suspending pump activity...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 77,
                            parameters = [1],
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for pump activity to be " +
                                           "completely suspended... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



    def resume(self):

        """
        ========================================================================
        RESUME
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Resuming pump activity...",
                            power = 0,
                            attempts = 2,
                            pages = 1,
                            code = 77,
                            parameters = [0],
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for pump activity to " +
                                           "be resumed... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



    def pushButton(self, button):

        """
        ========================================================================
        PUSHBUTTON
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Pushing button: " + button,
                            power = 0,
                            attempts = 1,
                            pages = 0,
                            code = 91,
                            parameters = [int(self.BUTTONS[button])],
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for button to be " +
                                           "pushed... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



    def deliverBolus(self, bolus):

        """
        ========================================================================
        DELIVERBOLUS
        ========================================================================
        """

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolus_time = self.BOLUS_DELIVERY_RATE * bolus + self.BOLUS_EXTRA_TIME

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Sending bolus: " + str(bolus) + "U",
                            power = 0,
                            attempts = 0,
                            pages = 1,
                            code = 66,
                            parameters = [int(bolus * self.BOLUS_BLOCK)],
                            n_bytes_expected = 0,
                            sleep = bolus_time,
                            sleep_reason = "Waiting for bolus to be " +
                                           "delivered... (" + str(bolus_time) +
                                           "s)")

        # Make pump request
        self.request.make()



    def setTemporaryBasalRate(self, units, rate, duration):

        """
        ========================================================================
        SETTEMPORARYBASALRATE
        ========================================================================

        Note: Make sure the temporary basal option is correctly set on the pump,
              or this command will not work!
        """

        # Store infos of the temporary basal rate (TBR) that will be set
        self.set_TBR_units = units
        self.set_TBR_rate = rate
        self.set_TBR_duration = duration

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # If request is for absolute temporary basal rate
        if self.set_TBR_units == "U/H":
            code = 76
            parameters = [0,
                          int(rate * self.BOLUS_RATE_FACTOR),
                          int(duration / self.BASAL_TIME_BLOCK)]

        # If request is for temporary basal rate in percentage
        elif self.set_TBR_units == "%":
            code = 105
            parameters = [int(rate),
                          int(duration / self.BASAL_TIME_BLOCK)]

        # Define rest of pump request
        self.request.define(info = "Set temporary basal rate: " +
                                   str(self.set_TBR_rate) + " " +
                                   self.set_TBR_units + " (" +
                                   str(self.set_TBR_duration) + "m)",
                            power = 0,
                            attempts = 0,
                            pages = 1,
                            code = code,
                            parameters = parameters,
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for temporary basal " +
                                           "rate to be set... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a pump for me
    pump = Pump()

    # Start pump
    pump.start()

    # Read pump model
    pump.readModel()

    # Read pump firmware version
    #pump.readFirmwareVersion()

    # Read bolus history of pump
    #pump.readTime()

    # Read battery level of pump
    #pump.readBatteryLevel()

    # Send bolus to pump
    #pump.deliverBolus(0.2)

    # Send temporary basal rate to pump
    pump.setTemporaryBasalRate("U/H", 2, 60)
    #pump.setTemporaryBasalRate("%", 50, 90)

    # Read temporary basal rate
    pump.readTemporaryBasalRate()

    # Suspend pump activity
    #pump.suspend()

    # Resume pump activity
    #pump.resume()

    # Push button on pump
    #pump.pushButton("DOWN")

    # Read remaining amount of insulin in pump
    #pump.readReservoir()

    # Stop pump
    pump.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
