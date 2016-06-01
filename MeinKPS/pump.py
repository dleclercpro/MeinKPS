#! /usr/bin/python



"""
================================================================================
Title:    pump

Author:   David Leclerc

Version:  0.1

Date:     30.05.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that contains a handful of commands that can be sent
          wirelessly to a Medtronic RF Paradigm pump through a Carelink USB
          stick. Please use carefully!

Notes:    - When the battery is low, the stick will not be able to communicate
            with the pump anymore; the script will say the pump does not appear
            to be in range
================================================================================
"""



# TODO: - Make sure the maximal temporary basal rate and bolus are correctly
#         set, that is higher than or equal to the TB and/or bolus that will be
#         issued.
#       - Get manually issued bolus, in order for the loop to know when to stop/
#         restart.
#       - Test with alarm set on pump
#       - Test with pump reservoir empty
#       - Simplify pump request structure (see requester.py)
#       - Add all of the data in the buffer to the stick response
#       - Deal with timezones, DST, year switch



# LIBRARIES
import os
import sys
import time
import datetime



# USER LIBRARIES
import lib
import stick
import reporter



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



    def define(self, info, power, attempts, size, code, parameters,
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
        self.size = size
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
        self.packet.append(self.size)
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

        # Ask stick if pump data is ready until it says a certain number of
        # bytes are waiting in buffer
        while self.n_bytes_received == 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts
            if self.TALKATIVE:
                print "Asking if pump data was received: " + str(n) + "/-"

            # Send request
            self.stick.sendRequest([3, 0, 0])

            # Get size of response waiting in radio buffer
            self.n_bytes_received = self.stick.response[7]

            # Give user info
            if self.TALKATIVE:
                print "Number of bytes found: " + str(self.n_bytes_received)
                print "Expected number of bytes: " + str(self.n_bytes_expected)



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Verify if received data is as expected. If not, resend pump request
        # until it is
        while self.n_bytes_received != self.n_bytes_expected:

            # Verify connection with pump, quit if inexistent (this number of
            # bytes means no data was received from pump)
            if self.n_bytes_received == 14:
                sys.exit("Pump is either out of range, or will not take "
                         "commands anymore because of low battery level... :-(")

            # Give user info
            if self.TALKATIVE:
                print "Data does not correspond to expectations."
                print "Resending pump request..."

            # Resend pump request to stick
            self.send()

            # Ask pump if data is now ready to be read
            self.ask()

        # Give user info
        if self.TALKATIVE:
            print "Data corresponds to expectations."



    def retrieve(self):

        """
        ========================================================================
        RETRIEVE
        ========================================================================
        """
        
        # Ask if some pump data was received
        self.ask()

        # Verify if pump data corresponds to expectations
        self.verify()

        # Give user info
        if self.TALKATIVE:
            print "Retrieving pump data on stick..."

        # Initialize packet to retrieve pump data on stick
        self.packet = []

        # Build said packet
        self.packet.extend([12, 0])
        self.packet.append(lib.getByte(self.n_bytes_expected, 1))
        self.packet.append(lib.getByte(self.n_bytes_expected, 0))
        self.packet.append(lib.computeCRC8(self.packet))

        # Initialize pump response vectors
        self.response = []
        self.response_hex = []
        self.response_chr = []

        # Retrieve data until the end of it
        while True:

            # Download pump data by sending packet to stick
            self.send()

            # Store pump response in vectors
            self.response.extend(self.stick.response)
            self.response_hex.extend(self.stick.response_hex)
            self.response_chr.extend(self.stick.response_chr)

            # If the last digits, excluding the very last one, are zeros, then
            # the requested data has been downloaded
            if sum(self.stick.response[-6:-1]) == 0:

                break



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

        # If data was requested, retrieve it
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
    POWER_TIME          = 10     # Time (s) needed for pump to go online
    SESSION_TIME        = 5      # Time (m) for which pump will listen to RFs
    EXECUTION_TIME      = 5      # Time (s) needed for pump command execution
    STROKE_SIZE         = 0.1    # Pump stroke (U)
    TIME_BLOCK          = 30     # Time block (m) used by pump
    BOLUS_DELIVERY_RATE = 40.0   # Bolus delivery rate (s/U)
    BOLUS_EXTRA_TIME    = 7.5    # Ensure bolus was completely given
    BASAL_FACTOR        = 40.0   # Conversion of bolus rate to bytes
    VOLTAGE_FACTOR      = 0.0001 # Conversion of battery voltage
    BUTTONS             = {"EASY" : 0,
                           "ESC"  : 1,
                           "ACT"  : 2,
                           "UP"   : 3,
                           "DOWN" : 4}
    BATTERY_STATUS      = {0 : "Normal",
                           1 : "Low"}



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Give user info
        print "Starting dialogue with pump..."

        # Give the pump a reporter
        self.reporter = reporter.Reporter()

        # Instanciate a stick to communicate with the pump
        self.stick = stick.Stick()

        # Start stick and give it the pump serial number
        self.stick.start()

        # Power up pump's RF transmitter
        self.power()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        """

        # Give user info
        print "Stopping dialogue with the pump..."

        # Stop my stick
        self.stick.stop()



    def power(self):

        """
        ========================================================================
        POWER
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Powering pump radio transmitter for: " + 
                                   str(self.SESSION_TIME) + "m",
                            power = 85,
                            attempts = 0,
                            size = 0,
                            code = 93,
                            parameters = [1, self.SESSION_TIME],
                            n_bytes_expected = 0,
                            sleep = self.POWER_TIME,
                            sleep_reason = "Sleeping until pump " +
                                           "radio transmitter is powered " +
                                           "up... (" + str(self.POWER_TIME) +
                                           "s)")

        # Make pump request
        self.request.make()



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
                            size = 1,
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
                            size = 1,
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
                            size = 0,
                            code = 91,
                            parameters = [int(self.BUTTONS[button])],
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for button to be " +
                                           "pushed... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



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
                            size = 1,
                            code = 112,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump time from received data
        second = self.request.response[15]
        minute = self.request.response[14]
        hour = self.request.response[13]
        day = self.request.response[19]
        month = self.request.response[18]
        year = (lib.getByte(self.request.response[16], 0) * 256 |
                     lib.getByte(self.request.response[17], 0))

        # Generate time object
        time = datetime.datetime(year, month, day, hour, minute, second)

        # Store formatted time
        self.time = datetime.datetime.strftime(time, "%Y.%m.%d - %H:%M:%S")

        # Give user info
        print "Pump time: " + self.time



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
                            size = 1,
                            code = 141,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump model from received data
        self.model = int("".join(self.request.response_chr[14:17]))

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
                            size = 1,
                            code = 116,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump firmware from received data
        self.firmware = ("".join(self.request.response_chr[17:21]) +
                         " " +
                         "".join(self.request.response_chr[21:24]))

        # Give user info
        print "Pump firmware version: " + self.firmware



    def readBatteryLevel(self):

        """
        ========================================================================
        READBATTERYLEVEL
        ========================================================================

        Note: not very useful, since the pump won't respond anymore when the
              battery level is considered to be low...
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading battery level...",
                            power = 0,
                            attempts = 2,
                            size = 1,
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



    def readReservoirLevel(self):

        """
        ========================================================================
        READRESERVOIRLEVEL
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
                            size = 1,
                            code = 115,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract remaining amout of insulin
        self.reservoir = ((lib.getByte(self.request.response[13], 0) * 256 |
                         lib.getByte(self.request.response[14], 0)) *
                         self.STROKE_SIZE)

        # Give user info
        print "Amount of insulin in reservoir: " + str(self.reservoir) + "U"



    def readStatus(self):

        """
        ========================================================================
        READSTATUS
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading pump status...",
                            power = 0,
                            attempts = 2,
                            size = 1,
                            code = 206,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump status from received data
        self.status = {"Normal" : self.request.response[13] == 3,
                       "Bolusing" : self.request.response[14] == 1,
                       "Suspended" : self.request.response[15] == 1}

        # Give user info
        print "Pump status: " + str(self.status)



    def readSettings(self):

        """
        ========================================================================
        READSETTINGS
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading pump settings...",
                            power = 0,
                            attempts = 2,
                            size = 1,
                            code = 192,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract pump settings from received data
        self.settings = {
            "Max Bolus" : self.request.response[18] * self.STROKE_SIZE,
            "Max Basal" : (lib.getByte(self.request.response[19], 0) * 256 |
                           lib.getByte(self.request.response[20], 0)) /
                           self.BASAL_FACTOR,
            "Insulin Action Curve" : self.request.response[30]}

        # Give user info
        print "Pump settings: " + str(self.settings)



    def readHistory(self, n_pages):

        """
        ========================================================================
        READHISTORY
        ========================================================================
        """

        # Initialize pump history vector
        self.history = []

        # Download user-defined number of most recent pages of pump history
        for i in range(n_pages):

            # Give user info
            print "Reading pump history page: " + str(i)

            # Create pump request
            self.request = Request()

            # Give pump request a link to stick
            self.request.link(stick = self.stick)

            # Define pump request
            self.request.define(info = "Reading pump history...",
                                power = 0,
                                attempts = 2,
                                size = 2, # 2 means larger data exchange
                                code = 128,
                                parameters = [i], # 0 equals most recent page
                                n_bytes_expected = 206,
                                sleep = 0,
                                sleep_reason = None)

            # Make pump request
            self.request.make()

            # Extend known history of pump
            self.history.extend(self.request.response)



    def readDailyTotals(self):

        """
        ========================================================================
        READDAILYTOTALS
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading daily totals...",
                            power = 0,
                            attempts = 2,
                            size = 1,
                            code  = 121,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract daily totals of today and yesterday
        self.daily_total_today = (
            (lib.getByte(self.request.response[13], 0) * 256 |
             lib.getByte(self.request.response[14], 0)) * self.STROKE_SIZE)
        self.daily_total_yesterday = (
            (lib.getByte(self.request.response[15], 0) * 256 |
             lib.getByte(self.request.response[16], 0)) * self.STROKE_SIZE)

        # Give user info
        print ("Daily totals of today: " +
               str(self.daily_total_today) + "U")
        print ("Daily totals of yesterday: " +
               str(self.daily_total_yesterday) + "U")



    def readBolus(self):

        """
        ========================================================================
        READBOLUS
        ========================================================================
        """

        # Download most recent boluses on first pump history page
        n_pages = 1

        # Download pump history
        self.readHistory(n_pages = n_pages)

        print self.history

        # Define parameters to parse history pages when looking for boluses
        payload_code = 1
        payload_size = 9
        now = datetime.datetime.now()

        # Parse history page to find boluses
        for i in range(len(self.history) - 1 - payload_size):

            # Define bolus criteria
            if ((self.history[i] == payload_code) &
                (self.history[i + 1] == self.history[i + 2]) &
                (self.history[i + 3] == 0)):
        
                # Extract bolus from pump history
                bolus = round(self.history[i + 1] * self.STROKE_SIZE, 1)

                # Extract time at which bolus was delivered
                bolus_time = lib.parseTime(self.history[i + 4 : i + 9])

                # Test proof the bolus by looking closer at its delivery time
                try:

                    # Build datetime object
                    bolus_time = datetime.datetime(bolus_time[0],
                                                   bolus_time[1],
                                                   bolus_time[2],
                                                   bolus_time[3],
                                                   bolus_time[4],
                                                   bolus_time[5])

                    # Format bolus time
                    bolus_time = datetime.datetime.strftime(
                                 bolus_time, "%Y.%m.%d - %H:%M:%S")

                    # Give user info
                    print ("Bolus read: " + str(bolus) +
                           "U (" + str(bolus_time) + ")")

                    # Add bolus to insulin report
                    self.reporter.addBolusEntry(bolus = bolus,
                                                bolus_time = bolus_time)

                except ValueError:

                    # Error with bolus time (probably bad CRC)
                    print "Erroneous bolus time: " + str(bolus_time)
                    print "Not saving bolus."



    def deliverBolus(self, bolus):

        """
        ========================================================================
        DELIVERBOLUS
        ========================================================================
        """

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolus_delivery_time = (self.BOLUS_DELIVERY_RATE * bolus +
                               self.BOLUS_EXTRA_TIME)

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Sending bolus: " + str(bolus) + "U",
                            power = 0,
                            attempts = 0,
                            size = 1,
                            code = 66,
                            parameters = [int(bolus / self.STROKE_SIZE)],
                            n_bytes_expected = 0,
                            sleep = bolus_delivery_time,
                            sleep_reason = "Waiting for bolus to be " +
                                           "delivered... (" + 
                                           str(bolus_delivery_time) + "s)")

        # Make pump request
        self.request.make()



    def readTemporaryBasal(self):

        """
        ========================================================================
        READTEMPORARYBASAL
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # Define pump request
        self.request.define(info = "Reading current temporary basal...",
                            power = 0,
                            attempts = 2,
                            size = 1,
                            code = 152,
                            parameters = [],
                            n_bytes_expected = 78,
                            sleep = 0,
                            sleep_reason = None)

        # Make pump request
        self.request.make()

        # Extract absolute TB
        if self.request.response[13] == 0:
            self.TB_units = "U/h"
            self.TB_rate = (
                (lib.getByte(self.request.response[15], 0) * 256 |
                 lib.getByte(self.request.response[16], 0)) /
                 self.BASAL_FACTOR)

        # Extract percent TB
        elif self.request.response[13] == 1:
            self.TB_units = "%"
            self.TB_rate = self.request.response[14]

        # Extract TB remaining time
        self.TB_duration = (
            (lib.getByte(self.request.response[17], 0) * 256 |
             lib.getByte(self.request.response[18], 0)))

        # Give user info
        print ("Temporary basal: " + str(self.TB_rate) + " " +
               self.TB_units + " (" + str(self.TB_duration) + "m)")



    def setTemporaryBasalUnits(self, units):

        """
        ========================================================================
        SETTEMPORARYBASALUNITS
        ========================================================================
        """

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # If request is for absolute temporary basal
        if units == "U/h":
            parameters = [0]

        # If request is for temporary basal in percentage
        elif units == "%":
            parameters = [1]

        # Define rest of pump request
        self.request.define(info = "Setting temporary basal units: " +
                                   units,
                            power = 0,
                            attempts = 0,
                            size = 1,
                            code = 104,
                            parameters = parameters,
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for temporary basal " +
                                           "rate units to be set... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()



    def setTemporaryBasal(self, rate, units, duration, first_run = True):

        """
        ========================================================================
        SETTEMPORARYBASAL
        ========================================================================
        """

        # Give user info regarding the next TB that will be set
        print "Trying to set new temporary basal: " + str(rate) + \
              " " + units + " (" + str(duration) + "m)"

        # First run
        if first_run == True:

            # Before issuing any TB, read the current one
            self.readTemporaryBasal()

            # Store last TB values
            last_rate = self.TB_rate
            last_units = self.TB_units
            last_duration = self.TB_duration

            # In case the user wants to set the exact same TB, just ignore it
            if (rate == last_rate) & \
               (units == last_units) & \
               (duration == last_duration):

                # Give user info
                print "There is no point in reissuing the exact same " + \
                      "temporary basal: ignoring."

                return

            # Look if a non-zero TB is already set
            elif (last_rate != 0) | (last_duration != 0):

                # Give user info
                print "Temporary basal needs to be set to zero before " + \
                      "issuing a new one..."

                # Set TB to zero (it is crucial here to use the precedent
                # units, otherwise it would not work!)
                self.setTemporaryBasal(rate = 0,
                                           units = last_units,
                                           duration = 0,
                                           first_run = False)

            # In case the user wants to set the TB to zero in other units, more
            # specifically when it has already been canceled (this is why the
            # call is done to self.TB and not last)
            if (rate == 0) & (duration == 0) & \
               (self.TB_rate == 0) & (self.TB_duration == 0):

                # Give user info
                print "There is no point in reissuing a zero TB: ignoring."

                return

            # If units do not match, they must be changed
            elif units != last_units:

                # Give user info
                print "Old and new temporary basal units mismatch."

                # Modify units as wished by the user
                self.setTemporaryBasalUnits(units)

            # If user only wishes to extend/shorten the length of the already
            # set TB
            elif (rate == last_rate) & (duration != last_duration):

                # Evaluate time difference
                dt = duration - last_duration

                # For a shortened TB
                if dt < 0:

                    # Give user info
                    print "The temporary basal will be shortened " + \
                          "by: " + str(-dt) + "m"

                # For an extended TB
                elif dt > 0:

                    # Give user info
                    print "The temporary basal will be extended " + \
                          "by: " + str(dt) + "m"

        # Create pump request
        self.request = Request()

        # Give pump request a link to stick
        self.request.link(stick = self.stick)

        # If request is for absolute temporary basal
        if units == "U/h":
            code = 76
            parameters = [0,
                          int(rate * self.BASAL_FACTOR),
                          int(duration / self.TIME_BLOCK)]

        # If request is for temporary basal in percentage
        elif units == "%":
            code = 105
            parameters = [int(rate),
                          int(duration / self.TIME_BLOCK)]

        # Define rest of pump request
        self.request.define(info = "Setting temporary basal: " +
                                   str(rate) + " " +
                                   units + " (" +
                                   str(duration) + "m)",
                            power = 0,
                            attempts = 0,
                            size = 1,
                            code = code,
                            parameters = parameters,
                            n_bytes_expected = 0,
                            sleep = self.EXECUTION_TIME,
                            sleep_reason = "Waiting for temporary basal " +
                                           "rate to be set... (" +
                                           str(self.EXECUTION_TIME) + "s)")

        # Make pump request
        self.request.make()

        # Give user info
        print "Verifying that the new temporary basal was correctly " + \
              "set..."

        # Verify that the TB was correctly issued by reading current TB on
        # pump
        self.readTemporaryBasal()

        # Compare to expectedly set TB
        if (self.TB_rate == rate) & \
           (self.TB_units == units) & \
           (self.TB_duration == duration):

            # Give user info
            print "New temporary basal correctly set!"

        # Otherwise, quit
        else:
            sys.exit("New temporary basal could not be correctly " +
                     "set. :-(")



    def snoozeTemporaryBasal(self, snooze):

        """
        ========================================================================
        SNOOZETEMPORARYBASAL
        ========================================================================
        """

        self.setTemporaryBasal("U/h", 0, snooze)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a pump for me
    pump = Pump()

    # Start dialogue pump
    pump.start()

    # Read bolus history of pump
    pump.readTime()

    # Read pump model
    #pump.readModel()

    # Read pump firmware version
    #pump.readFirmwareVersion()

    # Read battery level of pump
    #pump.readBatteryLevel()

    # Read remaining amount of insulin in pump
    #pump.readReservoirLevel()

    # Read pump status
    #pump.readStatus()

    # Read pump settings
    #pump.readSettings()

    # Read daily totals on pump
    #pump.readDailyTotals()

    # Read history on pump
    pump.readBolus()

    # Send bolus to pump
    #pump.deliverBolus(0.5)

    # Send temporary basal to pump
    #pump.setTemporaryBasal(4.1, "U/h", 150)
    #pump.setTemporaryBasal(50, "%", 60)

    # Suspend pump activity
    #pump.suspend()

    # Resume pump activity
    #pump.resume()

    # Push button on pump
    #pump.pushButton("DOWN")

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
