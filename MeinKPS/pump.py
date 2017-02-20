#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO: - Make sure the maximal TBR and bolus are correctly
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
#       - Deal with manually set TBR. Read end of TBR?



# LIBRARIES
import datetime
import json
import sys
import time



# USER LIBRARIES
import lib
import decoder
import reporter
import requester
import stick



class Pump:

    # PUMP CHARACTERISTICS
    serial            = 799163
    powerTime         = 10     # Time (s) needed for pump's radio to power up
    sessionTime       = 10     # Time (m) for which pump will listen to RFs
    executionDelay    = 5      # Time (s) needed for pump command execution
    timeBlock         = 30     # Time block (m) used by pump
    basalStroke       = 0.05   # Pump basal stroke rate (U/h)
    bolusDeliveryRate = 40.0   # Bolus delivery rate (s/U)
    bolusStroke       = 0.1    # Pump bolus stroke (U)
    bolusDelay        = 5.0    # Time (s) to wait after bolus delivery



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the pump a reporter
        self.reporter = reporter.Reporter()

        # Give the pump a requester
        self.requester = requester.Requester()

        # Give the pump a stick
        self.stick = stick.Stick()

        # Give the pump a power instance
        self.power = Power(self)

        # Give the pump a time instance
        self.time = Time(self)

        # Give the pump a model instance
        self.model = Model(self)

        # Give the pump a firmware instance
        self.firmware = Firmware(self)

        # Give the pump an instance for its buttons
        self.buttons = Buttons(self)

        # Give the pump a battery instance
        self.battery = Battery(self)

        # Give the pump a reservoir instance
        self.reservoir = Reservoir(self)

        # Give the pump a status instance
        self.status = Status(self)

        # Give the pump a settings instance
        self.settings = Settings(self)

        # Give the pump a BG units instance
        self.BGUnits = BGUnits(self)

        # Give the pump a carb units instance
        self.carbUnits = CarbUnits(self)

        # Give the pump a TBR units instance
        self.TBRUnits = TBRUnits(self)

        # Give the pump a BG targets instance
        self.BGTargets = BGTargets(self)

        # Give the pump an ISF instance
        self.ISF = ISF(self)

        # Give the pump a CSF instance
        self.CSF = CSF(self)

        # Give the pump a daily totals instance
        self.dailyTotals = DailyTotals(self)

        # Give the pump a history instance
        self.history = History(self)

        # Give the pump a boluses instance
        self.boluses = Boluses(self)

        # Give the pump a carbs instance
        self.carbs = Carbs(self)

        # Give the pump a TBR instance
        self.TBR = TBR(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Starting dialogue with pump..."

        # Start stick
        self.stick.start()

        # Initialize requester to speak with pump
        self.requester.start(recipient = "Pump",
                             serial = self.serial,
                             handle = self.stick.handle)

        # Power pump's radio transmitter if necessary
        self.power.verify()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Stopping dialogue with the pump..."

        # Stop stick
        self.stick.stop()



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









class Power:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time a link to its corresponding device
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump's report
        self.device.reporter.load("pump.json")

        # Read last time pump's radio transmitter was power up
        then = self.device.reporter.getEntry([], "Power Up")

        # Format time
        then = lib.formatTime(then)

        # Define max time allowed between RF communication sessions
        session = datetime.timedelta(minutes = self.device.sessionTime)

        # Get current time
        now = datetime.datetime.now()

        # Compute time since last power up
        delta = now - then

        # Power up pump if necessary
        if delta > session:

            # Give user info
            print "Pump's radio transmitter will be turned on..."

            # Power up pump's RF transmitter
            self.do()

        else:

            # Give user info
            print ("Pump's radio transmitter is already on. Remaining time: " +
                   str(self.device.sessionTime - delta.seconds / 60) + " m")



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Devine infos for request
        info = ("Powering pump radio transmitter for: " +
                       str(self.device.sessionTime) + "m")
        sleepReason = ("Sleeping until pump radio transmitter is " +
                              "powered up... (" + str(self.device.powerTime) +
                              "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.powerTime,
                                     sleepReason = sleepReason,
                                     power = 85,
                                     attempts = 0,
                                     size = 0,
                                     code = 93,
                                     parameters = [1, self.device.sessionTime])

        # Make request
        self.device.requester.make()

        # Get current time
        now = datetime.datetime.now()

        # Convert time to string
        now = lib.formatTime(now)

        # Save power up time
        self.device.reporter.storePowerTime(now)



class Time:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump time..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 112)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readTime")

        # Give user info
        print "Pump time: " + self.value



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class Model:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump model..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 141)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readModel")

        # Store pump model
        self.device.reporter.storeModel(self.value)

        # Give user info
        print "Pump model: " + str(self.value)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class Firmware:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump firmware version..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 116)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readFirmware")

        # Store pump model
        self.device.reporter.storeFirmware(self.value)

        # Give user info
        print "Pump firmware version: " + str(self.value)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class Buttons:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Buttons
        values = {"EASY": 0, "ESC": 1, "ACT": 2, "UP": 3, "DOWN": 4}



    def push(self, button):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PUSH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Pushing button: " + button
        sleepReason = ("Waiting for button " + button + " to be pushed... (" +
                       str(self.device.executionDelay) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.executionDelay,
                                     sleepReason = sleepReason,
                                     attempts = 1,
                                     size = 0,
                                     code = 91,
                                     parameters = [int(self.values[button])])

        # Make request
        self.device.requester.make()



