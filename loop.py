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
Logger = logger.Logger("loop.py")
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

        # Define report
        self.report = reporter.REPORTS["loop"]



    def do(self, task, branch, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do task
        task(*args)

        # Update loop log
        self.report.increment(branch)



    def doTry(self, task, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try task
        try:

            # Do it
            return task(*args)

        # Ignore all errors
        except Exception as e:

            # But log them
            Logger.error("\n" + traceback.format_exc())

            # Return
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

        # Turn stick's LED on to signify active looping
        self.stick.switchLED("ON")

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

        # Turn stick's LED off
        self.stick.switchLED("OFF")

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

        # Update loop iterations
        self.report.increment(["Status", "N"])

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

        # Update loop infos
        self.report.set(dt, ["Status", "Duration"], True)

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

        # Reading done
        return True



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
        self.do(self.pump.basal.read, ["Pump", "Basal", "Standard"])

        # Update history
        self.do(self.pump.history.update, ["Pump", "History"])

        # Reading done
        return True



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

        # Return TB recommendation
        return calculator.recommendTB(BGDynamics,
            profiles["Basal"],
            profiles["FutureISF"],
            profiles["IDC"])



    def autosens(self, now, t = 24):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            AUTOSENS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define past reference time
        past = now - datetime.timedelta(hours = t)

        # Define DIA as a datetime timedelta object
        dia = datetime.timedelta(hours = self.DIA)

        # Instanciate profiles
        profiles = {"IDC": idc.WalshIDC(self.DIA),
                    "Suspend": None,
                    "Resume": None,
                    "Basal": None,
                    "TB": None,
                    "Bolus": None,
                    "Net": None,
                    "PastISF": isf.PastISF(),
                    "PastBG": bg.PastBG()}

        # Build past BG profile
        profiles["PastBG"].build(past, now)
        
        # Build past ISF profile
        profiles["PastISF"].build(past, now)

        # Reference to BG time axes
        T = profiles["PastBG"].T
        t = profiles["PastBG"].t

        # Initialize IOB arrays
        IOBs = []

        # Get number of BGs
        n = len(T)

        # Compute IOB for each BG
        for i in range(n):

            # Reset necessary profiles
            profiles["Suspend"] = suspend.Suspend()
            profiles["Resume"] = resume.Resume()
            profiles["Basal"] = basal.Basal()
            profiles["TB"] = tb.TB()
            profiles["Bolus"] = bolus.Bolus()
            profiles["Net"] = net.Net()

            # Build net insulin profile
            profiles["Net"].build(T[i] - dia, T[i], profiles["Suspend"],
                                                    profiles["Resume"],
                                                    profiles["Basal"], 
                                                    profiles["TB"],
                                                    profiles["Bolus"])

            # Do it
            IOBs.append(calculator.computeIOB(profiles["Net"], profiles["IDC"]))

            # Show IOB
            print "IOB(" + lib.formatTime(T[i]) + ") = " + fmt.IOB(IOBs[-1])

        # Initialize dBG deviations
        ddBGs = []

        # Go through IOB and find difference between expected dBG and actual one
        for i in range(n - 1):

            # Compute dIOB
            dIOB = IOBs[i + 1] - IOBs[i]

            # Compute dBG
            dBG = profiles["PastBG"].y[i + 1] - profiles["PastBG"].y[i]
            expecteddBG = dIOB * profiles["PastISF"].f(t[i])

            # Compute delta dBG
            ddBGs.append(dBG - expecteddBG)

            # Avoid division by zero
            if not expecteddBG == 0:

                # Compute dBG ratio
                r = round(dBG / float(expecteddBG), 2)

            # Otherwise
            else:

                # No ratio available
                r = None

            # Info
            print "dIOB: " + fmt.IOB(dIOB)
            print "dBG: " + fmt.BG(dBG)
            print "Expected dBG: " + fmt.BG(expecteddBG)
            print "ddBG: " + fmt.BG(ddBGs[i])
            print "r: " + str(r)
            print

        # Plot
        print "Mean ddBG: " + fmt.BG(np.mean(ddBGs))
        lib.initPlot()
        ax = plt.subplot(1, 1, 1)

        # Define axis labels
        x = "(h)"
        y = "(mmol/L)"

        # Set title
        ax.set_title("dBG Deviations", fontweight = "semibold")

        # Set axis labels
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.plot(t[:-1], ddBGs, marker = "o", ms = 3.5, lw = 0, c = "red")
        plt.show()



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
                self.do(self.pump.TB.cancel, ["Pump"], "TB")

            # Otherwise
            else:
                return

        # Otherwise, enact TB recommendation
        else:
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
        self.doTry(self.start)

        # If reading CGM works
        if self.doTry(self.readCGM):

            # If reading pump works
            if self.doTry(self.readPump):

                # Compute necessary TB and enact it
                self.doTry(self.enactTB, self.doTry(self.computeTB, self.t0))

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

    # Plot
    #loop.plot()

    # Autosens
    #loop.autosens(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()