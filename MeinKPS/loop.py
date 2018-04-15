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
import calculator
from CGM import cgm
from Stick import stick
from Pump import pump



# Define a instances
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

        # Give the loop a calculator
        self.calc = calculator.Calculator()

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



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting time
        self.t0 = datetime.datetime.now()

        # Give user info
        Logger.info("Start: " + lib.formatTime(self.t0))

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
        Logger.info("End: " + lib.formatTime(self.t1))

        # Update loop infos
        Reporter.add(self.report, ["Status"],
                                  {"Duration": (self.t1 - self.t0).seconds},
                                  True)



    def doCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOCGM
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



    def doPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

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

        # Run calculator and get recommendation
        TB = self.calc.run(self.t0)

        # If no TB is required
        if TB is None:

            # Get current TB
            self.pump.TB.read()

            # If TB currently set
            if self.pump.TB.value["Duration"] != 0:

                # Cancel it
                self.pump.TB.cancel()

                # Re-update history
                self.pump.history.update

        # Otherwise, enact recommendation
        else:

            # Enact TB
            self.pump.TB.set(*TB)

            # Re-update history
            self.pump.history.update

        # Acknowledge TB was done
        self.do(lib.NOP, ["Pump"], "TB")



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        self.do(Exporter.run, ["Status"], "Export", self.t0)

        # Upload them
        self.upload()



    def upload(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Upload stuff
        self.do(Uploader.run, ["Status"], "Upload")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start
        self.start()

        # Try CGM stuff
        try:

            # Do it
            self.doCGM()

        # Error
        except:

            # Ignore
            pass

        # Try pump stuff
        try:

            # Do it
            self.doPump()

        # Error
        except:

            # Ignore
            pass

        # Try exporting recent treatments
        try:

            # Do it
            self.export()

        # Error
        except:

            # Ignore
            pass

        # Stop
        self.stop()



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