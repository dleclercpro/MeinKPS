#! /usr/bin/python

"""
================================================================================

    Title:    pump

    Author:   David Leclerc

    Version:  0.2

    Date:     01.06.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains a handful of commands that can be
              sent wirelessly to a Medtronic RF Paradigm pump through a Carelink
              USB stick. Please use carefully!

    Notes:    - When the battery is low, the stick will not be able to
                communicate with the pump anymore.

================================================================================
"""

# TODO: - Make sure the maximal temporary basal rate and bolus are correctly
#         set, that is higher than or equal to the TBR and/or bolus that will be
#         issued.
#       - Test with alarm set on pump
#       - Test with pump reservoir empty or almost empty
#       - Deal with timezones, DST, year switch
#       - Run series of tests overnight
#       X Make sure enacted bolus are detected!
#       - No point in reissuing same TBR?
#       - Decode square/dual boluses?
#       - Add "change battery" suggestion when no more response received from
#         stick
#       - Reduce session time if looping every 5 minutes?



# LIBRARIES
import datetime
import json
import sys
import time



# USER LIBRARIES
import lib
import reporter
import requester
import stick



class Pump:

    # PUMP CHARACTERISTICS
    serial            = 799163
    powerTime         = 10     # Time (s) needed for pump's radio to power up
    sessionTime       = 10     # Time (m) for which pump will listen to RFs
    executionTime     = 5      # Time (s) needed for pump command execution
    bolusStroke       = 0.1    # Pump bolus stroke (U)
    basalStroke       = 0.05   # Pump basal stroke rate (U/h)
    timeBlock         = 30     # Time block (m) used by pump
    bolusDeliveryRate = 40.0   # Bolus delivery rate (s/U)
    bolusExtraTime    = 7.5    # Ensure bolus was completely given
    buttons           = {"EASY": 0, "ESC": 1, "ACT": 2, "UP": 3, "DOWN": 4}



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

        # Initialize requester to speak with pump
        self.requester.initialize(recipient = "Pump",
                                  serial = self.serial,
                                  handle = self.stick.handle)

        # Power pump's radio transmitter if necessary
        self.verifyPower()



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



    def verifyPower(self):

        """
        ========================================================================
        VERIFYPOWER
        ========================================================================
        """

        # Get current time
        now = datetime.datetime.now()

        # Read last time pump's radio transmitter was power up
        then = self.reporter.getEntry("pump.json", [], "Power Up")

        # Format time
        then = lib.formatTime(then)

        # Define max time allowed between RF communication sessions
        session = datetime.timedelta(minutes = self.sessionTime)

        # Compute time since last power up
        delta = now - then

        # Power up pump if necessary
        if delta > session:

            # Give user info
            print "Pump's radio transmitter will be turned on..."

            # Power up pump's RF transmitter
            self.power()

        else:

            # Give user info
            print ("Pump's radio transmitter is already on. Remaining time: " +
                   str(self.sessionTime - delta.seconds / 60) + " m")



    def power(self):

        """
        ========================================================================
        POWER
        ========================================================================
        """

        # Define infos for pump request
        info = ("Powering pump radio transmitter for: " +
                str(self.sessionTime) + "m")
        sleepReason = ("Sleeping until pump radio transmitter is powered " +
                       "up... (" + str(self.powerTime) + "s)")

        # Define pump request
        self.requester.define(
            info = info,
            sleep = self.powerTime,
            sleepReason = sleepReason,
            power = 85,
            attempts = 0,
            size = 0,
            code = 93,
            parameters = [1, self.sessionTime])

        # Make pump request
        self.requester.make()

        # Save power up time
        self.reporter.storePowerTime()



    def suspend(self):

        """
        ========================================================================
        SUSPEND
        ========================================================================
        """

        # Define infos for pump request
        info = "Suspending pump activity..."
        sleepReason = ("Waiting for pump activity to be suspended... (" +
                       str(self.executionTime) + "s)")

        # Define pump request
        self.requester.define(info = info,
                              sleep = self.executionTime,
                              sleepReason = sleepReason,
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

        # Define infos for pump request
        info = "Resuming pump activity..."
        sleepReason = ("Waiting for pump activity to be resumed... (" +
                       str(self.executionTime) + "s)")

        # Define pump request
        self.requester.define(info = info,
                              sleep = self.executionTime,
                              sleepReason = sleepReason,
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

        # Define infos for pump request
        info = "Pushing button: " + button
        sleepReason = ("Waiting for button " + button + " to be pushed... (" +
                       str(self.executionTime) + "s)")

        # Define pump request
        self.requester.define(info = info,
                              sleep = self.executionTime,
                              sleepReason = sleepReason,
                              attempts = 1,
                              size = 0,
                              code = 91,
                              parameters = [int(self.buttons[button])])

        # Make pump request
        self.requester.make()



    def readTime(self):

        """
        ========================================================================
        READTIME
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump time..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 112)

        # Make pump request
        self.requester.make()

        # Extract pump time from received data
        second = self.requester.data[2]
        minute = self.requester.data[1]
        hour   = self.requester.data[0]
        day    = self.requester.data[6]
        month  = self.requester.data[5]
        year   = lib.bangInt(self.requester.data[3:5])

        # Generate time object
        time = datetime.datetime(year, month, day, hour, minute, second)

        # Store formatted time
        self.time = lib.formatTime(time)

        # Give user info
        print "Pump time: " + self.time



    def readModel(self):

        """
        ========================================================================
        READMODEL
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump model..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 141)

        # Make pump request
        self.requester.make()

        # Extract pump model from received data
        self.model = int("".join([chr(x) for x in self.requester.data[1:4]]))

        # Give user info
        print "Pump model: " + str(self.model)



    def readFirmwareVersion(self):

        """
        ========================================================================
        READFIRMWAREVERSION
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump firmware version..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 116)

        # Make pump request
        self.requester.make()

        # Extract pump firmware from received data
        self.firmware = ("".join(self.requester.responseChr[17:21]) + " " +
                         "".join(self.requester.responseChr[21:24]))

        # Give user info
        print "Pump firmware version: " + self.firmware



    def readBatteryLevel(self):

        """
        ========================================================================
        READBATTERYLEVEL
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading battery level..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 114)

        # Make pump request
        self.requester.make()

        # Decode battery level
        level = self.requester.data[0]

        if level == 0:
            self.battery = "Normal"
        elif level == 1:
            self.battery = "Low"

        # Decode battery voltage # FIXME
        self.batteryVoltage = lib.bangInt([self.requester.data[1],
                                           self.requester.data[2]]) / 100.0

        # Give user info
        print "Pump's battery level: " + str([self.battery,
                                              str(self.batteryVoltage) + " V"])



    def readReservoirLevel(self):

        """
        ========================================================================
        READRESERVOIRLEVEL
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading amount of insulin left in pump reservoir..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 115)

        # Make pump request
        self.requester.make()

        # Decode remaining amount of insulin
        self.reservoir = (lib.bangInt(self.requester.data[0:2]) *
                          self.bolusStroke)

        # Round amount
        self.reservoir = round(self.reservoir, 1)

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Add current reservoir level to pump report
        self.reporter.addReservoirLevel(now, self.reservoir)

        # Give user info
        print "Amount of insulin in reservoir: " + str(self.reservoir) + "U"



    def readStatus(self):

        """
        ========================================================================
        READSTATUS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump status..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 206)

        # Make pump request
        self.requester.make()

        # Extract pump status from received data
        self.status = {"Normal" : self.requester.data[0] == 3,
                       "Bolusing" : self.requester.data[1] == 1,
                       "Suspended" : self.requester.data[2] == 1}

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
            print "Pump status allows desired course of action."

            return True



    def readSettings(self):

        """
        ========================================================================
        READSETTINGS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump settings..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 192)

        # Make pump request
        self.requester.make()

        # Extract pump settings from received data
        self.settings = {
            "Max Bolus": self.requester.data[5] * self.bolusStroke,
            "Max Basal": (lib.bangInt(self.requester.data[6:8]) *
                          self.basalStroke / 2.0),
            "IAC": self.requester.data[17]
        }

        # Save pump settings to profile report
        self.reporter.storeSettings(self.settings)

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
                print ("Pump cannot issue bolus since it is bigger than its " +
                       "maximal allowed bolus. Update the latter before " +
                       "trying again." )

                return False

        elif (rate != None) & (units != None):

            if ((units == "U/h") & (rate > self.settings["Max Basal"]) |
                (units == "%") & (rate > 200)):

                # Give user info
                print ("Pump cannot issue temporary basal rate since it is " +
                       "bigger than its maximal basal rate. Update the " +
                       "latter before trying again.") 

                return False

        # Pump settings allow desired action
        else:

            # Give user info
            print "Pump settings allow desired course of action."

            return True



    def readBGU(self):

        """
        ========================================================================
        READBGU
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump's BG units..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 137)

        # Make pump request
        self.requester.make()

        # Decode BG units
        if self.requester.data[0] == 1:
            self.BGU = "mg/dL"

        elif self.requester.data[0] == 2:
            self.BGU = "mmol/L"

        # Give user info
        print "Pump's BG units are set to: " + str(self.BGU)



    def readCU(self):

        """
        ========================================================================
        READCU
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump's carb units..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 136)

        # Make pump request
        self.requester.make()

        # Decode BG units
        if self.requester.data[0] == 1:
            self.CU = "g"

        elif self.requester.data[0] == 2:
            self.CU = "exchanges"

        # Give user info
        print "Pump's carb units are set to: " + str(self.CU)



    def readDailyTotals(self):

        """
        ========================================================================
        READDAILYTOTALS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump daily totals..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 121)

        # Make pump request
        self.requester.make()

        # Initialize daily totals dictionary
        self.dailyTotals = {"Today": None,
                             "Yesterday": None}

        # Extract daily totals of today and yesterday
        self.dailyTotals["Today"] = round(
            lib.bangInt(self.requester.data[0:2]) * self.bolusStroke, 2)

        # Extract daily totals of yesterday
        self.dailyTotals["Yesterday"] = round(
            lib.bangInt(self.requester.data[2:4]) * self.bolusStroke, 2)

        # Give user info
        print "Daily totals:"
        print json.dumps(self.dailyTotals, indent = 2,
                                           separators = (",", ": "),
                                           sort_keys = True)



    def readBGTargets(self):

        """
        ========================================================================
        READBGTARGETS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading blood glucose targets from pump..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 159)

        # Make pump request
        self.requester.make()

        # Initialize blood glucose targets, times, and units
        self.BGTargets = []
        self.BGTargetsTimes = []
        self.BGU = None

        # Extract carb sensitivity units
        units = self.requester.data[0]

        # Decode units
        if units == 1:
            self.BGU = "mg/dL"

            # Define a multiplicator to decode ISF bytes
            m = 0

        else:
            self.BGU = "mmol/L"

            # Define a multiplicator to decode ISF bytes
            m = 1.0

        # Initialize index as well as targets and times vectors
        i = 0
        targets = []
        times = []

        # Extract BG targets
        while True:

            # Define start (a) and end (b) indexes of current factor based on
            # number of bytes per entry
            n = 3
            a = 2 + n * i
            b = a + n

            # Get current target entry
            entry = self.requester.data[a:b]

            # Exit condition: no more targets stored
            if sum(entry) == 0:
                break
            else:
                # Decode entry
                target = [entry[0] / 10 ** m, entry[1] / 10 ** m]
                time = entry[2] * 30 # Get time in minutes (each block
                                     # corresponds to 30 m)

                # Format time
                time = str(time / 60).zfill(2) + ":" + str(time % 60).zfill(2)

                # Store decoded target and its corresponding ending time
                targets.append(target)
                times.append(time)

            # Increment index
            i += 1

        # Store number of targets read
        n = len(targets)

        # Rearrange targets to have starting times instead of ending times
        for i in range(n):
            self.BGTargets.append(targets[i])
            self.BGTargetsTimes.append(times[i - 1])


        # Give user info
        print "Found " + str(n) + " blood glucose targets:"

        for i in range(n):
            print (self.BGTargetsTimes[i] + " - " +
                   str(self.BGTargets[i]) + " " + str(self.BGU))

        # Save blood glucose targets to profile report
        self.reporter.storeBloodGlucoseTargets(self.BGTargetsTimes,
                                              self.BGTargets,
                                              self.BGU)



    def readInsulinSensitivityFactors(self):

        """
        ========================================================================
        READINSULINSENSITIVITYFACTORS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading insulin sensitivity factors from pump..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 139)

        # Make pump request
        self.requester.make()

        # Initialize insulin sensitivity factors, times, and units
        self.ISF = []
        self.ISFTimes = []
        self.ISU = None

        # Extract insulin sensitivity units
        units = self.requester.data[0]

        # Decode units
        if units == 1:
            self.ISU = "mg/dL/U"
            
            # Define a multiplicator to decode ISF bytes
            m = 0

        else:
            self.ISU = "mmol/L/U"

            # Define a multiplicator to decode ISF bytes
            m = 1.0

        # Initialize index as well as factors and times vectors
        i = 0
        factors = []
        times = []

        # Extract insulin sensitivity factors
        while True:

            # Define start (a) and end (b) indexes of current factor based on
            # number of bytes per entry
            n = 2
            a = 2 + n * i
            b = a + n

            # Get current factor entry
            entry = self.requester.data[a:b]

            # Exit condition: no more factors stored
            if sum(entry) == 0:
                break
            else:
                # Decode entry
                factor = entry[0] / 10 ** m
                time = entry[1] * 30 # Get time in minutes (each block
                                     # corresponds to 30 m)

                # Format time
                time = str(time / 60).zfill(2) + ":" + str(time % 60).zfill(2)

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Store number of factors read
        n = len(factors)

        # Rearrange factors to have starting times instead of ending times
        for i in range(n):
            self.ISF.append(factors[i])
            self.ISFTimes.append(times[i - 1])

        # Give user info
        print "Found " + str(n) + " insulin sensitivity factors:"

        for i in range(n):
            print (self.ISFTimes[i] + " - " +
                   str(self.ISF[i]) + " " + str(self.ISU))

        # Save insulin sensitivity factors to profile report
        self.reporter.storeInsulinSensitivityFactors(self.ISFTimes, self.ISF,
                                                    self.ISU)



    def readCarbSensitivityFactors(self):

        """
        ========================================================================
        READCARBSENSITIVITYFACTORS
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading carb sensitivity factors from pump..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 138)

        # Make pump request
        self.requester.make()

        # Initialize carb sensitivity factors, times, and units
        self.CSF = []
        self.CSFTimes = []
        self.CSU = None

        # Extract carb sensitivity units
        units = self.requester.data[0]

        # Decode units
        if units == 1:
            self.CSU = "g/U"

            # Define a multiplicator to decode ISF bytes
            m = 0

        else:
            self.CSU = "exchanges/U"

            # Define a multiplicator to decode ISF bytes
            m = 1.0

        # Initialize index as well as factors and times vectors
        i = 0
        factors = []
        times = []

        # Extract carb sensitivity factors
        while True:

            # Define start (a) and end (b) indexes of current factor based on
            # number of bytes per entry
            n = 2
            a = 2 + n * i
            b = a + n

            # Get current factor entry
            entry = self.requester.data[a:b]

            # Exit condition: no more factors stored
            if sum(entry) == 0:
                break
            else:
                # Decode entry
                factor = entry[0] / 10 ** m
                time = entry[1] * 30 # Get time in minutes (each block
                                     # corresponds to 30 m)

                # Format time
                time = str(time / 60).zfill(2) + ":" + str(time % 60).zfill(2)

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Store number of factors read
        n = len(factors)

        # Rearrange factors to have starting times instead of ending times
        for i in range(n):
            self.CSF.append(factors[i])
            self.CSFTimes.append(times[i - 1])

        # Give user info
        print "Found " + str(n) + " carb sensitivity factors:"

        for i in range(n):
            print (self.CSFTimes[i] + " - " +
                   str(self.CSF[i]) + " " + str(self.CSU))

        # Save carb sensitivity factors to profile report
        self.reporter.storeCarbSensitivityFactors(self.CSFTimes, self.CSF,
                                                 self.CSU)



    def readNumberHistoryPages(self):

        """
        ========================================================================
        READNUMBERHISTORYPAGES
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading current pump history page number..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 157)

        # Make pump request
        self.requester.make()

        # Store number of history pages
        self.nHistoryPages = self.requester.data[3] + 1

        # Give user info
        print "Found " + str(self.nHistoryPages) + " pump history pages."



    def readHistory(self):

        """
        ========================================================================
        READHISTORY
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading pump history..."

        # Read number of existing history pages
        self.readNumberHistoryPages()

        # Initialize pump history vector
        self.history = []

        # Download user-defined number of most recent pages of pump history
        for i in range(self.nHistoryPages):

            # Give user info
            print "Reading pump history page: " + str(i)

            # Define pump request
            self.requester.define(info = info,
                                  attempts = 2,
                                  size = 2,
                                  code = 128,
                                  parameters = [i])

            # Make pump request
            self.requester.make()

            # Extend known history of pump
            self.history.extend(self.requester.data)

        # Print collected history pages
        print str(self.nHistoryPages) + " pages of pump history:"
        print self.history



    def readTreatments(self):

        """
        ========================================================================
        READTREATMENTS
        ========================================================================

        Note: - Boluses and carbs input seem to be stored exactly at sime time
                in pump.
              - No need to run readBGU and readCU functions, since units are
                encoded in message bytes!
              - No idea how to decode low ISF in mg/dL... information seems to
                be stored in 4th body byte, but no other byte enables
                differenciation between < and >= 256 ?

        Warning: - Do not change units for no reason, otherwise treatments will
                   not be read correctly!
        """

        # Initialize carbs and times vectors
        carbs = []
        times = []

        # Define an indicator dictionary to decode BG and carb bytes
        # <i>: [<BGU>, <CU>, <larger BG>, <larger C>]
        self.indicators = {
            80: ["mg/dL", "g", False, False],
            82: ["mg/dL", "g", True, False],
            84: ["mg/dL", "g", False, True],
            86: ["mg/dL", "g", True, True],

            96: ["mg/dL", "exchanges", False, False],
            98: ["mg/dL", "exchanges", True, False],

            144: ["mmol/L", "g", False, False],
            145: ["mmol/L", "g", True, False],
            148: ["mmol/L", "g", False, True],
            149: ["mmol/L", "g", True, True],

            160: ["mmol/L", "exchanges", False, False],
            161: ["mmol/L", "exchanges", True, False],
        }

        # Read current time
        now = datetime.datetime.now()

        # Download pump history
        self.readHistory()

        # Define record characteristics
        code = 91
        headSize = 2
        dateSize = 5
        bodySize = 13

        # Compute minimum size of record
        minRecordSize = headSize + dateSize + bodySize

        # Parse history
        for i in range(len(self.history) - minRecordSize + 1):

            # Look for code, with which every record should start
            if self.history[i] == code:

                # Test proof bolus wizard record
                try:

                    # Define a record running variable
                    x = i
            
                    # Assign record head
                    head = self.history[x:x + headSize]

                    # Update running variable
                    x += headSize

                    # Assign record date
                    date = self.history[x:x + dateSize]

                    # Update running variable
                    x += dateSize

                    # Assign record body
                    body = self.history[x:x + bodySize]

                    # Decode time using date bytes
                    time = lib.decodeTime(date)

                    # Build datetime object
                    time = datetime.datetime(time[0], time[1], time[2],
                                             time[3], time[4], time[5])

                    # Proof record year
                    if abs(time.year - now.year) > 1:

                        raise ValueError("Record and current year too far " +
                                         "apart!")

                    # Format time
                    time = lib.formatTime(time)

                    # Decode units and sizes of BG and carb entries using 2nd
                    # body byte as indicator
                    indicator = body[1]
                    
                    # Find a match between current indicator and the previously
                    # defined dictionary
                    [BGU, CU, largerBG, largerC] = self.indicators[indicator]

                    # Define rounding multiplicator for BGs and Cs
                    if BGU == "mmol/L":
                        mBGU = 1.0

                    else:
                        mBGU = 0

                    if CU == "exchanges":
                        mCU = 1.0

                    else:
                        mCU = 0

                    # Define number of bytes to add for larger BGs and Cs
                    if largerBG:
                        
                        # Extra number of bytes depends on BG units
                        if BGU == "mmol/L":
                            mBG = 256

                        else:
                            mBG = 512

                    else:
                        mBG = 0

                    if largerC:
                        mC = 256

                    else:
                        mC = 0

                    # Decode record
                    BG = (head[1] + mBG) / 10 ** mBGU
                    C = (body[0] + mC) / 10 ** mCU

                    # Not really necessary, but those are correct
                    BGTargets = [body[4] / 10 ** mBGU, body[12] / 10 ** mBGU]
                    CSF = body[2] / 10 ** mCU

                    # Add carbs and times at which they were consumed to their
                    # respective vectors only if they have a given value!
                    if C:
                        carbs.append([C, CU])
                        times.append(time)

                    # Give user output
                    print str(head) + ", " + str(body)
                    print "BG: " + str(BG) + " " + str(BGU) + " - " + time
                    print "Carbs: " + str(C) + " " + str(CU) + " - " + time
                    print

                except:
                    pass

        # If carbs read, store them
        if len(carbs) != 0:
            self.reporter.addCarbs(times, carbs)



    def readBoluses(self):

        """
        ========================================================================
        READBOLUSES
        ========================================================================
        """

        # Download pump history
        self.readHistory()

        # Define parameters to parse history pages when looking for boluses
        payloadCode = 1
        payloadSize = 9
        now = datetime.datetime.now()

        # Initialize boluses and times vectors
        boluses = []
        times = []

        # Parse history page to find boluses
        for i in range(len(self.history) - 1 - payloadSize):

            # Define bolus criteria
            if ((self.history[i] == payloadCode) &
                (self.history[i + 1] == self.history[i + 2]) &
                (self.history[i + 3] == 0)):
        
                # Extract bolus from pump history
                bolus = round(self.history[i + 1] * self.bolusStroke, 1)

                # Extract time at which bolus was delivered
                time = lib.decodeTime(self.history[i + 4 : i + 9])

                # Test proof the bolus by looking closer at its delivery time
                try:

                    # Check for bolus year
                    if abs(time[0] - now.year) > 1:

                        raise ValueError("Bolus can't be more than one year " +
                                         "in the past!")

                    # Build datetime object
                    time = datetime.datetime(time[0], time[1], time[2],
                                             time[3], time[4], time[5])

                    # Format bolus time
                    time = lib.formatTime(time)

                    # Give user info
                    print ("Bolus read: " + str(bolus) +
                           "U (" + str(time) + ")")
                    
                    # Store bolus
                    boluses.append(bolus)
                    times.append(time)

                except:

                    pass

        # If boluses read, store them
        if len(boluses) != 0:
            self.reporter.addBoluses(times, boluses)



    def readCarbs(self):

        """
        ========================================================================
        READCARBS
        ========================================================================
        """

        # Download pump history
        self.readHistory()

        # Define parameters to parse history pages when looking for boluses
        payloadCode = 91
        payloadSize = 20 # FIXME
        now = datetime.datetime.now()

        # Initialize carbs and times vectors
        carbs = []
        times = []

        # Parse history page to find boluses
        for i in range(len(self.history) - 1 - payloadSize):

            # Define carb criteria
            if self.history[i] == payloadCode:
        
                print self.history[i:i + payloadSize]



    def readCurrentTBR(self):

        """
        ========================================================================
        READCURRENTTBR
        ========================================================================
        """

        # Define infos for pump request
        info = "Reading current temporary basal..."

        # Define pump request
        self.requester.define(info = info,
                              attempts = 2,
                              size = 1,
                              code = 152)

        # Make pump request
        self.requester.make()

        # Define current temporary basal dictionary
        self.TBR = {"Value": None,
                    "Units": None,
                    "Duration": None}

        # Extract TBR [U/h]
        if self.requester.data[0] == 0:

            # Extract characteristics
            self.TBR["Units"] = "U/h"
            self.TBR["Value"] = round(
                lib.bangInt(self.requester.data[2:4]) * self.basalStroke / 2.0,
                2)

        # Extract TBR [%]
        elif self.requester.data[0] == 1:

            # Extract characteristics
            self.TBR["Units"] = "%"
            self.TBR["Value"] = round(self.requester.data[1], 2)

        # Extract remaining time
        self.TBR["Duration"] = round(lib.bangInt(self.requester.data[4:6]), 0)

        # Give user info
        print "Temporary basal:"
        print json.dumps(self.TBR, indent = 2,
                                   separators = (",", ": "),
                                   sort_keys = True)



    def deliverBolus(self, bolus):

        """
        ========================================================================
        DELIVERBOLUS
        ========================================================================
        """

        # Verify pump status and settings before doing anything
        if self.verifyStatus() == False:
            return
        if self.verifySettings(bolus = bolus) == False:
            return

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolusDeliveryTime = (self.bolusDeliveryRate * bolus +
                             self.bolusExtraTime)

        # Define infos for pump request
        info = "Sending bolus: " + str(bolus) + " U"
        sleepReason = ("Waiting for bolus to be delivered... (" +
                       str(bolusDeliveryTime) + "s)")

        # Define pump request
        self.requester.define(info = info,
                              sleep = bolusDeliveryTime,
                              sleepReason = sleepReason,
                              attempts = 0,
                              size = 1,
                              code = 66,
                              parameters = [int(bolus / self.bolusStroke)])

        # Make pump request
        self.requester.make()

        # Read issued bolus in order to store it to the reports
        self.readBoluses()

        # Check if last bolus stored fits to the one just delivered
        # TODO



    def setTBRUnits(self, units):

        """
        ========================================================================
        SETTBRUNITS
        ========================================================================
        """

        # If request is for absolute temporary basal
        if units == "U/h":
            parameters = [0]

        # If request is for temporary basal in percentage
        elif units == "%":
            parameters = [1]

        # Define infos for pump request
        info = "Setting temporary basal units: " + units
        sleepReason = ("Waiting for temporary basal rate units to be set... (" +
                       str(self.executionTime) + "s)")

        # Define pump request
        self.requester.define(info = info,
                              sleep = self.executionTime,
                              sleepReason = sleepReason,
                              attempts = 0,
                              size = 1,
                              code = 104,
                              parameters = parameters)

        # Make pump request
        self.requester.make()



    def setTBR(self, rate, units, duration, run = True):

        """
        ========================================================================
        SETTBR
        ========================================================================
        """

        # Give user info regarding the next TBR that will be set
        print ("Trying to set new temporary basal: " + str(rate) + " " + units +
               " (" + str(duration) + "m)")

        # First run
        if run == True:

            # Verify pump status and settings before doing anything
            if self.verifyStatus() == False:
                return
            if self.verifySettings(rate = rate, units = units) == False:
                return

            # Before issuing any TBR, read the current one
            self.readCurrentTBR()

            # Store last TBR values
            lastValue = self.TBR["Value"]
            lastUnits = self.TBR["Units"]
            lastDuration = self.TBR["Duration"]

            # In case the user wants to set the exact same TBR, just ignore it
            if (rate == lastValue) & \
               (units == lastUnits) & \
               (duration == lastDuration):

                # Give user info
                print ("There is no point in reissuing the exact same " +
                       "temporary basal: ignoring.")

                return

            # In case the user wants to cancel a non-existent TBR
            elif ((rate == 0) & (lastValue == 0) &
                  (duration == 0) & (lastDuration == 0)):

                # Give user info
                print ("There is no point in canceling a non-existent TBR: " +
                       "ignoring.")

                return

            # Look if a TBR is already set
            elif (lastValue != 0) | (lastDuration != 0):

                # Give user info
                print ("Temporary basal needs to be set to zero before " +
                       "issuing a new one...")

                # Set TBR to zero (it is crucial here to use the precedent
                # units, otherwise it would not work!)
                self.setTBR(rate = 0, units = lastUnits, duration = 0,
                            run = False)

            # If units do not match, they must be changed
            if units != lastUnits:

                # Give user info
                print "Old and new temporary basal units mismatch."

                # Modify units as wished by the user
                self.setTBRUnits(units = units)

            # If user only wishes to extend/shorten the length of the already
            # set TBR
            elif (rate == lastValue) & (duration != lastDuration):

                # Evaluate time difference
                dt = duration - lastDuration

                # For a shortened TBR
                if dt < 0:

                    # Give user info
                    print ("The temporary basal will be shortened by: " +
                           str(-dt) + "m")

                # For an extended TBR
                elif dt > 0:

                    # Give user info
                    print ("The temporary basal will be extended by: " +
                           str(dt) + "m")

        # If request is for absolute temporary basal
        if units == "U/h":
            code = 76
            parameters = [0,
                          int(round(rate / self.basalStroke * 2.0)),
                          int(duration / self.timeBlock)]

        # If request is for temporary basal in percentage
        elif units == "%":
            code = 105
            parameters = [int(round(rate)),
                          int(duration / self.timeBlock)]



        # Define infos for pump request
        info = ("Setting temporary basal: " + str(rate) + " " + units + " (" +
                str(duration) + "m)")
        sleepReason = ("Waiting for temporary basal rate to be set... (" +
                       str(self.executionTime) + "s)")

        # Define pump request
        self.requester.define(
            info = info,
            sleep = self.executionTime,
            sleepReason = sleepReason,
            attempts = 0,
            size = 1,
            code = code,
            parameters = parameters)

        # Get current time
        now = datetime.datetime.now()

        # Store time at which TBR is requested
        time = lib.formatTime(now)

        # Make pump request
        self.requester.make()

        # Give user info
        print "Verifying that the new temporary basal was correctly set..."

        # Verify that the TBR was correctly issued by reading current TBR on
        # pump
        self.readCurrentTBR()

        # Compare to expectedly set TBR
        if ((self.TBR["Value"] == rate) &
            (self.TBR["Units"] == units) &
            (self.TBR["Duration"] == duration)):

            # Give user info
            print ("New temporary basal correctly set: " +
                   str(self.TBR["Value"]) + " " + str(self.TBR["Units"]) +
                   " (" + str(self.TBR["Duration"]) + ")")

            # Give user info
            print "Saving new temporary basal to reports..."

            # Add bolus to insulin report
            self.reporter.addTBR(time, rate, units, duration)

        # Otherwise, quit
        else:
            sys.exit("New temporary basal could not be correctly " +
                     "set. :-(")



    def snoozeTBR(self, snooze):

        """
        ========================================================================
        SNOOZETBR
        ========================================================================
        """

        self.setTBR(0, "U/h", snooze)



    def cancelTBR(self):

        """
        ========================================================================
        CANCELTBR
        ========================================================================
        """

        self.setTBR(0, "U/h", 0)



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

    # Read pump battery level
    #pump.readBatteryLevel()

    # Read remaining amount of insulin in pump
    #pump.readReservoirLevel()

    # Read pump status
    #pump.readStatus()

    # Read pump settings
    #pump.readSettings()

    # Read daily totals on pump
    #pump.readDailyTotals()

    # Read current history page number
    #pump.readNumberHistoryPages()

    # Read bolus history on pump
    #pump.readTreatments()

    # Read bolus history on pump
    pump.readBoluses()

    # Read carbs history on pump
    #pump.readCarbs()

    # Send bolus to pump
    #pump.deliverBolus(0.1)

    # Read temporary basal
    #pump.readCurrentTBR()

    # Send temporary basal to pump
    #pump.setTBR(5, "U/h", 30)
    #pump.setTBR(200, "%", 60)

    # Read insulin sensitivity factors stored in pump
    #pump.readInsulinSensitivityFactors()

    # Read carb sensitivity factors stored in pump
    #pump.readCarbSensitivityFactors()

    # Read blood glucose targets stored in pump
    #pump.readBGTargets()

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
