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

        # Instanciate profiles
        self.profiles = {"IDC": None,
                         "Suspend": suspend.Suspend(),
                         "Resume": resume.Resume(),
                         "Basal": basal.Basal(),
                         "TB": TB.TB(),
                         "Bolus": bolus.Bolus(),
                         "Net": net.Net(),
                         "BGTargets": BGTargets.BGTargets(),
                         "ISF": ISF.ISF(),
                         "CSF": CSF.CSF(),
                         "PastIOB": IOB.PastIOB(),
                         "FutureIOB": IOB.FutureIOB(),
                         "PastBG": BG.PastBG(),
                         "FutureBG": BG.FutureBG()}

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



    def _try(self, task, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            _TRY
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



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.info("Started loop.")

        # Define starting time
        self.t0 = datetime.datetime.now()

        # Update last loop time
        Reporter.add(self.report, ["Status"],
                     {"Time": lib.formatTime(self.t0)}, True)

        # Update loop iterations
        Reporter.increment(self.report, ["Status"], "N")

        # Start CGM
        self.cgm.start()

        # Start pump
        self.pump.start()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.info("Ended loop.")

        # Define ending time
        self.t1 = datetime.datetime.now()

        # Update loop infos
        Reporter.add(self.report, ["Status"],
                                  {"Duration": (self.t1 - self.t0).seconds},
                                  True)

        # Stop CGM
        self.cgm.stop()

        # Stop pump
        self.pump.stop()



    def readCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READCGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read BGs (last 24 hours)
        self.do(self.cgm.dumpBG, ["CGM"], "BG", 8)

        # Read battery
        self.do(self.cgm.battery.read, ["CGM"], "Battery")

        # Read sensor events
        self.do(self.cgm.databases["Sensor"].read, ["CGM"], "Sensor")

        # Read calibrations
        self.do(self.cgm.databases["Calibration"].read, ["CGM"], "Calibration")

        # Reading done
        return True



    def readPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read battery level
        self.do(self.pump.battery.read, ["Pump"], "Battery")

        # Read remaining amount of insulin
        self.do(self.pump.reservoir.read, ["Pump"], "Reservoir")

        # Read pump settings
        self.do(self.pump.settings.read, ["Pump"], "Settings")

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

        # Reading done
        return True



    def compute(self, now, dt = 5.0 / 60.0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read DIA
        DIA = Reporter.get("pump.json", ["Settings"], "DIA")

        # Define past/future reference times
        past = now - datetime.timedelta(hours = DIA)
        future = now + datetime.timedelta(hours = DIA)

        # Build IDC
        self.profiles["IDC"] = IDC.WalshIDC(DIA)
        
        # Build net insulin profile
        self.profiles["Net"].build(past, now, self.profiles["Suspend"],
                                              self.profiles["Resume"],
                                              self.profiles["Basal"],
                                              self.profiles["TB"],
                                              self.profiles["Bolus"])

        # Build past profiles
        self.profiles["PastIOB"].build(past, now)
        self.profiles["PastBG"].build(past, now)
        
        # Build daily profiles
        self.profiles["BGTargets"].build(now, future)
        self.profiles["ISF"].build(now, future)
        self.profiles["CSF"].build(now, future)

        # Build prediction profiles
        self.profiles["FutureIOB"].build(dt, self.profiles["Net"],
                                             self.profiles["IDC"])
        self.profiles["FutureBG"].build(dt, self.profiles["Net"],
                                            self.profiles["IDC"],
                                            self.profiles["ISF"],
                                            self.profiles["PastBG"])

        # Compute BG dynamics
        BGDynamics = calc.computeBGDynamics(self.profiles["PastBG"],
                                            self.profiles["FutureBG"],
                                            self.profiles["BGTargets"],
                                            self.profiles["FutureIOB"],
                                            self.profiles["ISF"])

        # Run calculator, get TB recommendation and return it
        return calc.recommendTB(BGDynamics, self.profiles["Basal"],
                                            self.profiles["ISF"],
                                            self.profiles["IDC"])



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



    def plot(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare plot
        lib.initPlot()

        # Build graph 1 (basals)
        self.profiles["Basal"].plot(1, [4, 1], False, None, "purple")
        self.profiles["Net"].plot(1, [4, 1], False, "Basals", "orange")

        # Build graph 2 (ISFs)
        self.profiles["ISF"].plot(2, [4, 1], False, "ISFs", "red")

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

        # Start loop
        self._try(self.start)

        # If reading CGM works
        if self._try(self.readCGM):

            # If reading pump works
            if self._try(self.readPump):

                # Compute necessary TB and enact it
                self._try(self.enact, self._try(self.compute, self.t0))

            # Export recent treatments
            self._try(self.export)

        # Stop loop
        self._try(self.stop)



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