class Battery:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading battery level..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 114)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readBatteryLevel")

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Add current reservoir level to pump report
        self.device.reporter.addBatteryLevel(now, [self.level, self.voltage])

        # Give user info
        print ("Pump's battery level: " +
               str([self.level, str(self.voltage) + " V"]))



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return [self.level, self.voltage]



class Reservoir:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading amount of insulin left in pump reservoir..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 115)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readReservoirLevel")

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Add current reservoir level to pump report
        self.device.reporter.addReservoirLevel(now, self.value)

        # Give user info
        print "Amount of insulin in reservoir: " + str(self.value) + " U"



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class Status:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Overview: Verify pump's status before enabling any desired course of
                  action (e.g. bolusing or enacting a TBR).
        """

        # Read pump status
        self.read()

        # Check if pump is ready to take action
        if not self.value["Normal"]:

            # Give user info
            print "There seems to be a problem with the pump. Try again later."

            return False

        elif self.value["Bolusing"]:

            # Give user info
            print "Pump is bolusing. Try again later."

            return False

        elif self.value["Suspended"]:

            # Give user info
            print "Pump is suspended, but will be asked to resume activity."

            # Resume pump activity
            self.resume()

        # Give user info
        print "Pump status allows desired course of action. Proceeding..."

        return True



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump status..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 206)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readStatus")

        # Give user info
        print "Pump status: " + str(self.value)



    def suspend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUSPEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Suspending pump activity..."
        sleepReason = ("Waiting for pump activity to be suspended... (" +
                       str(self.device.executionDelay) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.executionDelay,
                                     sleepReason = sleepReason,
                                     attempts = 2,
                                     size = 1,
                                     code = 77,
                                     parameters = [1])

        # Make request
        self.device.requester.make()



    def resume(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESUME
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Resuming pump activity..."
        sleepReason = ("Waiting for pump activity to be resumed... (" +
                       str(self.device.executionDelay) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.executionDelay,
                                     sleepReason = sleepReason,
                                     attempts = 2,
                                     size = 1,
                                     code = 77,
                                     parameters = [0])

        # Make request
        self.device.requester.make()



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class Settings:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def verify(self, bolus = None, rate = None, units = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read pump settings
        self.read()

        # Check if pump is ready to take action
        if bolus is not None:

            if bolus > self.values["Max Bolus"]:

                # Give user info
                print ("Pump cannot issue bolus since it is bigger than its " +
                       "maximal allowed bolus. Update the latter before " +
                       "trying again." )

                return False

        elif (rate is not None) and (units is not None):

            if ((units == "U/h") and (rate > self.values["Max Basal"]) or
                (units == "%") and (rate > 200)):

                # Give user info
                print ("Pump cannot issue TBR since it is " +
                       "bigger than its maximal basal rate. Update the " +
                       "latter before trying again.") 

                return False

        # Give user info
        print "Pump settings allow desired course of action. Proceeding..."

        return True



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump settings..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 192)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readSettings")

        # Save pump settings to profile report
        self.device.reporter.storeSettings(self.values)

        # Give user info
        print "Pump settings: " + str(self.values)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return self.values



class BGUnits:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump's BG units..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 137)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readBGU")

        # Store BG units to pump report
        self.device.reporter.storeBGU(self.value)

        # Give user info
        print "Pump's BG units are set to: " + str(self.value)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



    def set(self, value):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update instance's value
        self.value = value



class CarbUnits:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump's carb units..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 136)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readCU")

        # Store BG units to pump report
        self.device.reporter.storeCU(self.value)

        # Give user info
        print "Pump's carb units are set to: " + str(self.value)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



    def set(self, value):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update instance's value
        self.value = value



class TBRUnits:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current TBR in order to extract current units
        self.device.TBR.read()

        # Get units
        self.value = self.device.TBR.get()["Units"]

        # Give user info
        print "Current TBR units: " + self.value



    def set(self, units):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If request is for absolute TBR
        if units == "U/h":
            parameters = [0]

        # If request is for TBR in percentage
        elif units == "%":
            parameters = [1]



        # Define request infos
        info = "Setting TBR units: " + units
        sleepReason = ("Waiting for TBR units to be set... (" +
                       str(self.device.executionDelay) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.executionDelay,
                                     sleepReason = sleepReason,
                                     attempts = 0,
                                     size = 1,
                                     code = 104,
                                     parameters = parameters)

        # Make request
        self.device.requester.make()



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class BGTargets:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize blood glucose targets, times, and units
        self.values = []
        self.times = []
        self.units = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading blood glucose targets from pump..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 159)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readBGTargets")

        # Store BG targets to pump report
        self.device.reporter.storeBGTargets(self.times, self.values, self.units)

        # Store BG units to pump report
        self.device.reporter.storeBGU(self.units)

        # Get number of BG targets read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " blood glucose targets:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                                           str(self.units))



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return [self.times, self.values, self.units]



class ISF:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize insulin sensitivity factors, times, and units
        self.values = []
        self.times = []
        self.units = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading insulin sensitivity factors from pump..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 139)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readISF")

        # Store insulin sensitivities factors to pump report
        self.device.reporter.storeISF(self.times, self.values,
                                      self.units + "/U")

        # Store BG units to pump report
        self.device.reporter.storeBGU(self.units)

        # Get number of ISF read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " ISF:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                   self.units + "/U")



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return [self.times, self.values, self.units]



class CSF:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize carb sensitivity factors, times, and units
        self.values = []
        self.times = []
        self.units = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading carb sensitivity factors from pump..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 138)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readCSF")

        # Store carb sensitivities factors to pump report
        self.device.reporter.storeCSF(self.times, self.values,
                                      self.units + "/U")

        # Store BG units to pump report
        self.device.reporter.storeCU(self.units)

        # Get number of ISF read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " CSF:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                   self.units + "/U")



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return [self.times, self.values, self.units]



class DailyTotals:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize daily totals dictionary
        value = {"Today": None, "Yesterday": None}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading pump daily totals..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 121)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readDailyTotals")

        # Give user info
        print "Daily totals:"
        print json.dumps(self.value, indent = 2, separators = (",", ": "),
                                     sort_keys = True)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.value



class History:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize pump history vector
        self.pages = []



    def evaluate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EVALUATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading current pump history page number..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 157)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readNumberHistoryPages")

        # Give user info
        print "Found " + str(self.size) + " pump history pages."



    def read(self, n = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If no number of pages to read was specified, read all of them
        if not n:

            # Find number of existing history pages
            self.evaluate()

            n = self.size

        # Download user-defined number of most recent pages of pump history
        for i in range(n):

            # Define request infos
            info = "Reading pump history page: " + str(i)

            # Define request
            self.device.requester.define(info = info,
                                  attempts = 2,
                                  size = 2,
                                  code = 128,
                                  parameters = [i])

            # Make request
            self.device.requester.make()

            # Extend known history of pump
            self.pages.extend(self.device.requester.data)

        # Print collected history pages
        print "Read " + str(n) + " page(s) of pump history:"
        print self.pages



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's value
        return self.pages



class Boluses:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize boluses and times vectors
        self.values = []
        self.times = []



    def deliver(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELIVER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        TODO: Check if last bolus stored fits to the one just delivered
        """

        # Verify pump status and settings before doing anything
        if not self.device.status.verify():
            return

        if not self.device.settings.verify(bolus = bolus):
            return

        # Evaluating time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        bolusDeliveryTime = (self.rate * bolus +
                             self.self.device.bolusDelay)

        # Define request infos
        info = "Sending bolus: " + str(bolus) + " U"
        sleepReason = ("Waiting for bolus to be delivered... (" +
                       str(bolusDeliveryTime) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = bolusDeliveryTime,
                                     sleepReason = sleepReason,
                                     attempts = 0,
                                     size = 1,
                                     code = 66,
                                     parameters = [int(bolus /
                                                   self.device.bolusStroke)])

        # Make request
        self.device.requester.make()

        # Read last page and search it for boluses, then store new one to report
        self.read(1)



    def read(self, n = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Download n pages of pump history (or all of it if none is given)
        self.device.history.read(n)

        # Decode pump record
        self.decoder.decodeBolusRecord(code = 1, size = 9)

        # Give user output
        print "Found following bolus entries:"

        for i in range(len(self.values)):

            print str(self.values[i]) + " U (" + str(self.times[i]) + ")"

        # If boluses read, store them
        self.device.reporter.addBoluses(self.times, self.values)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return [self.times, self.values]



class Carbs:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Initialize carbs and times vectors
        self.values = []
        self.times = []



    def read(self, n = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: - Boluses and carbs input seem to be stored exactly at sime time
                in pump.
              - No need to run readBGU and readCU functions, since units are
                encoded in message bytes!
              - No idea how to decode large ISF in mg/dL... information seems to
                be stored in 4th body byte, but no other byte enables
                differenciation between < and >= 256 ? This is not critical,
                since those ISF only represent the ones the BolusWizard used in
                its calculations. The ISF profiles can be read with readISF().

        Warning: - Do not change units for no reason, otherwise treatments will
                   not be read correctly!

        TODOs: - Should we store BGs that were input by the user? Those could
                 correspond to calibration BGs...
        """

        # Download n pages of pump history (or all of it if none is given)
        self.device.history.read(n)

        # Decode pump record
        self.decoder.decodeBolusWizardRecord(code = 91, headSize = 2,
                                             dateSize = 5, bodySize = 13)

        # Give user output
        print "Found following carb entries:"

        for i in range(len(self.values)):

            print str(self.values[i]) + " U (" + str(self.times[i]) + ")"

        # If carbs read, store them
        self.device.reporter.addCarbs(self.times, self.values)



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return [self.times, self.values]



class TBR:

    def __init__(self, device):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give time an instance to the device it should be linked to
        self.device = device

        # Give time a decoder
        self.decoder = decoder.Decoder(device, self)

        # Define current TBR dictionary
        self.value = {"Rate": None, "Units": None, "Duration": None}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading current TBR..."

        # Define request
        self.device.requester.define(info = info,
                                     attempts = 2,
                                     size = 1,
                                     code = 152)

        # Make request
        self.device.requester.make()

        # Decode pump's response
        self.decoder.decode("readTBR")

        # Give user info
        print "Current TBR:"
        print json.dumps(self.value, indent = 2,
                                     separators = (",", ": "),
                                     sort_keys = True)



    def set(self, rate, units, duration, n = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stringify TBR
        TBR = str(rate) + " " + units + " (" + str(duration) + "m)"

        # Give user info regarding the next TBR that will be set
        print ("Trying to set new TBR: " + TBR)

        # First run
        if n:

            # Verify pump status and settings before doing anything
            if not self.device.status.verify():
                return

            if not self.device.settings.verify(rate = rate, units = units):
                return

            # Before issuing any TBR, read the current one
            self.read()

            # Store current TBR
            liveTBR = self.get()

            # Look if a TBR is already set
            if ((liveTBR["Rate"] != 0) and (liveTBR["Units"] == "U/h") or
                (liveTBR["Rate"] != 100) and (liveTBR["Units"] == "%")):

                # Give user info
                print ("TBR must be canceled before issuing a new one...")

                # Set TBR to zero. (It is crucial here to use the precedent
                # units, otherwise it would not work! Using the cancel method
                # would result in a useless additional reading of TBR units...)
                self.set(0, liveTBR["Units"], 0, False)

            # Look if units match up
            if units != liveTBR["Units"]:

                # Give user info
                print "Old and new TBR units do not match. Adjusting them..."

                # Modify units as wished by the user
                self.device.TBRUnits.set(units)

        # If request is for absolute TBR
        if units == "U/h":
            code = 76
            parameters = [0,
                          int(round(rate / self.device.basalStroke * 2.0)),
                          int(duration / self.device.timeBlock)]

        # If request is for TBR in percentage
        elif units == "%":
            code = 105
            parameters = [int(round(rate)),
                          int(duration / self.device.timeBlock)]

        # Get current time
        now = datetime.datetime.now()

        # Format time at which TBR is requested
        now = lib.formatTime(now)

        # Define request infos
        info = "Setting TBR: " + TBR
        sleepReason = ("Waiting for TBR [" + TBR + "] to be set... (" +
                       str(self.device.executionDelay) + "s)")

        # Define request
        self.device.requester.define(info = info,
                                     sleep = self.device.executionDelay,
                                     sleepReason = sleepReason,
                                     attempts = 0,
                                     size = 1,
                                     code = code,
                                     parameters = parameters)

        # Make request
        self.device.requester.make()

        # Give user info
        print "Verifying if new TBR was correctly set..."

        # Verify that the TBR was correctly issued by reading current TBR on
        # pump
        self.read()

        # Store current TBR
        liveTBR = self.get()

        # Compare to expectedly set TBR
        if ((liveTBR["Rate"] == rate) and
            (liveTBR["Units"] == units) and
            (liveTBR["Duration"] == duration)):

            # Give user info
            print "New TBR correctly set: " + TBR
            print "Storing it..."

            # Add bolus to insulin report
            self.device.reporter.addTBR(now, rate, units, duration)

        # FIXME: Otherwise, quit
        else:
            sys.exit("New TBR could not be correctly set. " +
                     "Exiting...")



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return instance's values
        return self.value



    def cancel(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CANCEL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current units
        self.device.TBRUnits.read()

        # Store them
        units = self.device.TBRUnits.get()

        # Cancel on-going TBR
        if units == "U/h":
            self.set(0, units, 0, False)

        elif units == "%":
            self.set(100, units, 0, False)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a pump for me
    pump = Pump()

    # Start dialogue with pump
    pump.start()

    # Read bolus history of pump
    #pump.time.read()

    # Read pump model
    #pump.model.read()

    # Read pump firmware version
    #pump.firmware.read()

    # Read pump battery level
    #pump.battery.read()

    # Read remaining amount of insulin in pump
    #pump.reservoir.read()

    # Read pump status
    #pump.status.read()
    #pump.status.verify()
    #pump.status.suspend()
    #pump.status.resume()

    # Read pump settings
    #pump.settings.read()
    #pump.settings.verify()

    # Push button on pump
    #pump.buttons.push("EASY")
    #pump.buttons.push("ESC")
    #pump.buttons.push("ACT")
    #pump.buttons.push("UP")
    #pump.buttons.push("DOWN")

    # Read daily totals on pump
    #pump.dailyTotals.read()

    # Read BG units set in pump's bolus wizard
    #pump.BGUnits.read()

    # Read carb units set in pump's bolus wizard
    #pump.carbUnits.read()

    # Read blood glucose targets stored in pump
    #pump.BGTargets.read()

    # Read pump history
    #pump.history.read()

    # Read insulin sensitivity factors stored in pump
    #pump.ISF.read()

    # Read carb sensitivity factors stored in pump
    #pump.CSF.read()

    # Read boluses from pump history
    #pump.boluses.read()

    # Read carbs from pump history
    #pump.carbs.read()

    # Send bolus to pump
    #pump.boluses.deliver(0.1)

    # Read current TBR units
    #pump.TBRUnits.read()

    # Read current TBR
    #pump.TBR.read()

    # Send TBR to pump
    #pump.TBR.set(5, "U/h", 30)
    #pump.TBR.set(50, "%", 90)
    #pump.TBR.cancel()

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
