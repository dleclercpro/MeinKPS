#! /usr/bin/python



"""
================================================================================
Title:    pump

Author:   David Leclerc

Version:  0.2

Date:     01.06.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that contains a handful of commands that can be sent
          wirelessly to a Medtronic RF Paradigm pump through a Carelink USB
          stick. Please use carefully!

Notes:    - When the battery is low, the stick will not be able to communicate
            with the pump anymore; the script will say the pump does not appear
            to be in range.
================================================================================
"""

# TODO: - Make sure the maximal temporary basal rate and bolus are correctly
#         set, that is higher than or equal to the TB and/or bolus that will be
#         issued.
#       - Test with alarm set on pump
#       - Test with pump reservoir empty or almost empty
#       - Deal with timezones, DST, year switch
#       - Run series of tests overnight
#       - Make sure enacted bolus are detected!



# LIBRARIES
import datetime
import json
import numpy as np
import sys



# USER LIBRARIES
import lib
import reporter
import requester
import stick



class Pump:

    # PUMP CHARACTERISTICS
    VERBOSE               = True
    PACKETS_HEAD          = [1, 0, 167, 1]
    SERIAL_NUMBER         = 799163
    SERIAL_NUMBER_ENCODED = lib.encodeSerialNumber(SERIAL_NUMBER)
    POWER_TIME            = 10     # Time (s) needed for pump to go online
    SESSION_TIME          = 10     # Time (m) for which pump will listen to RFs
    EXECUTION_TIME        = 5      # Time (s) needed for pump command execution
    BOLUS_STROKE          = 0.1    # Pump bolus stroke (U)
    BASAL_STROKE          = 0.05   # Pump basal stroke rate (U/h)
    TIME_BLOCK            = 30     # Time block (m) used by pump
    BOLUS_DELIVERY_RATE   = 40.0   # Bolus delivery rate (s/U)
    BOLUS_EXTRA_TIME      = 7.5    # Ensure bolus was completely given
    BUTTONS               = {"EASY" : 0,
                             "ESC"  : 1,
                             "ACT"  : 2,
                             "UP"   : 3,
                             "DOWN" : 4}



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

        # Give the pump a requester
        self.requester = requester.Requester()

        # Instanciate a stick to communicate with the pump
        self.stick = stick.Stick()

        # Start stick
        self.stick.start()

        # Prepare requester to send requests to the pump
        self.requester.prepare(recipient = "Pump", handle = self.stick.handle)

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

        # Stop stick
        self.stick.stop()



    def power(self):

        """
        ========================================================================
        POWER
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Powering pump radio transmitter for: " + 
                                     str(self.SESSION_TIME) + "m",
                              sleep = self.POWER_TIME,
                              sleep_reason = "Sleeping until pump " +
                                             "radio transmitter is powered " +
                                             "up... (" + str(self.POWER_TIME) +
                                             "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 85,
                              attempts = 0,
                              size = 0,
                              code = 93,
                              parameters = [1, self.SESSION_TIME])

        # Make pump request
        self.requester.make()



    def suspend(self):

        """
        ========================================================================
        SUSPEND
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Suspending pump activity...",
                              sleep = self.EXECUTION_TIME,
                              sleep_reason = "Waiting for pump activity to " +
                                             "be suspended... (" +
                                             str(self.EXECUTION_TIME) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 77,
                              parameters = [1])

        # Make pump request
        self.requester.make()



    def resume(self):

        """
        ========================================================================
        RESUME
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Resuming pump activity...",
                              sleep = self.EXECUTION_TIME,
                              sleep_reason = "Waiting for pump activity to " +
                                             "be resumed... (" +
                                             str(self.EXECUTION_TIME) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 77,
                              parameters = [0])

        # Make pump request
        self.requester.make()



    def pushButton(self, button):

        """
        ========================================================================
        PUSHBUTTON
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Pushing button: " + button,
                              sleep = self.EXECUTION_TIME,
                              sleep_reason = "Waiting for button to " +
                                             "be pushed... (" +
                                             str(self.EXECUTION_TIME) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 1,
                              size = 0,
                              code = 91,
                              parameters = [int(self.BUTTONS[button])])

        # Make pump request
        self.requester.make()



    def readTime(self):

        """
        ========================================================================
        READTIME
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading pump time...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 112,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract pump time from received data
        second = self.requester.response[15]
        minute = self.requester.response[14]
        hour   = self.requester.response[13]
        day    = self.requester.response[19]
        month  = self.requester.response[18]
        year   = (lib.getByte(self.requester.response[16], 0) * 256 |
                  lib.getByte(self.requester.response[17], 0))

        # Generate time object
        time = datetime.datetime(year, month, day, hour, minute, second)

        # Store formatted time
        self.time = lib.getTime(time)

        # Give user info
        print "Pump time: " + self.time



    def readModel(self):

        """
        ========================================================================
        READMODEL
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading pump model...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 141,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract pump model from received data
        self.model = int("".join([chr(x) for x in self.requester.data[14:17]]))

        # Give user info
        print "Pump model: " + str(self.model)



    def readFirmwareVersion(self):

        """
        ========================================================================
        READFIRMWAREVERSION
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading pump firmware version...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 116,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract pump firmware from received data
        self.firmware = ("".join(self.requester.response_chr[17:21]) + " " +
                         "".join(self.requester.response_chr[21:24]))

        # Give user info
        print "Pump firmware version: " + self.firmware



    def readReservoirLevel(self):

        """
        ========================================================================
        READRESERVOIRLEVEL
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading amount of insulin left...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 115,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract remaining amout of insulin
        self.reservoir = (
            (lib.getByte(self.requester.response[13], 0) * 256 |
             lib.getByte(self.requester.response[14], 0)) * self.BOLUS_STROKE)

        # Give user info
        print "Amount of insulin in reservoir: " + str(self.reservoir) + "U"



    def readStatus(self):

        """
        ========================================================================
        READSTATUS
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading pump status...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 206,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract pump status from received data
        self.status = {"Normal" : self.requester.response[13] == 3,
                       "Bolusing" : self.requester.response[14] == 1,
                       "Suspended" : self.requester.response[15] == 1}

        # Give user info
        print "Pump status: " + str(self.status)



    def verifyStatus(self):

        """
        ========================================================================
        VERIFYSTATUS
        ========================================================================
        """

        # Read pump status
        self.readStatus()

        # Check if pump is ready to take action
        if self.status["Normal"] == False:

            # Give user info
            print "There seems to be a problem with the pump. Try again later."

            return False

        elif self.status["Bolusing"] == True:

            # Give user info
            print "Pump is bolusing. Try again later."

            return False

        elif self.status["Suspended"] == True:

            # Give user info
            print "Pump is suspended, but will be asked to resume activity."

            # Resume pump activity
            self.resume()

            # Give user info
            print "Pump status allow desired course of action."

            return True



    def readSettings(self):

        """
        ========================================================================
        READSETTINGS
        ========================================================================
        """

        # Define pump request
        self.requester.define(info = "Reading pump settings...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 192,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract pump settings from received data
        self.settings = {
            "Max Bolus" : self.requester.response[18] * self.BOLUS_STROKE,
            "Max Basal" : (lib.getByte(self.requester.response[19], 0) * 256 |
                           lib.getByte(self.requester.response[20], 0)) *
                           self.BASAL_STROKE / 2.0,
            "Insulin Action Curve" : self.requester.response[30]}

        # Give user info
        print "Pump settings: " + str(self.settings)



    def verifySettings(self, bolus = None, rate = None, units = None):

        """
        ========================================================================
        VERIFYSETTINGS
        ========================================================================
        """

        # Read pump settings
        self.readSettings()

        # Check if pump is ready to take action
        if bolus != None:

            if bolus > self.settings["Max Bolus"]:

                # Give user info
                print "Pump cannot issue bolus since it is bigger than its " + \
                      "maximal allowed bolus. Update the latter before " + \
                      "trying again." 

                return False

        elif (rate != None) & (units != None):

            if ((units == "U/h") & (rate > self.settings["Max Basal"]) |
                (units == "%") & (rate > 200)):

                # Give user info
                print "Pump cannot issue temporary basal rate since it is " + \
                      "bigger than its maximal basal rate. Update the " + \
                      "latter before trying again." 

                return False

        # Pump settings allow desired action
        else:

            # Give user info
            print "Pump settings allow desired course of action."

            return True



    def readInsulinSensitivityFactors(self):

        """
        ========================================================================
        READINSULINSENSITIVITYFACTORS
        ========================================================================
        """

        # Initialize insulin sensitivity factors and units
        self.ISF = []
        self.ISU = None;

        # Define pump request
        self.requester.define(info = ("Reading insulin sensitivity factors " +
                                      "from pump..."),
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 139,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract insulin sensitivity units
        units = self.requester.response[13]

        # Decode units
        if units == 1:
            self.ISU = "mg/dL/U"
        else:
            self.ISU = "mmol/L/U" 

        # Initialize index as well as factors vector
        i = 0
        factors = []

        # Extract insulin sensitivity factors
        while True:

            # Define start (a) and end (b) indexes of current factor (each
            # factor entry corresponds to 2 bytes)
            a = 15 + 2 * i
            b = a + 2

            # Get current factor entry
            entry = self.requester.response[a:b]

            # Exit condition: no more factors stored
            if sum(entry) == 0:
                break
            else:
                # Decode entry
                factor = entry[0] / 10.0;
                time = entry[1] * 30; # Get time in minutes (each block
                                      # corresponds to 30 m)

                # Format time
                time = str(time / 60).zfill(2) + ":" + str(time % 60).zfill(2)

                # Store decoded factor and its corresponding ending time
                factors.append([time, factor]);

            # Increment index
            i += 1

        # Store number of factors read
        n = len(factors)

        # Rearrange factors to have starting times instead of ending times
        for i in range(n):
            self.ISF.append([factors[i - 1][0], factors[i][1]])


        # Give user info
        print "Found " + str(n) + " insulin sensitivity factors:"

        for i in range(n):
            print (self.ISF[i][0] + " - " +
                   str(self.ISF[i][1]) + " " + str(self.ISU))

        # Save insulin sensitivity factors to profile report
        self.reporter.saveInsulinSensitivityFactors(self.ISF, self.ISU)



    def readCarbSensitivityFactors(self):

        """
        ========================================================================
        READCARBSENSITIVITYFACTORS
        ========================================================================
        """

        # Initialize carb sensitivity factors and units
        self.CSF = []
        self.CSU = None;

        # Define pump request
        self.requester.define(info = ("Reading carb sensitivity factors from " +
                                      "pump..."),
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 138,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract carb sensitivity units
        units = self.requester.response[13]

        # Decode units
        if units == 1:
            self.CSU = "g/U"
        else:
            self.CSU = "exchanges/U" 

        # Initialize index as well as factors vector
        i = 0
        factors = []

        # Extract carb sensitivity factors
        while True:

            # Define start (a) and end (b) indexes of current factor (each
            # factor entry corresponds to 2 bytes)
            a = 15 + 2 * i
            b = a + 2

            # Get current factor entry
            entry = self.requester.response[a:b]

            # Exit condition: no more factors stored
            if sum(entry) == 0:
                break
            else:
                # Decode entry
                factor = entry[0];
                time = entry[1] * 30; # Get time in minutes (each block
                                      # corresponds to 30 m)

                # Format time
                time = str(time / 60).zfill(2) + ":" + str(time % 60).zfill(2)

                # Store decoded factor and its corresponding ending time
                factors.append([time, factor]);

            # Increment index
            i += 1

        # Store number of factors read
        n = len(factors)

        # Rearrange factors to have starting times instead of ending times
        for i in range(n):
            self.CSF.append([factors[i - 1][0], factors[i][1]])


        # Give user info
        print "Found " + str(n) + " carb sensitivity factors:"

        for i in range(n):
            print (self.CSF[i][0] + " - " +
                   str(self.CSF[i][1]) + " " + str(self.CSU))

        # Save carb sensitivity factors to profile report
        self.reporter.saveCarbSensitivityFactors(self.CSF, self.CSU)



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

            # Define pump request
            self.requester.define(info = "Reading pump history...",
                                  n_bytes_expected = 206,
                                  head = self.PACKETS_HEAD,
                                  serial = self.SERIAL_NUMBER_ENCODED,
                                  power = 0,
                                  attempts = 2,
                                  size = 2, # 2 means larger data exchange
                                  code = 128,
                                  parameters = [i]) # 0 equals most recent page

            # Make pump request
            self.requester.make()

            # Extend known history of pump
            self.history.extend(self.requester.data)

        # Give user info
        if self.VERBOSE:

            # Print collected history pages
            print "First " + str(n_pages) + " pages of pump history:"
            print self.history



    def readDailyTotals(self):

        """
        ========================================================================
        READDAILYTOTALS
        ========================================================================
        """

        # Initialize daily totals dictionary
        self.daily_totals = {"Today": None,
                             "Yesterday": None}

        # Define pump request
        self.requester.define(info = "Reading pump daily totals...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 121,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract daily totals of today and yesterday
        self.daily_totals["Today"] = round(
            (lib.getByte(self.requester.response[13], 0) * 256 |
             lib.getByte(self.requester.response[14], 0)) * self.BOLUS_STROKE,
             2)

        # Extract daily totals of yesterday
        self.daily_totals["Yesterday"] = round(
            (lib.getByte(self.requester.response[15], 0) * 256 |
             lib.getByte(self.requester.response[16], 0)) * self.BOLUS_STROKE,
             2)

        # Give user info
        print "Daily totals:"
        print json.dumps(self.daily_totals, indent = 2,
                                            separators = (",", ": "),
                                            sort_keys = True)



    def readBoluses(self):

        """
        ========================================================================
        READBOLUSES
        ========================================================================
        """

        # Initialize boluses vector
        boluses = []

        # Download most recent boluses on first pump history pages
	    # FIXME When pump history too short, higher history pages do not exist?
        n_pages = 1

        # Download pump history
        self.readHistory(n_pages = n_pages)

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
                bolus = round(self.history[i + 1] * self.BOLUS_STROKE, 1)

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
                    bolus_time = lib.getTime(bolus_time)

                    # Give user info
                    print ("Bolus read: " + str(bolus) +
                           "U (" + str(bolus_time) + ")")

                    # Store bolus
                    boluses.append([bolus_time, bolus])

                except:

                    # Error with bolus time (bad CRC?)
                    print "Erroneous bolus time: " + str(bolus_time)
                    print "Not saving bolus."

        # If new boluses read, write them to insulin report
        if len(boluses) != 0:

            # Convert boluses vector to numpy array
            boluses = np.array(boluses)

            # Add boluses to report
            self.reporter.addBoluses(boluses[:, 0], boluses[:, 1])



    def readTemporaryBasal(self):

        """
        ========================================================================
        READTEMPORARYBASAL
        ========================================================================
        """

        # Define current temporary basal dictionary
        self.TB = {"Rate": None,
                   "Units": None,
                   "Duration": None}

        # Define pump request
        self.requester.define(info = "Reading current temporary basal...",
                              n_bytes_expected = 78,
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 2,
                              size = 1,
                              code = 152,
                              parameters = [])

        # Make pump request
        self.requester.make()

        # Extract TB [U/h]
        if self.requester.response[13] == 0:

            # Extract TB characteristics
            self.TB["Units"] = "U/h"
            self.TB["Rate"] = round(
                (lib.getByte(self.requester.response[15], 0) * 256 |
                 lib.getByte(self.requester.response[16], 0)) *
                 self.BASAL_STROKE / 2.0, 2)

        # Extract TB [%]
        elif self.requester.response[13] == 1:

            # Extract TB characteristics
            self.TB["Units"] = "%"
            self.TB["Rate"] = round(self.requester.response[14], 2)

        # Extract TB remaining time
        self.TB["Duration"] = round(
            (lib.getByte(self.requester.response[17], 0) * 256 |
             lib.getByte(self.requester.response[18], 0)), 0)

        # Give user info
        print "Temporary basal:"
        print json.dumps(self.TB, indent = 2,
                                  separators = (",", ": "),
                                  sort_keys = True)



    def deliverBolus(self, bolus):

        """
        ========================================================================
        DELIVERBOLUS
        ========================================================================
        """

        # Verify pump status and settings before doing anything
        if ((self.verifyStatus() == False) |
            (self.verifySettings(bolus = bolus) == False)):

            return

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolus_delivery_time = (self.BOLUS_DELIVERY_RATE * bolus +
                               self.BOLUS_EXTRA_TIME)

        # Define pump request
        self.requester.define(info = "Sending bolus: " + str(bolus) + " U",
                              sleep = bolus_delivery_time,
                              sleep_reason = "Waiting for bolus to be " +
                                             "delivered... (" + 
                                             str(bolus_delivery_time) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 0,
                              size = 1,
                              code = 66,
                              parameters = [int(bolus / self.BOLUS_STROKE)])

        # Make pump request
        self.requester.make()

        # Read issued bolus in order to save it to the reports
        self.readBoluses()



    def setTemporaryBasalUnits(self, units):

        """
        ========================================================================
        SETTEMPORARYBASALUNITS
        ========================================================================
        """

        # If request is for absolute temporary basal
        if units == "U/h":
            parameters = [0]

        # If request is for temporary basal in percentage
        elif units == "%":
            parameters = [1]

        # Define pump request
        self.requester.define(info = "Setting temporary basal units: " + units,
                              sleep = self.EXECUTION_TIME,
                              sleep_reason = "Waiting for temporary basal " +
                                             "rate units to be set... (" +
                                             str(self.EXECUTION_TIME) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 0,
                              size = 1,
                              code = 104,
                              parameters = parameters)

        # Make pump request
        self.requester.make()



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

            # Verify pump status and settings before doing anything
            if ((self.verifyStatus() == False) |
                (self.verifySettings(rate = rate, units = units) == False)):

                return

            # Before issuing any TB, read the current one
            self.readTemporaryBasal()

            # Store last TB values
            last_rate = self.TB["Rate"]
            last_units = self.TB["Units"]
            last_duration = self.TB["Duration"]

            # In case the user wants to set the exact same TB, just ignore it
            if (rate == last_rate) & \
               (units == last_units) & \
               (duration == last_duration):

                # Give user info
                print "There is no point in reissuing the exact same " + \
                      "temporary basal: ignoring."

                return

            # In case the user wants to cancel a non-existent TB
            elif ((rate == 0) & (last_rate == 0) &
                  (duration == 0) & (last_duration == 0)):

                # Give user info
                print "There is no point in canceling a non-existent TB: " + \
                      "ignoring."

                return

            # Look if a TB is already set
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

            # If units do not match, they must be changed
            if units != last_units:

                # Give user info
                print "Old and new temporary basal units mismatch."

                # Modify units as wished by the user
                self.setTemporaryBasalUnits(units = units)

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

        # If request is for absolute temporary basal
        if units == "U/h":
            code = 76
            parameters = [0,
                          int(round(rate / self.BASAL_STROKE * 2.0)),
                          int(duration / self.TIME_BLOCK)]

        # If request is for temporary basal in percentage
        elif units == "%":
            code = 105
            parameters = [int(round(rate)),
                          int(duration / self.TIME_BLOCK)]

        # Define pump request
        self.requester.define(info = "Setting temporary basal: " +
                                     str(rate) + " " +
                                     units + " (" +
                                     str(duration) + "m)",
                              sleep = self.EXECUTION_TIME,
                              sleep_reason = "Waiting for temporary basal " +
                                             "rate to be set... (" +
                                             str(self.EXECUTION_TIME) + "s)",
                              head = self.PACKETS_HEAD,
                              serial = self.SERIAL_NUMBER_ENCODED,
                              power = 0,
                              attempts = 0,
                              size = 1,
                              code = code,
                              parameters = parameters)

        # Make pump request
        self.requester.make()

        # Give user info
        print "Verifying that the new temporary basal was correctly " + \
              "set..."

        # Verify that the TB was correctly issued by reading current TB on
        # pump
        self.readTemporaryBasal()

        # Compare to expectedly set TB
        if (self.TB["Rate"] == rate) & \
           (self.TB["Units"] == units) & \
           (self.TB["Duration"] == duration):

            # Give user info
            print ("New temporary basal correctly set: " +
                   str(self.TB["Rate"]) + " " + str(self.TB["Units"]) + " (" +
                   str(self.TB["Duration"]) + ")")

            # Give user info
            print "Saving new temporary basal to reports..."

            # Format time at which TB was set
            time = lib.getTime(self.requester.time)

            # Add bolus to insulin report
            self.reporter.addTemporaryBasal(time = time,
                                            rate = rate,
                                            units = units,
                                            duration = duration)

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

        self.setTemporaryBasal(0, "U/h", snooze)



    def cancelTemporaryBasal(self):

        """
        ========================================================================
        CANCELTEMPORARYBASAL
        ========================================================================
        """

        self.setTemporaryBasal(0, "U/h", 0)



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
    #pump.readTime()

    # Read pump model
    #pump.readModel()

    # Read pump firmware version
    #pump.readFirmwareVersion()

    # Read remaining amount of insulin in pump
    #pump.readReservoirLevel()

    # Read pump status
    #pump.readStatus()

    # Read pump settings
    #pump.readSettings()

    # Read daily totals on pump
    #pump.readDailyTotals()

    # Read bolus history on pump
    #pump.readBoluses()

    # Send bolus to pump
    #pump.deliverBolus(0.5)

    # Read temporary basal
    #pump.readTemporaryBasal()

    # Send temporary basal to pump
    #pump.setTemporaryBasal(5, "U/h", 30)
    #pump.setTemporaryBasal(200, "%", 60)
    #pump.cancelTemporaryBasal()

    # Read insulin sensitivity factors stored in pump
    pump.readInsulinSensitivityFactors()

    # Read carb sensitivity factors stored in pump
    pump.readCarbSensitivityFactors()

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
