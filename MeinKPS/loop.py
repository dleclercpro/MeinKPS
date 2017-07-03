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



# USER LIBRARIES
import lib
import reporter
import uploader
import calculator
from CGM import cgm
from Pump import pump



# Define a reporter
Reporter = reporter.Reporter()



class Loop(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.now = None

        # Give the loop a CGM
        self.cgm = cgm.CGM()

        # Give the loop a pump
        self.pump = pump.Pump()

        # Give the loop a calculator
        self.calc = calculator.Calculator()



    def prepareCGM(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARECGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If not a quick run
        if not quick:

            # Read clock
            self.do(self.cgm.clock.read, ["CGM"], "Clock")

            # Read battery
            self.do(self.cgm.battery.read, ["CGM"], "Battery")

            # Read units
            self.do(self.cgm.units.read, ["CGM"], "Units")

            # Read language
            self.do(self.cgm.language.read, ["CGM"], "Language")

            # Read firmware
            self.do(self.cgm.firmware.read, ["CGM"], "Firmware")

            # Read transmitter
            self.do(self.cgm.transmitter.read, ["CGM"], "Transmitter")

            # Read BG
            self.do(self.cgm.dumpBG, ["CGM"], "BG")

        # Otherwise
        else:

            # Read CGM
            self.do(self.cgm.dumpNewBG, ["CGM"], "BG")



    def doCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOCGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try doing CGM tasks
        try:

            # Establish connection with CGM
            self.cgm.connect()

            # Prepare CGM
            self.prepareCGM()

            # End connection with CGM
            self.cgm.disconnect()

        # Otherwise
        except:

            # Skip
            pass



    def preparePump(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPAREPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If not a quick run
        if not quick:

            # Read time
            self.do(self.pump.time.read, ["Pump"], "Time")

            # Read model
            self.do(self.pump.model.read, ["Pump"], "Model")

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

        # Read latest history
        self.do(self.pump.history.update, ["Pump"], "History")



    def doPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try doing pump tasks
        try:

            # Start dialogue with pump
            self.pump.start()

            # Prepare pump
            self.preparePump()

            # Run calculator and get TB recommendation
            TB = self.calc.run(self.now)
            #TB = [self.now.minute / 60.0, "U/h", 30]

            # If no TB is required
            if TB is None:

                # Cancel TB
                self.pump.TB.cancel()

            # Otherwise, enact recommendation
            else:

                # Enact TB
                self.do(self.pump.TB.set, ["Pump"], "TB", *TB)

            # Stop dialogue with pump
            self.pump.stop()

        # Otherwise
        except:

            # Skip
            pass



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
            Reporter.increment(path, key)

        # Otherwise, skip
        except:

            # Give user info
            print "Could not execute task '" + key + "'."



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting time
        start = datetime.datetime.now()

        # Give user info
        print "Start: " + lib.formatTime(start)

        # Store it
        self.now = start

        # Load loop report
        Reporter.load("loop.json")

        # Update loop infos
        Reporter.addEntries(["Status"], "Time", lib.formatTime(start), True)
        Reporter.increment(["Status"], "N")

        # Do CGM stuff
        self.doCGM()

        # Do pump stuff
        self.doPump()

        # Upload stuff
        self.do(uploader.main, ["Status"], "Upload")

        # Define ending time
        end = datetime.datetime.now()

        # Get duration of loop
        d = end - start

        # Update loop infos
        Reporter.addEntries(["Status"], "Duration", d.seconds, True)

        # Give user info
        print "End: " + lib.formatTime(end)



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
