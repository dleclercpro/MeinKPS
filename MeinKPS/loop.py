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
import sys



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



# CONSTANTS
SRC = os.path.dirname(os.path.realpath(__file__)) + os.sep



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
        self.devices = {"CGM": cgm.CGM(),
                        "Pump": pump.Pump()}

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

        # Trying doing given task
        try:

            # Do task
            task(*args)

            # Update loop log
            Reporter.increment(self.report, path, key)

        # Otherwise, skip
        except Exception as e:

            # Give user info
            print "Could not execute task '" + key + "':"

            # Show error
            print e

            # Exit
            sys.exit(True)



    def cgm(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start CGM
        self.devices["CGM"].start()

        # If not a quick run
        if not quick:

            # Read clock
            self.do(self.devices["CGM"].clock.read,
                ["CGM"], "Clock")

            # Read units
            self.do(self.devices["CGM"].units.read,
                ["CGM"], "Units")

            # Read language
            self.do(self.devices["CGM"].language.read,
                ["CGM"], "Language")

            # Read firmware
            self.do(self.devices["CGM"].firmware.read,
                ["CGM"], "Firmware")

            # Read transmitter
            self.do(self.devices["CGM"].transmitter.read,
                ["CGM"], "Transmitter")

            # Read BG
            self.do(self.devices["CGM"].dumpBG,
                ["CGM"], "BG")

        # Otherwise
        else:

            # Read BGs
            self.do(self.devices["CGM"].dumpBG,
                ["CGM"], "BG", 8)

        # Read battery
        self.do(self.devices["CGM"].battery.read,
            ["CGM"], "Battery")

        # Read sensor events
        self.do(self.devices["CGM"].databases["Sensor"].read,
            ["CGM"], "Sensor")

        # Read calibrations
        self.do(self.devices["CGM"].databases["Calibration"].read,
            ["CGM"], "Calibration")

        # Stop CGM
        self.devices["CGM"].stop()



    def pump(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start pump
        self.devices["Pump"].start()

        # If not a quick run
        if not quick:

            # Read time
            self.do(self.devices["Pump"].time.read,
                ["Pump"], "Time")

            # Read model
            self.do(self.devices["Pump"].model.read,
                ["Pump"], "Model")

        # Read battery level
        self.do(self.devices["Pump"].battery.read,
            ["Pump"], "Battery")

        # Read remaining amount of insulin
        self.do(self.devices["Pump"].reservoir.read,
            ["Pump"], "Reservoir")

        # Read ISF
        self.do(self.devices["Pump"].ISF.read,
            ["Pump"], "ISF")

        # Read CSF
        self.do(self.devices["Pump"].CSF.read,
            ["Pump"], "CSF")

        # Read BG targets
        self.do(self.devices["Pump"].BGTargets.read,
            ["Pump"], "BG Targets")

        # Read basal
        self.do(self.devices["Pump"].basal.read,
            ["Pump"], "Basal", "Standard")

        # Update history
        self.do(self.devices["Pump"].history.update,
            ["Pump"], "History")

        # Run calculator and get recommendation
        TB = self.calc.run(self.start)

        # Fake TB
        # TB = [self.start.minute / 60.0, "U/h", 30]

        # If no TB is required
        if TB is None:

            # Cancel TB
            self.do(self.devices["Pump"].TB.cancel,
                ["Pump"], "TB")

        # Otherwise, enact recommendation
        else:

            # Enact TB
            self.do(self.devices["Pump"].TB.set,
                ["Pump"], "TB", *TB)

        # Re-update history
        self.do(self.devices["Pump"].history.update,
            ["Pump"], "History")

        # Stop pump
        self.devices["Pump"].stop()



    def export(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Export preprocessed treatments
        self.do(Exporter.run, ["Status"], "Export", self.start)



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

        # Define starting time
        self.start = datetime.datetime.now()

        # Give user info
        print "Start: " + lib.formatTime(self.start)

        # Update last loop time
        Reporter.add(self.report, ["Status"],
                     {"Time": lib.formatTime(self.start)}, True)

        # Update loop iterations
        Reporter.increment(self.report, ["Status"], "N")

        # Reset USB ports
        os.system("sudo sh " + SRC + "reset.sh")

        # Wait until stick is back
        time.sleep(2)

        # Do CGM stuff
        self.cgm()

        # Do pump stuff
        self.pump()

        # Export recent treatments
        self.export()

        # Upload them
        self.upload()

        # Define ending time
        self.end = datetime.datetime.now()

        # Give user info
        print "End: " + lib.formatTime(self.end)

        # Get duration of loop
        d = self.end - self.start

        # Update loop infos
        Reporter.add(self.report, ["Status"], {"Duration": d.seconds}, True)



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
