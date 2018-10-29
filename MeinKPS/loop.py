#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    loop

    Author:   David Leclerc

    Version:  0.1

    Date:     24.05.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import time



# USER LIBRARIES
import lib
import logger
import reporter
import exporter
import uploader
import calculator as calc
from CGM import cgm
from Stick import stick
from Pump import pump
from Profiles import *



# Define instances
Logger = logger.Logger("loop.py")
Reporter = reporter.Reporter()
Exporter = exporter.Exporter()
Uploader = uploader.Uploader()



# CLASSES
class Loop(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize start/end times
        self.t0 = None
        self.t1 = None

        # Give the loop devices
        self.cgm = cgm.CGM()
        self.pump = pump.Pump(stick.Stick())

        # Define report
        self.report = "loop.json"



    def do(self, task, path, key, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do task
        task(*args)

        # Update loop log
        Reporter.increment(self.report, path, key)



    def doTry(self, task, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try task
        try:

            # Do it
            task(*args)

        # Ignore all errors
        except Exception as e:

            # But log them
            Logger.error(e)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting time
        self.t0 = datetime.datetime.now()

        # Give user info
        Logger.info("Started loop.")

        # Start CGM
        self.cgm.start()

        # Start pump
        self.pump.start()

        # LED on
        self.pump.stick.commands["LED On"].run()

        # Update last loop time
        Reporter.add(self.report, ["Status"],
                     {"Time": lib.formatTime(self.t0)}, True)

        # Update loop iterations
        Reporter.increment(self.report, ["Status"], "N")



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # LED off
        self.pump.stick.commands["LED Off"].run()

        # Stop pump
        self.pump.stop()

        # Stop CGM
        self.cgm.stop()

        # Define ending time
        self.t1 = datetime.datetime.now()

        # Give user info
        Logger.info("Ended loop.")

        # Update loop infos
        Reporter.add(self.report, ["Status"],
                                  {"Duration": (self.t1 - self.t0).seconds},
                                  True)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # CGM
        # Read BGs (last 24 hours)
        self.do(self.cgm.dumpBG, ["CGM"], "BG", 8)

        # Read battery
        self.do(self.cgm.battery.read, ["CGM"], "Battery")

        # Read sensor events
        self.do(self.cgm.databases["Sensor"].read, ["CGM"], "Sensor")

        # Read calibrations
        self.do(self.cgm.databases["Calibration"].read, ["CGM"], "Calibration")

        # PUMP
        # Read battery level
        self.do(self.pump.battery.read, ["Pump"], "Battery")

        # Read remaining amount of insulin
        self.do(self.pump.reservoir.read, ["Pump"], "Reservoir")

        # Read ISF
        self.do(self.pump.ISF.read, ["Pump"], "ISF")

        # Read CSF
        self.do(self.pump.CSF.read, ["Pump"], "CSF")

        # Read BG targets
        self.do(self.pump.BGTargets.read, ["Pump"], "BG Targets")

        # Read basal
        self.do(self.pump.basal.read, ["Pump"], "Basal", "Standard")

        # Update history
        self.do(self.pump.history.update, ["Pump"], "History")



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read DIA
        DIA = Reporter.get("pump.json", ["Settings"], "DIA")

        # Read current time
        now = self.t0

        # Define past/future reference times
        past = now - datetime.timedelta(hours = DIA)
        future = now + datetime.timedelta(hours = DIA)

        # Instanciate profiles
        profiles = {"Suspend": suspend.Suspend(),
                    "Resume": resume.Resume(),
                    "Basal": basal.Basal(),
                    "TB": TB.TB(),
                    "Bolus": bolus.Bolus(),
                    "Net": net.Net(),
                    "BGTargets": BGTargets.BGTargets(),
                    "ISF": ISF.ISF(),
                    "CSF": CSF.CSF(),
                    "IDC": IDC.WalshIDC(DIA),
                    "PastIOB": IOB.PastIOB(),
                    "FutureIOB": IOB.FutureIOB(),
                    "PastBG": BG.PastBG(),
                    "FutureBG": BG.FutureBG()}
        
        # Build net insulin profile
        profiles["Net"].build(past, now, profiles["Suspend"],
                                         profiles["Resume"],
                                         profiles["Basal"],
                                         profiles["TB"],
                                         profiles["Bolus"])

        # Build past profiles
        profiles["PastIOB"].build(past, now)
        profiles["PastBG"].build(past, now)
        
        # Build daily profiles
        profiles["BGTargets"].build(now, future)
        profiles["ISF"].build(now, future)
        #profiles["CSF"].build(now, future)

        # Define timestep (m) for prediction (future) profiles
        dt = 5.0 / 60.0

        # Build prediction profiles
        profiles["FutureIOB"].build(dt, profiles["Net"], profiles["IDC"])
        profiles["FutureBG"].build(dt, profiles["Net"], profiles["IDC"],
                                       profiles["ISF"], profiles["PastBG"])

        # Compute BG dynamics
        BGDynamics = calc.computeBGDynamics(profiles["PastBG"],
                                            profiles["BGTargets"],
                                            profiles["FutureIOB"],
                                            profiles["ISF"])

        # Run calculator, get TB recommendation and return it
        return calc.recommendTB(BGDynamics, profiles["basal"],
                                            profiles["ISF"],
                                            profiles["IDC"])



    def enact(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If no TB is required
        if TB is None:

            # Get current TB
            self.pump.TB.read()

            # If TB currently set
            if self.pump.TB.value["Duration"] != 0:

                # Cancel it
                self.do(self.pump.TB.cancel, ["Pump"], "TB")

            # Otherwise
            else:

                # Exit
                return

        # Otherwise, enact recommendation
        else:

            # Enact TB
            self.do(self.pump.TB.set, ["Pump"], "TB", *TB)

        # Re-update history
        self.pump.history.update()



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        self.do(Exporter.run, ["Status"], "Export", self.t0)

        # Upload stuff
        self.do(Uploader.run, ["Status"], "Upload")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start loop
        self.doTry(self.start)

        # Read CGM/pump
        self.doTry(self.read)

        # Compute necessary TB and enact it
        self.doTry(self.enact, self.doTry(self.compute))

        # Export recent treatments
        self.doTry(self.export)

        # Stop loop
        self.doTry(self.stop)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~­
    """

    # Instanciate a loop
    loop = Loop()

    # Loop
    loop.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()