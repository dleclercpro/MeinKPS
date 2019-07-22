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
#       - Suspend/Resume records at same time problematic!



# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import fmt
import logger
import errors
import reporter
import commands
import records
from Stick import stick



# Define instances
Logger = logger.Logger("Pump.pump")



class Pump(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the pump a stick
        self.stick = stick

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

        # Give the pump a basal profile instance
        self.basal = Basal(self)

        # Give the pump a TB instance
        self.TB = TB(self)

        # Give the pump a bolus instance
        self.bolus = Bolus(self)

        # Give the pump a history instance
        self.history = History(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Tune stick to optimized frequency to establish further connections
        # with pump
        self.stick.tuneOptimizedFrequency(self)

        # Power pump's radio transmitter if necessary
        self.power.verify()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



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
        Logger.info(self.name + ": " + str(self.value))



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
        self.command = commands.Power(pump)

        # Define report
        self.report = reporter.REPORTS["pump"]



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read last time pump's radio transmitter was powered up
        self.value = lib.formatTime(self.report.get(["Power"]))



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
            Logger.info("Pump's radio transmitter is being turned on...")

            # Power up pump's RF transmitter
            self.command.run(self.session)
            return

        # Info
        Logger.info("Pump's radio transmitter is already on. Remaining time: " +
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
        self.command = commands.ReadTime(pump)



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
        self.command = commands.ReadModel(pump)



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
        self.command = commands.ReadFirmware(pump)



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
        self.command = commands.PushButton(pump)



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
        self.command = commands.ReadBattery(pump)



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
        self.command = commands.ReadReservoir(pump)



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
        self.commands = {"Read": commands.ReadStatus(pump),
                         "Suspend": commands.Suspend(pump),
                         "Resume": commands.Resume(pump)}



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
            raise errors.PumpStatusAbnormal

        elif self.value["Bolusing"]:
            raise errors.PumpStatusBolusing

        elif self.value["Suspended"]:
            raise errors.PumpStatusSuspended

        # Info
        Logger.info("Pump's status allows desired course of action. " +
                    "Proceeding...")



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
        self.command = commands.ReadSettings(pump)



    def verify(self, TB = None, bolus = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read pump settings
        self.read()

        # If TB is asked for, but exceeds max settings
        if (TB is not None and
            TB["Units"] == "U/h" and
            TB["Rate"] > self.value["Max Basal"]):
            raise ValueError("Max basal exceeded: " + fmt.basal(TB["Rate"]) +
                " > " + fmt.bolus(self.value["Max Basal"]))

        # If bolus is asked for, but exceeds max settings
        elif bolus is not None and bolus > self.value["Max Bolus"]:
            raise ValueError("Max bolus exceeded: " + fmt.bolus(bolus) +
                " > " + fmt.bolus(self.value["Max Bolus"]))

        # Info
        Logger.info("Pump's settings allow desired course of action. " +
                    "Proceeding...")



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
        self.command = commands.ReadBGUnits(pump)



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
        self.command = commands.ReadCarbsUnits(pump)



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
        self.command = commands.SetTBUnits(pump)



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
        self.command = commands.ReadBGTargets(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of BG targets read
        n = len(self.value["Times"])

        # Info
        Logger.info("BG target(s):")

        # Print targets
        for i in range(n):

            # Format info
            Logger.info(self.value["Times"][i] + " - " +
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
        self.command = commands.ReadISF(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of ISF read
        n = len(self.value["Times"])

        # Info
        Logger.info("ISF(s):")

        # Print factors
        for i in range(n):

            # Format info
            Logger.info(self.value["Times"][i] + " - " +
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
        self.command = commands.ReadCSF(pump)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of ISF read
        n = len(self.value["Times"])

        # Info
        Logger.info("CSF(s):")

        # Print factors
        for i in range(n):

            # Format info
            Logger.info(self.value["Times"][i] + " - " +
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
        self.command = commands.ReadDailyTotals(pump)



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
            "Standard": commands.ReadBasalProfileStandard(pump),
            "A": commands.ReadBasalProfileA(pump),
            "B": commands.ReadBasalProfileB(pump)}

        # Initialize basal characteristics
        self.stroke = 0.025 # Pump basal stroke rate (U/h)
        self.time   = 30    # Time block (m) used by pump for basal durations



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
            self.value = self.commands["Standard"].run()

        # A
        elif profile == "A":
            self.value = self.commands["A"].run()

        # B
        elif profile == "B":
            self.value = self.commands["B"].run()

        # Otherwise
        else:
            raise ValueError("Invalid basal profile.")

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
        Logger.info("Bolus profile '" + self.profile + "':")

        # Print rates
        for i in range(n):

            # Format info
            Logger.info(self.value["Times"][i] + " - " +
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
        self.commands = {"Read": commands.ReadTB(pump),
                         "Set Absolute": commands.SetAbsoluteTB(pump),
                         "Set Percentage": commands.SetPercentageTB(pump)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current TB
        self.value = self.commands["Read"].run()

    	# Info
    	Logger.info("Current TB:")
        Logger.info(fmt.TB(TB))



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
            raise errors.BadTBRate(TB)

        # Verify if duration is a multiple of 30
        if TB["Duration"] % 30:
            raise errors.BadTBDuration(TB)

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
            Logger.warning("TB must be canceled before doing anything...")

            # Cancel TB
            self.cancel(self.value["Units"])

        # Look if units match up
        if self.value["Units"] != TB["Units"]:

            # Info
            Logger.warning("TB units do not match. Adjusting them...")

            # Modify units as wished by the user
            self.pump.units["TB"].set(TB["Units"])



    def adjust(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADJUST
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.info("Adjusting TB from:")
        Logger.info(fmt.TB(TB))

        # Round rate
        # U/h
        if TB["Units"] == "U/h":
            TB["Rate"] = round(round(TB["Rate"] / self.pump.basal.stroke) *
                                                  self.pump.basal.stroke, 2)

        # %
        elif TB["Units"] == "%":
            TB["Rate"] = round(TB["Rate"])

        # Round duration
        TB["Duration"] = (round(TB["Duration"] / self.pump.basal.time) *
                                                 self.pump.basal.time)

        # Info
        Logger.info("To:")
        Logger.info(fmt.TB(TB))

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
        Logger.info("Enacting TB:")
        Logger.info(fmt.TB(TB))

        # Choose command depending on units
        # U/h
        if TB["Units"] == "U/h":
            self.commands["Set Absolute"].run(TB["Rate"], TB["Duration"])

        # %
        elif TB["Units"] == "%":
            self.commands["Set Percentage"].run(TB["Rate"], TB["Duration"])

        # Otherwise
        else:
            raise ValueError("Bad TB units.")

        # Info
        Logger.info("Verifying if TB was correctly enacted...")

        # Verify that the TB was correctly issued by reading current TB
        self.read()

        # Compare to expectedly set TB
        if TB != self.value:
            raise errors.TBFail()

        # Success
        Logger.info("TB correctly enacted.")




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
            self.set(0, units, 0, True)

        # %
        elif units == "%":
            self.set(100, units, 0, True)

        # Bad units
        else:
            raise ValueError("Bad TB units.")



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
        self.command = commands.DeliverBolus(pump)

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
        boluses = reporter.getRecent(reporter.TreatmentsReport, now,
            ["Boluses"])

        # Get latest bolus time
        lastTime = max(boluses)

        # Get last bolus
        self.value = boluses[lastTime]



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
        self.commands = {"Measure": commands.ReadHistorySize(pump),
                         "Read": commands.ReadHistoryPage(pump)}

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
        Logger.info("Found " + str(self.size) + " pump history pages.")



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
        Logger.debug("Read page(s) [" + str(len(self.pages)) + " byte(s)]:")

        # Print downloaded history pages
        Logger.debug(self.pages)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Finding records...")

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

        # Read max 2 pages
        self.read(min(self.size, 2))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate stick
    _stick = stick.Stick()

    # Start it
    _stick.start()

    # Instanciate pump
    pump = Pump(_stick)

    # Start it
    pump.start()

    # Read time
    pump.time.read()

    # Read model
    pump.model.read()

    # Read firmware version
    pump.firmware.read()

    # Read battery level
    pump.battery.read()

    # Read remaining amount of insulin
    pump.reservoir.read()

    # Push buttons
    #pump.buttons.push("EASY")
    #pump.buttons.push("ESC")
    #pump.buttons.push("ACT")
    #pump.buttons.push("UP")
    #pump.buttons.push("DOWN")

    # Read status
    pump.status.read()
    #pump.status.verify()
    #pump.status.suspend()
    #pump.status.resume()

    # Read settings
    pump.settings.read()
    #pump.settings.verify()

    # Read set units
    pump.units["BG"].read()
    pump.units["Carbs"].read()
    pump.units["TB"].read()

    # Set TB units
    #pump.units["TB"].set("U/h")
    #pump.units["TB"].set("%")

    # Read BG targets
    pump.BGTargets.read()

    # Read insulin sensitivity factors
    pump.ISF.read()

    # Read carb sensitivity factors
    pump.CSF.read()

    # Read basal profiles
    pump.basal.read("Standard")
    pump.basal.read("A")
    pump.basal.read("B")

    # Read daily totals
    pump.dailyTotals.read()

    # Read history
    pump.history.read(2)

    # Enact bolus
    #pump.bolus.deliver(0.2)

    # Read current TB
    #pump.TB.read()

    # Enact TB
    #pump.TB.set(2.35, "U/h", 30)
    #pump.TB.set(34.95, "U/h", 30)
    #pump.TB.set(1, "%", 90)
    #pump.TB.set(99, "%", 90)
    #pump.TB.cancel()

    # Stop pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()