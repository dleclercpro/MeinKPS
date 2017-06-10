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
#       - No point in reissuing same TBR
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
                      "TBR": TBRU(self)}

        # Give the pump a BG targets instance
        self.BGTargets = BGTargets(self)

        # Give the pump an ISF instance
        self.ISF = ISF(self)

        # Give the pump a CSF instance
        self.CSF = CSF(self)

        # Give the pump a basal profile instance
        self.basalProfile = BasalProfile(self)

        # Give the pump a daily totals instance
        self.dailyTotals = DailyTotals(self)

        # Give the pump a history instance
        self.history = History(self)

        # Give the pump a bolus instance
        self.bolus = Bolus(self)

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
        delta += datetime.timedelta(minutes = 2)

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
        print "Pump's status allows desired course of action. Proceeding..."

        return True



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

            if bolus > self.value["Max Bolus"]:

                # Give user info
                print ("Pump cannot issue bolus since it is bigger than its " +
                       "maximal allowed bolus. Update the latter before " +
                       "trying again." )

                return False

        elif (rate is not None) and (units is not None):

            if ((units == "U/h") and (rate > self.value["Max Basal"]) or
                (units == "%") and (rate > 200)):

                # Give user info
                print ("Pump cannot issue TBR since it is " +
                       "bigger than its maximal basal rate. Update the " +
                       "latter before trying again.") 

                return False

        # Give user info
        print "Pump's settings allow desired course of action. Proceeding..."

        return True



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



class TBRU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.SetPumpTBRU(pump)

        # Link with pump
        self.pump = pump



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current TBR in order to extract current units
        self.pump.TBR.read()

        # Get units
        self.value = self.pump.TBR.value["Units"]

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



class BasalProfile(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = None

        # Link with its respective command
        self.command = commands.ReadPumpBasalProfile(pump)



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
                        "TBR": records.TBRRecord(pump),
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

        # Compute number of bytes read
        size = len(page)

        # Print collected history pages
        print "Read " + str(n) + " page(s) [or " + str(size) + " byte(s)]:"
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



    def deliver(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELIVER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # TODO: Check if last bolus stored fits to the one just delivered

        # Verify pump status and settings before doing anything
        if not self.pump.status.verify():
            return

        if not self.pump.settings.verify(bolus):
            return

        # Do command
        self.command.do(bolus)

        # Update reports by reading last page(s) of pump history
        self.pump.history.update()



class TBR(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize basal characteristics
        self.stroke = 0.025 # Pump basal stroke rate (U/h)
        self.timeBlock = 30 # Time block (m) used by pump for basal durations

        # Initialize current TBR
        self.value = None

        # Link with its respective command
        self.commands = {"Read": commands.ReadPumpTBR(pump),
                         "Set": commands.SetPumpTBR(pump)}

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
        print "Current TBR: " + str(self.value)



    def verify(self, TBR):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: on-going TBR with % units apparently need to be canceled before
              another TBR with same units can be set.
        """

        # Define theoretical max basal
        minTBR = {"U/h": 0, "%": 0}
        maxTBR = {"U/h": 35, "%": 200}

        # Verify size of TBR
        if (TBR["Rate"] < minTBR[TBR["Units"]] or
            TBR["Rate"] > maxTBR[TBR["Units"]]):

            # Raise error
            raise errors.TBRIncorrect(TBR["Rate"], TBR["Units"])

        # Verify if TBR duration is a multiple of 30
        if TBR["Duration"] % 30:

            # Raise error
            raise errors.TBRIncorrectDuration(TBR["Duration"])

        # Verify pump status and settings before doing anything
        if not self.pump.status.verify():
            return

        if not self.pump.settings.verify(None, TBR["Rate"], TBR["Units"]):
            return

        # Before issuing any TBR, read the current one
        self.read()

        # Look if a TBR is already set
        if (self.value["Duration"] != 0 and self.value["Units"] == "%" or
            self.value["Units"] != TBR["Units"]):

            # Give user info
            print ("TBR must be canceled before doing anything...")

            # Cancel TBR
            self.cancel(self.value["Units"])

        # Look if units match up
        if self.value["Units"] != TBR["Units"]:

            # Give user info
            print "TBR units do not match. Adjusting them..."

            # Modify units as wished by the user
            self.pump.units["TBR"].set(TBR["Units"])



    def set(self, rate, units, duration, cancel = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define new TBR
        newTBR = {"Rate": rate,
                  "Units": units,
                  "Duration": duration}

        # Give user info
        print "Trying to set new TBR:"

        # Show new TBR
        self.show(newTBR)

        # Verify if TBR can be set on pump
        if not cancel:
            self.verify(newTBR)

        # Do command
        self.commands["Set"].do(newTBR)

        # Update reports by reading last page(s) of pump history
        self.pump.history.update()

        # Give user info
        print "Verifying if new TBR was correctly set..."

        # Verify that the TBR was correctly issued by reading current TBR on
        # pump
        self.read()

        # Compare to expectedly set TBR
        if newTBR == self.value:

            # Give user info
            print "New TBR correctly set:"

            # Show TBR
            self.show(newTBR)

        # Otherwise, quit
        else:

            # Give user info
            print "Desired and actual TBRs:"

            # Show TBRs
            self.show(newTBR)
            self.show(self.value)

            # Raise error
            raise errors.TBRFail()



    def cancel(self, units = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CANCEL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units if not already provided
        if units is None:

            # Read current units
            self.pump.units["TBR"].read()

            # Get them
            units = self.pump.units["TBR"].value

        # Cancel on-going TBR
        if units == "U/h":
            self.set(0, units, 0, True)

        elif units == "%":
            self.set(100, units, 0, True)



    def show(self, TBR):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show TBR components
        print ("[" + str(TBR["Rate"]) + " " +
                         TBR["Units"] + " (" +
                     str(TBR["Duration"]) + " m)]")



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
    pump.time.read()

    # Read pump model
    pump.model.read()

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

    # Read current TBR units
    #pump.units["TBR"].read()

    # Set TBR units
    #pump.units["TBR"].set("U/h")
    #pump.units["TBR"].set("%")

    # Read BG targets stored in pump
    #pump.BGTargets.read()

    # Read insulin sensitivity factors stored in pump
    #pump.ISF.read()

    # Read carb sensitivity factors stored in pump
    #pump.CSF.read()

    # Read basal profile stored in pump
    #pump.basalProfile.read("Standard")
    #pump.basalProfile.read("A")
    #pump.basalProfile.read("B")

    # Read daily totals on pump
    #pump.dailyTotals.read()

    # Read pump history
    #pump.history.read(1)

    # Send bolus to pump
    #pump.bolus.deliver(0.1)

    # Read current TBR
    #pump.TBR.read()

    # Send TBR to pump
    #pump.TBR.set(0.05, "U/h", 30)
    #pump.TBR.set(34.95, "U/h", 30)
    #pump.TBR.set(1, "%", 90)
    #pump.TBR.set(99, "%", 90)
    #pump.TBR.cancel()

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
