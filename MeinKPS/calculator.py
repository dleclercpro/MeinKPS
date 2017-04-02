#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    calculator

    Author:   David Leclerc

    Version:  0.1

    Date:     27.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import numpy as np
import datetime
import sys



# USER LIBRARIES
import lib
import reporter



# Instanciate a reporter
Reporter = reporter.Reporter()



class Calculator(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize important values for calculator
        self.BGScale = None
        self.BGTargets = None
        self.ISF = None
        self.CSF = None
        self.dt = None
        self.dBGdtMax = None

        # Give calculator an IOB
        self.iob = IOB()

        # Give calculator a COB
        self.cob = COB()



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute IOB
        self.iob.compute()

        # Compute COB
        self.cob.compute()



class IOB(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.now = None

        # Initialize end time of insulin action based on DIA
        self.then = None

        # Initialize DIA
        self.DIA = None

        # Initialize basal profile
        self.basal = None

        # Initialize TBRs
        self.TBRs = None

        # Initialize boluses
        self.boluses = None



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # TODO: deal with various basal profiles?

        # Load pump report
        Reporter.load("pump.json")

        # Read DIA
        self.DIA = Reporter.getEntry(["Settings"], "DIA") 

        # Read basal profile
        self.basal = Reporter.getEntry([], "Basal Profile (Standard)")

        # Load treatments report
        Reporter.load("treatments.json")

        # Read past TBRs
        self.TBRs = Reporter.getEntry([], "Temporary Basals")

        # Read past boluses
        self.boluses = Reporter.getEntry([], "Boluses")

        # Give user info
        print "Number of steps in basal profile: " + str(len(self.basal))
        print "Number of TBRs enacted: " + str(len(self.TBRs))
        print "Number of boluses enacted: " + str(len(self.boluses))



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize temporary dictionary for active TBRs
        TBRs = {}

        # Initialize temporary dictionary for active boluses
        boluses = {}

        # Define TBR units
        units = "U/h"

        # Keep TBRs that are within DIA (+1 in case if extends over DIA)
        for t in sorted(self.TBRs):

            # Compare to time limit
            if lib.formatTime(t) >= self.then:

                # Check for units mismatch
                if self.TBRs[t][1] != units:

                    # TODO: deal with % TBRs?
                    sys.exit("TBR units mismatch. Exiting...")

                # Store active TBR
                TBRs[t] = self.TBRs[t]

            # Find last TBR until begin of insulin action time
            else:

                # Store its corresponding time
                last = t

        # Add last TBR
        TBRs[last] = self.TBRs[last]

        # Update TBRs
        self.TBRs = TBRs

        # Keep boluses that are within DIA (+1 in case if extends over DIA)
        for t in sorted(self.boluses):

            # Compare to time limit
            if lib.formatTime(t) >= self.then:

                # Store active TBR
                boluses[t] = self.boluses[t]

            # Find last bolus until begin of insulin action time
            else:

                # Store its corresponding time
                last = t

        # Add last bolus
        boluses[last] = self.boluses[last]

        # Update boluses
        self.boluses = boluses

        # Give user info
        print "Active TBRs:"

        # Print active TBRs
        lib.printJSON(self.TBRs)

        # Give user info
        print "Active boluses:"

        # Print active TBRs
        lib.printJSON(self.boluses)



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # FIXME: take into account bolus enacting time

        # Load necessary components in order to compute IOB
        self.load()

        # Get current time
        self.now = datetime.datetime.now()

        # Get time limit of insulin action
        self.then = self.now - datetime.timedelta(hours = self.DIA)

        # Filter TBRs and boluses to keep only the active ones
        self.filter()

        # Build active TBRs profile
        t = []
        TBRs = [] 
        activeTBRs = []

        for i in sorted(self.TBRs):
            t.append(lib.formatTime(i))
            TBRs.append(self.TBRs[i])

        # Check if last TBR is relevant
        # FIXME
        if t[0] + datetime.timedelta(minutes = TBRs[0][2]) > self.then:
            pass

        # Add current time to compute last TBR duration
        t.append(self.now)

        for i in range(len(t) - 1):

            dt = datetime.timedelta(minutes = TBRs[i][2])
            dT = t[i + 1] - t[i]

            if dT < dt:
                print str(TBRs[i][0]) + " (" + str(dT) + ")"
                activeTBRs.append([dt])

            else:
                print str(TBRs[i][0]) + " (" + str(dt) + ")"

        # Compute difference between basal and TBRs
        #lib.printJSON(self.basal)
        #lib.printJSON(self.TBRs)



class COB(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize DCA
        self.DCA = None



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a basal calculator for me
    calculator = Calculator()

    # Run calculator
    calculator.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
