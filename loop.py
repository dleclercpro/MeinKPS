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
import idc
from CGM import cgm
from Stick import stick
from Pump import pump
from Profiles import bg, basal, net, isf, csf, iob, cob, targets



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

        # Initialize profile dict
        self.profiles = {}

        # Initialize TB recommendation
        self.recommendation = None

        # Define report
        self.report = None



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
        self.report.store()



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



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            The loop is only considered started after the devices have been
            initialized and are ready to receive orders.
        """

        # Info
        Logger.info("Started loop.")

        # Define starting time
        self.t0 = datetime.datetime.now()

        # Get current day
        today = self.t0.date()

        # Get report
        self.report = reporter.getReportByType(reporter.LoopReport, today,
            strict = False)

        # Update loop stats
        self.report.set(lib.formatTime(self.t0), ["Loop", "Last Time"], True)
        self.report.increment(["Loop", "Start"])
        self.report.store()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define ending time
        self.t1 = datetime.datetime.now()

        # Get loop duration
        duration = (self.t1 - self.t0).seconds

        # Update loop stats
        self.report.set(duration, ["Loop", "Last Duration"], True)
        self.report.increment(["Loop", "End"])
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
        self.do(self.cgm.dumpBG, ["CGM", "BG"], 10)

        # Read battery
        self.do(self.cgm.battery.read, ["CGM", "Battery"])

        # Read sensor events
        self.do(self.cgm.databases["Sensor"].read, ["CGM", "Sensor"])



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



    def buildProfiles(self, now, dt = 5.0 / 60.0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILDPROFILES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            dt: step size
        """

        # Get DIA
        DIA = reporter.getPumpReport().get(["Settings", "DIA"])

        # Define PIA (peak of insulin action)
        PIA = 1.25

        # Define past/future reference times
        past = now - datetime.timedelta(hours = DIA)
        future = now + datetime.timedelta(hours = DIA)

        # Instanciate profiles
        self.profiles = {"IDC": idc.ExponentialIDC(DIA, PIA),
                         "Basal": basal.Basal(),
                         "Net": net.Net(),
                         "BGTargets": targets.BGTargets(),
                         "FutureISF": isf.FutureISF(),
                         "FutureCSF": csf.FutureCSF(),
                         "PastIOB": iob.PastIOB(),
                         "FutureIOB": iob.FutureIOB(),
                         "PastBG": bg.PastBG(),
                         "FutureBG": bg.FutureBG()}
        
        # Build net insulin profile
        self.profiles["Net"].build(past, now)

        # Build past profiles
        self.profiles["Basal"].build(past, now)
        self.profiles["PastIOB"].build(past, now)
        self.profiles["PastBG"].build(past, now)

        # Build daily profiles
        self.profiles["BGTargets"].build(now, future)
        self.profiles["FutureISF"].build(now, future)
        #self.profiles["FutureCSF"].build(now, future)

        # Build future profiles
        self.profiles["FutureIOB"].build(
            self.profiles["Net"],
            self.profiles["IDC"],
            dt)
        self.profiles["FutureBG"].build(
            self.profiles["PastBG"],
            self.profiles["Net"],
            self.profiles["IDC"],
            self.profiles["FutureISF"],
            dt)

        # Store latest IOB
        self.profiles["FutureIOB"].store()



    def computeTB(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTETB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Build profiles
        self.buildProfiles(now)

        # Get current IOB
        IOB = self.profiles["FutureIOB"].y[0]

        # Compute BG dynamics
        BGDynamics = calculator.computeBGDynamics(
            self.profiles["PastBG"],
            self.profiles["FutureBG"],
            self.profiles["BGTargets"],
            self.profiles["FutureIOB"],
            self.profiles["FutureISF"])

        # Store TB recommendation
        self.recommendation = calculator.recommendTB(
            BGDynamics,
            self.profiles["Basal"],
            self.profiles["FutureISF"],
            self.profiles["IDC"],
            IOB)



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
            self.do(self.pump.TB.set, ["Pump", "TB"], TB)

        # Re-update history
        self.pump.history.update()



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        self.do(Exporter.run, ["Loop", "Export"], self.t0)

        # Upload stuff
        self.do(Uploader.run, ["Loop", "Upload"])



    def plot(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Build profiles
        self.buildProfiles(now)

        # Profiles defined?
        if self.profiles:

            # Prepare plot
            lib.initPlot()

            # Build graph 1 (basals)
            self.profiles["Basal"].plot(1, [4, 1], False, None, "purple")
            self.profiles["Net"].plot(1, [4, 1], False, "Basals", "orange")

            # Build graph 2 (ISFs)
            self.profiles["FutureISF"].plot(2, [4, 1], False, "ISFs", "red")

            # Build graph 3 (IOBs)
            self.profiles["PastIOB"].plot(3, [4, 1], False, None, "#99e500")
            self.profiles["FutureIOB"].plot(3, [4, 1], False, "IOBs")
            
            # Build graph 4 (BGs)
            self.profiles["PastBG"].plot(4, [4, 1], False, None, "pink")
            self.profiles["FutureBG"].plot(4, [4, 1], True, "BGs")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start
        isStarted = {"Loop": self.tryAndCatch(self.start),
                     "Stick": self.tryAndCatch(self.stick.start),
                     "CGM": self.tryAndCatch(self.cgm.start),
                     "Pump": self.tryAndCatch(self.pump.start)}

        # Read
        isRead = {"CGM": isStarted["CGM"] and self.tryAndCatch(self.readCGM),
                  "Pump": isStarted["Pump"] and self.tryAndCatch(self.readPump)}

        # BG data is always necessary
        if isRead["CGM"]:

            # If pump was successfully read
            if isRead["Pump"]:

                # Compute and enact necessary TB
                if self.tryAndCatch(self.computeTB, self.t0):
                    self.tryAndCatch(self.enactTB, self.recommendation)
                
            # Export recent treatments
            self.tryAndCatch(self.export)

        # Stop
        isStopped = {"Pump": self.tryAndCatch(self.pump.stop),
                     "CGM": self.tryAndCatch(self.cgm.stop),
                     "Stick": self.tryAndCatch(self.stick.stop),
                     "Loop": self.tryAndCatch(self.stop)}



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~­
    """

    # Get current time
    now = datetime.datetime.now()

    # Instanciate a loop
    loop = Loop()

    # Loop
    loop.run()

    # Plot
    #loop.plot(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()