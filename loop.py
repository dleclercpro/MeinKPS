#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    loop

    Author:   David Leclerc

    Version:  0.2

    Date:     29.10.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import traceback
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import fmt
import errors
import logger
import reporter
import exporter
import uploader
import calculator
from CGM import cgm
from Stick import stick
from Pump import pump
from Profiles import (bg, basal, tb, bolus, net, isf, csf, iob, cob, targets,
    suspend, resume, idc)



# Define instances
Logger = logger.Logger("loop")
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
        self.stick = stick.Stick()
        self.cgm = cgm.CGM()
        self.pump = pump.Pump(self.stick)

        # Get DIA
        self.DIA = reporter.REPORTS["pump"].get(["Settings", "DIA"])

        # Initialize TB recommendation
        self.recommendation = None

        # Define report
        self.report = reporter.REPORTS["loop"]



    def do(self, task, branch, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Execute a task and increment its corresponding branch in the loop
            logs, in order to keep track of loop's performance.
        """

        # Do task
        task(*args)

        # Update loop log
        self.report.increment(branch)



    def tryAndCatch(self, task, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TRYANDCATCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Try to execute a given task and give back trace, in case it fails,
            as well as boolean indicating whether the execution was successful
            or not.
        """

        # Try task
        try:
            task(*args)
            return True

        # Ignore all errors, but log them
        except:
            Logger.error("\n" + traceback.format_exc())
            return False



    def startDevices(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STARTDEVICES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Initialize devices so they're ready to take commands.
        """

        # Start stick
        self.stick.start()

        # Start CGM
        self.cgm.start()

        # Start pump
        self.pump.start()



    def stopDevices(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOPDEVICES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stop pump
        self.pump.stop()

        # Stop CGM
        self.cgm.stop()

        # Stop stick
        self.stick.stop()



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.info("Started loop.")

        # Define starting time
        self.t0 = datetime.datetime.now()

        # Update last loop time
        self.report.set(lib.formatTime(self.t0), ["Status", "Time"], True)
        self.report.store()

        # Start devices
        self.startDevices()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stop devices
        self.stopDevices()

        # Define ending time
        self.t1 = datetime.datetime.now()

        # Get loop length
        dt = (self.t1 - self.t0).seconds

        # Update last loop duration, as well as number of successful loops
        self.report.set(dt, ["Status", "Duration"], True)
        self.report.increment(["Status", "N"])
        self.report.store()

        # Info
        Logger.info("Ended loop.")



    def readCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READCGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read BGs (last 24 hours)
        self.do(self.cgm.dumpBG, ["CGM", "BG"], 8)

        # Read battery
        self.do(self.cgm.battery.read, ["CGM", "Battery"])

        # Read sensor events
        self.do(self.cgm.databases["Sensor"].read, ["CGM", "Sensor"])

        # Read calibrations
        self.do(self.cgm.databases["Calibration"].read, ["CGM", "Calibration"])



    def readPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read battery level
        self.do(self.pump.battery.read, ["Pump", "Battery"])

        # Read remaining amount of insulin
        self.do(self.pump.reservoir.read, ["Pump", "Reservoir"])

        # Read pump settings
        self.do(self.pump.settings.read, ["Pump", "Settings"])

        # Read ISF
        self.do(self.pump.ISF.read, ["Pump", "ISF"])

        # Read CSF
        self.do(self.pump.CSF.read, ["Pump", "CSF"])

        # Read BG targets
        self.do(self.pump.BGTargets.read, ["Pump", "BG Targets"])

        # Read basal
        self.do(self.pump.basal.read, ["Pump", "Basal"], "Standard")

        # Update history
        self.do(self.pump.history.update, ["Pump", "History"])



    def computeTB(self, now, dt = 5.0 / 60.0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTETB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define past/future reference times
        past = now - datetime.timedelta(hours = self.DIA)
        future = now + datetime.timedelta(hours = self.DIA)

        # Instanciate profiles
        profiles = {"IDC": idc.WalshIDC(self.DIA),
                    "Suspend": suspend.Suspend(),
                    "Resume": resume.Resume(),
                    "Basal": basal.Basal(),
                    "TB": tb.TB(),
                    "Bolus": bolus.Bolus(),
                    "Net": net.Net(),
                    "BGTargets": targets.BGTargets(),
                    "FutureISF": isf.FutureISF(),
                    "CSF": csf.CSF(),
                    "PastIOB": iob.PastIOB(),
                    "FutureIOB": iob.FutureIOB(),
                    "PastBG": bg.PastBG(),
                    "FutureBG": bg.FutureBG()}
        
        # Build net insulin profile
        profiles["Net"].build(past, now,
            profiles["Suspend"],
            profiles["Resume"],
            profiles["Basal"],
            profiles["TB"],
            profiles["Bolus"])

        # Build past profiles
        profiles["PastIOB"].build(past, now)
        profiles["PastBG"].build(past, now)
        
        # Build daily profiles
        profiles["BGTargets"].build(now, future)
        profiles["FutureISF"].build(now, future)
        #profiles["CSF"].build(now, future)

        # Build prediction profiles
        profiles["FutureIOB"].build(dt,
            profiles["Net"],
            profiles["IDC"])
        profiles["FutureBG"].build(dt,
            profiles["Net"],
            profiles["IDC"],
            profiles["FutureISF"],
            profiles["PastBG"])

        # Compute BG dynamics
        BGDynamics = calculator.computeBGDynamics(profiles["PastBG"],
            profiles["FutureBG"],
            profiles["BGTargets"],
            profiles["FutureIOB"],
            profiles["FutureISF"])

        # Store TB recommendation
        self.recommendation = calculator.recommendTB(BGDynamics,
            profiles["Basal"],
            profiles["FutureISF"],
            profiles["IDC"])



    def enactTB(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENACTTB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If no TB is required
        if TB is None:

            # Get current TB
            self.pump.TB.read()

            # If TB currently set: cancel it
            if self.pump.TB.value["Duration"] != 0:
                self.do(self.pump.TB.cancel, ["Pump", "TB"])

        # Otherwise, enact TB recommendation
        else:
            self.do(self.pump.TB.set, ["Pump", "TB"], *TB)

        # Re-update history
        self.pump.history.update()



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        self.do(Exporter.run, ["Status", "Export"], self.t0)

        # Upload stuff
        self.do(Uploader.run, ["Status", "Upload"])



    def plot(self, profiles):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare plot
        lib.initPlot()

        # Build graph 1 (basals)
        profiles["Basal"].plot(1, [4, 1], False, None, "purple")
        profiles["Net"].plot(1, [4, 1], False, "Basals", "orange")

        # Build graph 2 (ISFs)
        profiles["ISF"].plot(2, [4, 1], False, "ISFs", "red")

        # Build graph 3 (IOBs)
        profiles["PastIOB"].plot(3, [4, 1], False, None, "#99e500")
        profiles["FutureIOB"].plot(3, [4, 1], False, "IOBs")
        
        # Build graph 4 (BGs)
        profiles["PastBG"].plot(4, [4, 1], False, None, "pink")
        profiles["FutureBG"].plot(4, [4, 1], True, "BGs")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start loop
        if self.tryAndCatch(self.start):

            # Turn stick's LED on to signify active looping
            self.stick.switchLED("ON")

            # If reading CGM works
            if self.tryAndCatch(self.readCGM):

                # If reading pump works
                if self.tryAndCatch(self.readPump):

                    # Compute necessary TB
                    if self.tryAndCatch(self.computeTB, self.t0):

                        # Enact it
                        self.tryAndCatch(self.enactTB, self.recommendation)

                # Export recent treatments
                self.tryAndCatch(self.export)

            # Turn stick's LED off
            self.stick.switchLED("OFF")

            # Stop loop
            self.tryAndCatch(self.stop)



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

    # Plot
    #loop.plot()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()