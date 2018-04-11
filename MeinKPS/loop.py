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
import reporter
import exporter
import uploader
import calculator
from CGM import cgm
from Pump import pump



# Define a reporter, an exporter, and an uploader
Reporter = reporter.Reporter()
Exporter = exporter.Exporter()
Uploader = uploader.Uploader()



# FUNCTIONS
def do(task, path, key, *args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        DO
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Do task
    task(*args)

    # Update loop log
    Reporter.increment("loop.json", path, key)



# CLASSES
class Loop(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize start/end times
        self.start = None
        self.end = None

        # Give the loop devices
        self.cgm = cgm.CGM()
        self.pump = pump.Pump()

        # Give the loop a calculator
        self.calc = calculator.Calculator()



    def doCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOCGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start CGM
        self.cgm.start()

        # Read BGs (last 24 hours)
        do(self.cgm.dumpBG, ["CGM"], "BG", 8)

        # Read battery
        do(self.cgm.battery.read, ["CGM"], "Battery")

        # Read sensor events
        do(self.cgm.databases["Sensor"].read, ["CGM"], "Sensor")

        # Read calibrations
        do(self.cgm.databases["Calibration"].read, ["CGM"], "Calibration")

        # Stop CGM
        self.cgm.stop()



    def doPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start pump
        self.pump.start()

        # Read battery level
        do(self.pump.battery.read, ["Pump"], "Battery")

        # Read remaining amount of insulin
        do(self.pump.reservoir.read, ["Pump"], "Reservoir")

        # Read ISF
        do(self.pump.ISF.read, ["Pump"], "ISF")

        # Read CSF
        do(self.pump.CSF.read, ["Pump"], "CSF")

        # Read BG targets
        do(self.pump.BGTargets.read, ["Pump"], "BG Targets")

        # Read basal
        do(self.pump.basal.read, ["Pump"], "Basal", "Standard")

        # Update history
        do(self.pump.history.update, ["Pump"], "History")

        # Run calculator and get recommendation
        TB = self.calc.run(self.start)

        # If no TB is required
        if TB is None:

            # Get current TB
            self.pump.TB.read()

            # If TB currently set
            if self.pump.TB.value["Duration"] != 0:

                # Cancel it
                do(self.pump.TB.cancel, ["Pump"], "TB")

        # Otherwise, enact recommendation
        else:

            # Enact TB
            do(self.pump.TB.set, ["Pump"], "TB", *TB)

        # Re-update history
        do(self.pump.history.update, ["Pump"], "History")

        # Stop pump
        self.pump.stop()



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        do(Exporter.run, ["Status"], "Export", self.start)



    def upload(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Upload stuff
        do(Uploader.run, ["Status"], "Upload")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting time
        self.start = datetime.datetime.now()

        # Give user info
        print "Start: " + lib.formatTime(self.start)

        # Update last loop time
        Reporter.add(self.report, ["Status"],
                     {"Time": lib.formatTime(self.start)}, True)

        # Update loop iterations
        Reporter.increment(self.report, ["Status"], "N")

        # Do CGM stuff
        self.doCGM()

        # Do pump stuff
        self.doPump()

        # Export recent treatments
        self.export()

        # Upload them
        self.upload()

        # Define ending time
        self.end = datetime.datetime.now()

        # Give user info
        print "End: " + lib.formatTime(self.end)

        # Update loop infos
        Reporter.add(self.report, ["Status"],
                                  {"Duration": (self.end - self.start).seconds},
                                  True)



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