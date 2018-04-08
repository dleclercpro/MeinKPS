#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    pump

    Author:   David Leclerc

    Version:  0.4

    Date:     20.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains a handful of commands that can be
              sent wirelessly to a Medtronic MiniMed insulin pump, using a Texas
              Instruments CC1111 USB radio stick. Please use carefully!

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO: - Deal with timezones, DST, year switch
#       - No point in reissuing same TB
#       - Decode square/dual boluses
#       - Bolus needs to be checked after being enacted!



# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import errors
import commands
import stick
import records
import reporter



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

        # Give the pump a battery instance
        self.battery = Battery(self)

        # Give the pump a reservoir instance
        self.reservoir = Reservoir(self)

        # Give the pump buttons
        self.buttons = Buttons(self)

        # Give the pump a status instance
        self.status = Status(self)

        # Give the pump a settings instance
        self.settings = Settings(self)

        # Give the pump units
        self.units = {"BG": BGUnits(self),
                      "Carbs": CarbsUnits(self),
                      "TB": TBUnits(self)}

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

        # Give the pump a basal profile instance
        self.basal = Basal(self)

        # Give the pump a TB instance
        self.TB = TB(self)

        # Give the pump a bolus instance
        self.bolus = Bolus(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print "Starting pump..."

        # Start stick (tune it by giving it access to read model command)
        self.stick.start(self)

        # Power pump's radio transmitter if necessary
        self.power.verify()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print "Stopping pump..."

        # Stop stick
        self.stick.stop()



class PumpComponent(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store pump
        self.pump = pump

        # Initialize name
        self.name = self.__class__.__name__

        # Initialize command
        self.command = None

        # Initialize value
        self.value = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get value
        self.value = self.command.run()

        # Show it
        self.show()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print "-- " + self.name + " --"
        print self.value



class Power(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize power component
        super(Power, self).__init__(pump)

        # Define default session length (m)
        self.session = 10

        # Instanciate corresponding command
        self.command = commands.PowerPump(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read last time pump's radio transmitter was powered up
        self.value = lib.formatTime(Reporter.get("pump.json", [], "Power"))



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read last power up time
        self.read()

        # Get current time
        now = datetime.datetime.now()

        # Compute time since last power up
        delta = now - self.value

        # Generate a datetime object for the pump's RF sessions' length
        session = datetime.timedelta(minutes = self.session)

        # Time buffer added to delta in order to eliminate dead calls at the end
        # of an RF session with the pump
        delta += datetime.timedelta(minutes = 2)

        # Power up pump if necessary
        if delta > session:

            # Info
            print "Pump's radio transmitter will be turned on..."

            # Power up pump's RF transmitter
            self.command.run(self.session)

        else:

            # Info
            print ("Pump's radio transmitter is already on. Remaining time: " +
                   str(self.session - delta.seconds / 60) + " m")



class Time(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time component
        super(Time, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpTime(pump)



class Model(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize model component
        super(Model, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpModel(pump)



class Firmware(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize firmware component
        super(Firmware, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpFirmware(pump)



class Buttons(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define name
        self.name = "Last button pushed"

        # Define command
        self.command = commands.PushPumpButton(pump)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



    def push(self, button):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PUSH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store last button pushed
        self.value = button

        # Push button
        self.command.run(button)



class Battery(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: The battery seems to stop communicating after some values of
                  1.2 V have been read. Set a warning at this point?
        """

        # Initialize battery component
        super(Battery, self).__init__(pump)

        # Define name
        self.name = "Battery level (V)"

        # Define command
        self.command = commands.ReadPumpBattery(pump)



class Reservoir(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize reservoir component
        super(Reservoir, self).__init__(pump)

        # Define name
        self.name = "Reservoir level (U)"

        # Define command
        self.command = commands.ReadPumpReservoir(pump)



class Status(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize status component
        super(Status, self).__init__(pump)

        # Instanciate corresponding commands
        self.commands = {"Read": commands.ReadPumpStatus(pump),
                         "Suspend": commands.SuspendPump(pump),
                         "Resume": commands.ResumePump(pump)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get status
        self.value = self.commands["Read"].run()

        # Show it
        self.show()



    def suspend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUSPEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Suspend pump
        self.commands["Suspend"].run()



    def resume(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESUME
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Resume pump
        self.commands["Resume"].run()



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify pump's status before enabling any desired course of action
            (e.g. bolusing or enacting a TB).
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

        # Info
        print "Pump's status allows desired course of action. Proceeding..."



class Settings(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize settings component
        super(Settings, self).__init__(pump)

        # Define name
        self.name = "Pump settings"

        # Define command
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

        # Info
        print "Pump's settings allow desired course of action. Proceeding..."



class BGUnits(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units component
        super(BGUnits, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpBGUnits(pump)



class CarbsUnits(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units component
        super(CarbsUnits, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpCarbsUnits(pump)



class TBUnits(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units component
        super(TBUnits, self).__init__(pump)

        # Define command
        self.command = commands.SetPumpTBUnits(pump)



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

        # Run command
        self.command.run(units)



class BGTargets(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize BG targets component
        super(BGTargets, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpBGTargets(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of BG targets read
        n = len(self.value["Times"])

        # Info
        print "Found " + str(n) + " BG target(s):"

        # Print targets
        for i in range(n):

            # Format info
            print (self.value["Times"][i] + " - " +
                   str(self.value["Targets"][i]) + " " +
                   self.value["Units"])



class ISF(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize ISF component
        super(ISF, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpISF(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of ISF read
        n = len(self.value["Times"])

        # Info
        print "Found " + str(n) + " ISF(s):"

        # Print factors
        for i in range(n):

            # Format info
            print (self.value["Times"][i] + " - " +
                   str(self.value["Factors"][i]) + " " +
                   self.value["Units"])



class CSF(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize CSF component
        super(CSF, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpCSF(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of ISF read
        n = len(self.value["Times"])

        # Info
        print "Found " + str(n) + " CSF(s):"

        # Print factors
        for i in range(n):

            # Format info
            print (self.value["Times"][i] + " - " +
                   str(self.value["Factors"][i]) + " " +
                   self.value["Units"])



class DailyTotals(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize daily totals component
        super(DailyTotals, self).__init__(pump)

        # Define command
        self.command = commands.ReadPumpDailyTotals(pump)



class History(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            HOTFIX: suspend/resume records last to avoid corrupted detection of
                    bolus records
        """

        # Initialize history component
        super(History, self).__init__(pump)

        # Initialize history size
        self.size = None

        # Initialize history pages
        self.pages = None

        # Define commands
        self.commands = {"Measure": commands.ReadPumpHistorySize(pump),
                         "Read": commands.ReadPumpHistoryPage(pump)}

        # Define possible records
        self.records = [records.TBRecord(pump),
                        records.BolusRecord(pump),
                        records.CarbsRecord(pump),
                        records.SuspendRecord(pump),
                        records.ResumeRecord(pump)]



    def measure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MEASURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get history size
        self.size = self.commands["Measure"].run()

        # Info
        print "Found " + str(self.size) + " pump history pages."



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
            n = self.size

        # Download n most recent pages of pump history (reverse page numbers to
        # ensure data is downloaded from oldest to most recent, without data
        # corruption between pages)
        for i in reversed(range(n)):

            # Get page
            page = self.commands["Read"].run(i)

            # Extend known history of pump if page passes CRC check
            self.pages.extend(page)

        # Show pages
        self.show()

        # Decode them
        self.decode()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print ("Read page(s) [" + str(len(self.pages)) + " byte(s)]:")

        # Print downloaded history pages
        print self.pages



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print "Finding records..."

        # Initialize pages
        pages = self.pages

        # Go through records
        for record in self.records:

            # Find record within pages, decode it, and store remaining data
            pages = record.find(pages)



    def update(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UDPATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read number of pages
        self.measure()

        # If only one page
        if self.size == 1:

            # Read it
            self.read(1)

        # Otherwise
        else:

            # Read last two
            self.read(2)



class Basal(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize basal component
        super(Basal, self).__init__(pump)

        # Define command
        self.commands = {
            "Standard": commands.ReadPumpBasalProfileStandard(pump),
            "A": commands.ReadPumpBasalProfileA(pump),
            "B": commands.ReadPumpBasalProfileB(pump)}

        # Initialize basal characteristics
        self.stroke = 0.025 # Pump basal stroke rate (U/h)
        self.time = 30 # Time block (m) used by pump for basal durations



    def read(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store profile
        self.profile = profile

        # Select profile
        # Standard
        if profile == "Standard":

            # Get basal
            self.value = self.commands["Standard"].run()

        elif profile == "A":

            # Get basal
            self.value = self.commands["A"].run()

        elif profile == "B":

            # Get basal
            self.value = self.commands["B"].run()

        # Show it
        self.show()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of rates read
        n = len(self.value["Times"])

        # Info
        print ("Found " + str(n) + " rates for bolus profile '" + self.profile +
               "':")

        # Print rates
        for i in range(n):

            # Format info
            print (self.value["Times"][i] + " - " +
                   str(self.value["Rates"][i]) + " U/h")



class TB(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize TB component
        super(TB, self).__init__(pump)

        # Instanciate corresponding command
        self.commands = {"Read": commands.ReadPumpTB(pump),
                         "Set Absolute": commands.SetPumpAbsoluteTB(pump),
                         "Set Percentage": commands.SetPumpPercentageTB(pump)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current TB
        self.value = self.commands["Read"].run()

        # Show it
        self.show()



    def show(self, TB = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # No TB given
        if TB is None:

            # Set it to read one
            TB = self.value

        # Info
        print ("TB: [" + str(TB["Rate"]) + " " + TB["Units"] + " (" +
                         str(TB["Duration"]) + " m)]")



    def verify(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: on-going TB with % units apparently need to be canceled before
                  another TB with same units can be set.
        """

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
        self.pump.settings.verify(TB = TB)

        # Before issuing any TB, read the current one
        self.read()

        # Look if a TB is already set
        if (self.value["Units"] == "%" and self.value["Duration"] != 0 or
            self.value["Units"] != TB["Units"]):

            # Info
            print "TB must be canceled before doing anything..."

            # Cancel TB
            self.cancel(self.value["Units"])

        # Look if units match up
        if self.value["Units"] != TB["Units"]:

            # Info
            print "TB units do not match. Adjusting them..."

            # Modify units as wished by the user
            self.pump.units["TB"].set(TB["Units"])



    def adjust(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADJUST
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        print "Adjusting TB:"

        # Show TB
        self.show(TB)

        # Round rate
        # U/h
        if TB["Units"] == "U/h":

            # Do it
            TB["Rate"] = round(round(TB["Rate"] / self.pump.basal.stroke) *
                                                  self.pump.basal.stroke, 2)

        # %
        elif TB["Units"] == "%":

            # Do it
            TB["Rate"] = round(TB["Rate"])

        # Round duration
        TB["Duration"] = (round(TB["Duration"] / self.pump.basal.time) *
                                                 self.pump.basal.time)

        # Info
        print "To:"

        # Show adjust TB
        self.show(TB)

        # Return adjusted TB
        return TB



    def set(self, rate, units, duration, cancel = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define new TB
        TB = {"Rate": rate,
              "Units": units,
              "Duration": duration}

        # Not a cancel TB
        if not cancel:

            # Adjust TB to fit commands
            TB = self.adjust(TB)

            # Verify if TB can be set on pump
            self.verify(TB)

        # Info
        print "Enacting TB:"

        # Show TB
        self.show(TB)

        # Choose command depending on units
        # U/h
        if units == "U/h":

            # Run command
            self.commands["Set Absolute"].run(rate, duration)

        # %
        elif units == "%":

            # Run command
            self.commands["Set Percentage"].run(rate, duration)

        # Info
        print "Verifying if TB was correctly enacted..."

        # Verify that the TB was correctly issued by reading current TB on
        # pump
        self.read()

        # Compare to expectedly set TB
        if TB == self.value:

            # Info
            print "TB correctly enacted."

        # Otherwise
        else:

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

        # Check units of TB
        # U/h
        if units == "U/h":

            # Cancel TB
            self.set(0, units, 0, True)

        # %
        elif units == "%":

            # Cancel TB
            self.set(100, units, 0, True)



class Bolus(PumpComponent):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize bolus component
        super(Bolus, self).__init__(pump)

        # Define name
        self.name = "Last bolus (U)"

        # Instanciate corresponding command
        self.command = commands.DeliverPumpBolus(pump)

        # Initialize bolus characteristics
        self.stroke = 0.1  # Pump bolus stroke (U)
        self.rate   = 40.0 # Bolus delivery rate (s/U)
        self.sleep  = 5    # Time (s) to wait after bolus delivery



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIXME: deal with no last bolus
        """

        # Get current time
        now = datetime.datetime.now()

        # Get recent boluses
        boluses = Reporter.getRecent(now, "treatments.json", ["Boluses"])

        # Get latest bolus time
        t = max(boluses)

        # Get last bolus
        self.value = boluses[t]



    def deliver(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELIVER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify pump status
        self.pump.status.verify()

        # Verify pump settings
        self.pump.settings.verify(bolus = bolus)

        # Run command
        self.command.run(bolus)



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
    pump.firmware.read()

    # Read pump battery level
    pump.battery.read()

    # Read remaining amount of insulin in pump
    pump.reservoir.read()

    # Push button on pump
    #pump.buttons.push("EASY")
    #pump.buttons.push("ESC")
    #pump.buttons.push("ACT")
    #pump.buttons.push("UP")
    #pump.buttons.push("DOWN")

    # Read pump status
    #pump.status.read()
    #pump.status.verify()
    #pump.status.suspend()
    #pump.status.resume()

    # Read pump settings
    #pump.settings.read()
    #pump.settings.verify()

    # Read units set in pump
    #pump.units["BG"].read()
    #pump.units["Carbs"].read()
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
    #pump.history.read(2)

    # Send bolus to pump
    #pump.bolus.deliver(0.2)

    # Read current TB
    #pump.TB.read()

    # Send TB to pump
    #pump.TB.set(0.5, "U/h", 30)
    #pump.TB.set(34.95, "U/h", 30)
    #pump.TB.set(1, "%", 90)
    #pump.TB.set(99, "%", 90)
    #pump.TB.cancel()

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()