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
        self.basalProfile = None

        # Initialize TBR profile
        self.TBRProfile = None

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

        # Keep TBRs that are within DIA (+1 in case it overlaps DIA)
        for t in sorted(self.TBRs):

            # Compare to time limit (is it within DIA?)
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

        # Keep boluses that are within DIA (+1 in case it overlaps DIA)
        for t in sorted(self.boluses):

            # Compare to time limit (is it within DIA?)
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
        print "Filtered TBRs:"

        # Print filtered TBRs
        lib.printJSON(self.TBRs)

        # Give user info
        print "Filtered boluses:"

        # Print filtered TBRs
        lib.printJSON(self.boluses)



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize TBR components
        t = []
        rates = []
        units = []
        durations = []

        # Decouple TBR components
        for i in sorted(self.TBRs):

            # Get time
            t.append(lib.formatTime(i))

            # Get rate
            rates.append(self.TBRs[i][0])

            # Get units
            units.append(self.TBRs[i][1])

            # Get duration
            durations.append(self.TBRs[i][2])

        # Return decoupled TBRs
        return [t, rates, units, durations]



    def profilize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PROFILIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize TBR profile
        profile = {"Times": [],
                 "Rates": []}

        # Decouple TBRs
        [t, rates, units, durations] = self.decouple()

        # Add fake current TBR
        t.append(self.now)
        rates.append(None)
        units.append(None)
        durations.append(None)

        # Compute number of TBRs
        n = len(t)
        
        # Inject natural TBR ends
        for i in range(n):

            # Add time
            profile["Times"].append(t[i])

            # Add rate
            profile["Rates"].append(rates[i])

            # Do not do on fake current TBR!
            if i < n - 1:

                # Read planed duration
                d = datetime.timedelta(minutes = durations[i])

                # Compute time between current TBR and next one
                dt = t[i + 1] - t[i]

                # Add a zero to profile (normal basal) if necessary
                if d < dt:

                    # Add time
                    profile["Times"].append(t[i] + d)

                    # Add rate
                    profile["Rates"].append(None)

        # Update number of TBRs
        n = len(profile["Times"])

        # Give user info
        print "TBR steps:"

        # Show TBR steps
        for i in range(n):
            print (str(profile["Rates"][i]) + " (" +
                   str(profile["Times"][i]) + ")")

        # Extract index of first TBR within DIA
        for i in range(n):

            # Is it within DIA?
            if profile["Times"][i] >= self.then:

                # Exit
                break

        # Add first TBR, which should be end of DIA, if not already there
        if profile["Times"][i] != self.then:

            # Add time
            profile["Times"].insert(i, self.then)

            # Add rate
            profile["Rates"].insert(i, profile["Rates"][i - 1])

        # Discard TBRs outside DIA
        profile["Times"] = profile["Times"][i:]
        profile["Rates"] = profile["Rates"][i:]

        # Update number of TBRs
        n = len(profile["Times"])

        # Give user info
        print "TBR profile:"

        # Show TBR profile
        for i in range(n):
            print (str(profile["Rates"][i]) + " (" +
                   str(profile["Times"][i]) + ")")



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # FIXME: take into account bolus enacting time
        # TODO: deal with uncompleted bolus

        # Load necessary components in order to compute IOB
        self.load()

        # Get current time
        self.now = datetime.datetime.now()

        # Get time limit of insulin action
        self.then = self.now - datetime.timedelta(hours = self.DIA)

        # Filter TBRs and boluses to keep only the active ones
        self.filter()

        # Build TBR profile
        self.profilize()

        # Compute difference between basal and TBRs



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
