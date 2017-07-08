#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    pump

    Author:   David Leclerc

    Version:  0.3

    Date:     20.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains a handful of commands that can be
              sent wirelessly to a Medtronic RF Paradigm pump through a Carelink
              USB stick. Please use carefully!

    Notes:    - When the battery is low, the stick will not be able to
                communicate with the pump anymore.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO: - Test with alarm set on pump
#       - Test with pump reservoir empty or almost empty
#       - Deal with timezones, DST, year switch
#       - Run series of tests overnight
#       - No point in reissuing same TB
#       - Decode square/dual boluses
#       - Add "change battery" suggestion
#       - Reduce session time if looping every 5 minutes
#       - What if session of commands is longer than pump's remaining RF
#         communication time? Detect long session time and compare it with 
#         remaining one?
#       - Bolus need to be checked after being enacted!



# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import commands
import stick
import records
import reporter
import errors



# Define a reporter
Reporter = reporter.Reporter()



class Pump(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

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

        # Give the pump units
        self.units = {"BG": BGU(self),
                      "C": CU(self),
                      "TB": TBU(self)}

        # Give the pump a BG targets instance
        self.BGTargets = BGTargets(self)

        # Give the pump an ISF instance
        self.ISF = ISF(self)

        # Give the pump a CSF instance
        self.CSF = CSF(self)

        # Give the pump a basal profile instance
        self.basal = Basal(self)

        # Give the pump a daily totals instance
        self.dailyTotals = DailyTotals(self)

        # Give the pump a history instance
        self.history = History(self)

        # Give the pump a bolus instance
        self.bolus = Bolus(self)

        # Give the pump a TB instance
        self.TB = TB(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Starting dialogue with pump..."

        # Connect to stick
        self.stick.connect()

        # Start stick
        self.stick.start()

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

        # Disconnect from stick
        self.stick.disconnect()



class Power(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with its respective command
        self.command = commands.PowerPump(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump's report
        Reporter.load("history.json")

        # Read last time pump's radio transmitter was power up
        then = Reporter.getEntry(["Pump"], "Power")

        # Format time
        then = lib.formatTime(then)

        # Return last power up time
        return then



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current time
        now = datetime.datetime.now()

        # Compute time since last power up
        delta = now - self.read()

        # Generate a datetime object for the pump's RF sessions' length
        session = datetime.timedelta(minutes = self.command.sessionTime)

        # Time buffer added to delta in order to eliminate dead calls at the end
        # of an RF session with the pump
        delta += datetime.timedelta(minutes = 5)

        # Power up pump if necessary
        if delta > session:

            # Give user info
            print "Pump's radio transmitter will be turned on..."

            # Power up pump's RF transmitter
            self.do()

        else:

            # Give user info
            print ("Pump's radio transmitter is already on. Remaining time: " +
                   str(self.command.sessionTime - delta.seconds / 60) + " m")



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()



class Time(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpTime(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Pump time: " + self.value



class Model(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpModel(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Pump model: " + str(self.value)



class Firmware(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpFirmware(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Pump firmware: " + str(self.value)



class Buttons(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with its respective command
        self.command = commands.PushPumpButton(pump)



    def push(self, button):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PUSH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do(button)

        # Give user info
        print "Pushed button: " + button



class Battery(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: The battery seems to stop communicating after some values of 1.2 V
              have been read. Set a warning at this point?
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpBattery(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Pump's battery level: " + str(self.value) + " V"



class Reservoir(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpReservoir(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Remaining amount of insulin: " + str(self.value) + " U"



class Status(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.value = None

        # Link with its respective commands
        self.commands = {"Read": commands.ReadPumpStatus(pump),
                         "Suspend": commands.SuspendPump(pump),
                         "Resume": commands.ResumePump(pump)}



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Overview: Verify pump's status before enabling any desired course of
                  action (e.g. bolusing or enacting a TB).
        """

        # Read pump status
        self.read()

        # Check if pump is ready to take action
        if not self.value["Normal"]:

            # Raise error
            raise errors.StatusAbnormal

        elif self.value["Bolusing"]:

            # Raise error
            raise errors.StatusBolusing

        elif self.value["Suspended"]:

            # Raise error
            raise errors.StatusSuspended

        # Give user info
        print "Pump's status allows desired course of action. Proceeding..."



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.commands["Read"].do()

        # Get command response
        self.value = self.commands["Read"].response

        # Give user info
        print "Pump's status: " + str(self.value)



    def suspend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUSPEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.commands["Suspend"].do()



    def resume(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESUME
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.commands["Resume"].do()



class Settings(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpSettings(pump)



    def verify(self, TB = None, bolus = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read pump settings
        self.read()

        # If TB is asked for, but exceeds max settings
        if (TB is not None and TB["Units"] == "U/h" and
            TB["Rate"] > self.value["Max Basal"]):

            # Raise error
            raise errors.SettingsMaxBasalExceeded

        # If bolus is asked for, but exceeds max settings
        elif bolus is not None and bolus > self.value["Max Bolus"]:

            # Raise error
            raise errors.SettingsMaxBolusExceeded

        # Give user info
        print "Pump's settings allow desired course of action. Proceeding..."



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Pump settings: " + str(self.value)



class Unit(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Show user units
        self.show()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get unit name
        unit = self.__class__.__name__

        # Give user info
        print "Pump's '" + unit + "' set to: " + self.value



class BGU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadPumpBGU(pump)



class CU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadPumpCU(pump)



class TBU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.SetPumpTBU(pump)

        # Link with pump
        self.pump = pump



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current TB in order to extract current units
        self.pump.TB.read()

        # Get units
        self.value = self.pump.TB.value["Units"]

        # Show user units
        self.show()



    def set(self, units):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do(units)



class BGTargets(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = None

        # Link with its respective command
        self.command = commands.ReadPumpBGTargets(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.values = self.command.response

        # Get number of BG targets read
        n = len(self.values["Times"])

        # Give user info
        print "Found " + str(n) + " BG target(s):"

        # Print targets
        for i in range(n):
            print (self.values["Times"][i] + " - " +
                   str(self.values["Targets"][i]) + " " +
                   self.values["Units"])



class ISF(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = None

        # Link with its respective command
        self.command = commands.ReadPumpISF(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.values = self.command.response

        # Get number of ISF read
        n = len(self.values["Times"])

        # Give user info
        print "Found " + str(n) + " ISF(s):"

        # Print factors
        for i in range(n):
            print (self.values["Times"][i] + " - " +
                   str(self.values["Factors"][i]) + " " +
                   self.values["Units"])



class CSF(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = None

        # Link with its respective command
        self.command = commands.ReadPumpCSF(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.values = self.command.response

        # Get number of ISF read
        n = len(self.values["Times"])

        # Give user info
        print "Found " + str(n) + " CSF(s):"

        # Print factors
        for i in range(n):
            print (self.values["Times"][i] + " - " +
                   str(self.values["Factors"][i]) + " " +
                   self.values["Units"])



class Basal(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = None

        # Link with its respective command
        self.command = commands.ReadPumpBasal(pump)



    def read(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do(profile)

        # Get command response
        self.values = self.command.response

        # Get number of rates read
        n = len(self.values["Times"])

        # Give user info
        print "Found " + str(n) + " rates for bolus profile '" + profile + "':"

        # Print rates
        for i in range(n):
            print (self.values["Times"][i] + " - " +
                   str(self.values["Rates"][i]) + " U/h")



class DailyTotals(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpDailyTotals(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.value = self.command.response

        # Give user info
        print "Daily totals: " + str(self.value)



class History(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize number of pump history pages
        self.n = None

        # Initialize pump history pages
        self.pages = None

        # Link with its respective command
        self.commands = {"Measure": commands.MeasurePumpHistory(pump),
                         "Read": commands.ReadPumpHistory(pump)}

        # Link with all possible records
        self.records = {"Suspend": records.SuspendRecord(pump),
                        "Resume": records.ResumeRecord(pump),
                        "TB": records.TBRecord(pump),
                        "Bolus": records.BolusRecord(pump),
                        "Carbs": records.CarbsRecord(pump)}



    def measure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MEASURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.commands["Measure"].do()

        # Get command response
        self.n = self.commands["Measure"].response

        # Give user info
        print "Found " + str(self.n) + " pump history pages."



    def read(self, n = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset pages
        self.pages = []

        # If no number of pages to read was specified, read all of them
        if n is None:

            # Find number of existing history pages
            self.measure()

            # Assign number of pages found
            n = self.n

        # Download n most recent pages of pump history
        for i in range(n):

            # Do command
            self.commands["Read"].do(i)

            # Get page
            page = self.commands["Read"].response

            # Extend known history of pump
            self.pages.extend(page)

        # Print collected history pages
        print "Read " + str(n) + " page(s) [or " + str(len(page)) + " byte(s)]:"
        print self.pages



    def update(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UDPATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read number of pages
        self.measure()

        # If only one page, read it
        if self.n == 1:
            self.read(1)

        # Otherwise, read last two
        else:
            self.read(2)



class Bolus(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize bolus characteristics
        self.stroke = 0.1  # Pump bolus stroke (U)
        self.rate   = 40.0 # Bolus delivery rate (s/U)
        self.sleep  = 5    # Time (s) to wait after bolus delivery

        # Link with its respective command
        self.command = commands.DeliverPumpBolus(pump)

        # Link with pump
        self.pump = pump



    def last(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LAST
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report
        Reporter.load("treatments.json")

        # Find last bolus
        [t, bolus] = Reporter.getLastEntry(["Boluses"])

        # Give user info
        print "Last bolus: " + str(bolus) + " U (" + t + ")"

        # Return it
        return [t, bolus]



    def deliver(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELIVER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify pump status
        self.pump.status.verify()

        # Verify pump settings
        self.pump.settings.verify(None, bolus)

        # Get current time
        now = datetime.datetime.now()

        # Do command
        self.command.do(bolus)

        # Update reports by reading last page(s) of pump history
        self.pump.history.update()

        # Read last bolus stored
        [lastTime, lastBolus] = self.last()

        # Read current pump time
        self.pump.time.read()

        # Get it
        pumpNow = self.pump.time.value

        # Format times
        lastTime_ = lib.formatTime(lastTime)
        pumpNow_ = lib.formatTime(pumpNow)

        # Get time difference (s) between current pump time and last bolus
        dt = (pumpNow_ - lastTime_).seconds

        # Compute bolus enactment time
        bolusDuration = self.rate * lastBolus + self.sleep

        # Define error margin (s)
        e = 1.0 * 60

        # Check for last bolus time
        if dt > bolusDuration + e:

            # Raise error
            raise errors.BolusBadTime(lastTime, pumpNow)

            # Exit
            return

        # Check for last bolus amount
        if lastBolus != bolus:

            # Raise error
            raise errors.BolusBadAmount(lastBolus, bolus)

            # Exit
            return

        # Give user info
        print "Bolus was delivered successfully!"



class TB(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize basal characteristics
        self.stroke = 0.025 # Pump basal stroke rate (U/h)
        self.timeBlock = 30 # Time block (m) used by pump for basal durations

        # Initialize current TB
        self.value = None

        # Link with its respective command
        self.commands = {"Read": commands.ReadPumpTB(pump),
                         "Set": commands.SetPumpTB(pump)}

        # Link with pump
        self.pump = pump



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.commands["Read"].do()

        # Get command response
        self.value = self.commands["Read"].response

        # Give user info
        print "Current TB: " + str(self.value)



    def verify(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: on-going TB with % units apparently need to be canceled before
              another TB with same units can be set.
        """

        # TODO: Test problematic cases where pump status/settings do not allow
        #       desired course of action

        # Verify size of TB
        if (TB["Rate"] < {"U/h": 0, "%": 0}[TB["Units"]] or
            TB["Rate"] > {"U/h": 35, "%": 200}[TB["Units"]]):

            # Raise error
            raise errors.TBBadRate(TB)

        # Verify if duration is a multiple of 30
        if TB["Duration"] % 30:

            # Raise error
            raise errors.TBBadDuration(TB)

        # Verify pump status
        self.pump.status.verify()

        # Verify pump settings
        self.pump.settings.verify(TB)

        # Before issuing any TB, read the current one
        self.read()

        # Look if a TB is already set
        if (self.value["Duration"] != 0 and self.value["Units"] == "%" or
            self.value["Units"] != TB["Units"]):

            # Give user info
            print ("TB must be canceled before doing anything...")

            # Cancel TB
            self.cancel(self.value["Units"])

        # Look if units match up
        if self.value["Units"] != TB["Units"]:

            # Give user info
            print "TB units do not match. Adjusting them..."

            # Modify units as wished by the user
            self.pump.units["TB"].set(TB["Units"])



    def round(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ROUND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "New TB:"

        # Show new TB
        self.show(TB)

        # If U/h
        if TB["Units"] == "U/h":

            # Round
            TB["Rate"] = round(round(TB["Rate"] / self.stroke) * self.stroke, 2)

        # If %
        elif TB["Units"] == "%":

            # Round
            TB["Rate"] = round(TB["Rate"])

        # Give user info
        print "New rounded TB:"

        # Show new rounded TB
        self.show(TB)



    def set(self, rate, units, duration, cancel = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define new TB
        newTB = {"Rate": rate,
                 "Units": units,
                 "Duration": duration}

        # Verify if TB can be set on pump
        if not cancel:
            self.verify(newTB)

        # Round new TB to fit pump's range
        self.round(newTB)

        # Do command
        self.commands["Set"].do(newTB)

        # Update reports by reading last page(s) of pump history
        self.pump.history.update()

        # Give user info
        print "Verifying if new TB was correctly set..."

        # Verify that the TB was correctly issued by reading current TB on
        # pump
        self.read()

        # Compare to expectedly set TB
        if newTB == self.value:

            # Give user info
            print "New TB correctly set:"

            # Show TB
            self.show(newTB)

        # Otherwise, quit
        else:

            # Give user info
            print "Desired and actual TBs:"

            # Show TBs
            self.show(newTB)
            self.show(self.value)

            # Raise error
            raise errors.TBFail()



    def cancel(self, units = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CANCEL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units if not already provided
        if units is None:

            # Read current units
            self.pump.units["TB"].read()

            # Get them
            units = self.pump.units["TB"].value

        # Cancel on-going TB
        if units == "U/h":
            self.set(0, units, 0, True)

        elif units == "%":
            self.set(100, units, 0, True)



    def show(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show TB components
        print ("[" + str(TB["Rate"]) + " " +
                         TB["Units"] + " (" +
                     str(TB["Duration"]) + " m)]")



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

    # Read pump time
    #pump.time.read()

    # Read pump model
    #pump.model.read()

    # Read pump firmware version
    #pump.firmware.read()

    # Push button on pump
    #pump.buttons.push("EASY")
    #pump.buttons.push("ESC")
    #pump.buttons.push("ACT")
    #pump.buttons.push("UP")
    #pump.buttons.push("DOWN")

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

    # Read BG units set in pump's bolus wizard
    #pump.units["BG"].read()

    # Read carb units set in pump's bolus wizard
    #pump.units["C"].read()

    # Read current TB units
    #pump.units["TB"].read()

    # Set TB units
    #pump.units["TB"].set("U/h")
    #pump.units["TB"].set("%")

    # Read BG targets stored in pump
    #pump.BGTargets.read()

    # Read insulin sensitivity factors stored in pump
    #pump.ISF.read()

    # Read carb sensitivity factors stored in pump
    #pump.CSF.read()

    # Read basal profile stored in pump
    #pump.basal.read("Standard")
    #pump.basal.read("A")
    #pump.basal.read("B")

    # Read daily totals on pump
    #pump.dailyTotals.read()

    # Read pump history
    pump.history.read(2)

    # Send bolus to pump
    #pump.bolus.deliver(0.6)

    # Read current TB
    #pump.TB.read()

    # Send TB to pump
    #pump.TB.set(0.3, "U/h", 30)
    #pump.TB.set(34.95, "U/h", 30)
    #pump.TB.set(1, "%", 90)
    #pump.TB.set(99, "%", 90)
    #pump.TB.cancel()

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
