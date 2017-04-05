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

        # Initialize DIA
        self.DIA = None

        # Give IOB a basal profile
        self.basalProfile = BasalProfile()

        # Give IOB a TBR profile
        self.TBRProfile = TBRProfile()

        # Give IOB a bolus profile
        self.bolusProfile = BolusProfile()



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current time
        self.now = datetime.datetime.now()

        # Load necessary components
        self.load()

        # Build basal profile
        self.basalProfile.compute("Standard")

        # Build TBR profile
        self.TBRProfile.compute(self.now, self.DIA)

        # Build bolus profile
        self.bolusProfile.compute(self.now, self.DIA)



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load("pump.json")

        # Read DIA
        self.DIA = Reporter.getEntry(["Settings"], "DIA")

        # Give user info
        print "DIA: " + str(self.DIA) + " h"



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



class Profile(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time axis
        self.t = None

        # Initialize y-axis
        self.y = None



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset time axis
        self.t = []

        # Reset y-axis
        self.y = []



class BasalProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Initialize basal
        self.basal = None

        # Initialize basal profile choice
        self.choice = None



    def compute(self, choice):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store basal profile choice
        self.choice = choice

        # Reset basal profile
        self.reset()

        # Load necessary components
        self.load()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load("pump.json")

        # Read basal profile
        self.basal = Reporter.getEntry([], "Basal Profile (" + self.choice +
                                           ")")

        # Give user info
        print ("Number of steps in basal profile '" + self.choice + "': " +
               str(len(self.basal)))



class TBRProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Initialize TBRs
        self.TBRs = None

        # Initialize current time
        self.now = None

        # Initialize time at which insulin action ends
        self.then = None



    def compute(self, now, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store current time
        self.now = now

        # Compute time limit of insulin action
        self.then = now - datetime.timedelta(hours = DIA)

        # Reset TBR profile
        self.reset()

        # Load necessary components
        self.load()

        # Filter TBRs and keep only active ones
        self.filter()

        # Build TBR profile steps
        self.build()

        # Cut TBRs outside of DIA
        self.cut()

        # Show TBR profile
        self.show()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load treatments report
        Reporter.load("treatments.json")

        # Read past TBRs
        self.TBRs = Reporter.getEntry([], "Temporary Basals")

        # Give user info
        print "Number of TBRs enacted: " + str(len(self.TBRs))



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize temporary dictionary for active TBRs
        TBRs = {}

        # Define correct TBR units
        units = "U/h"

        # Keep TBRs that are within DIA (+1 in case it overlaps DIA)
        for t in sorted(self.TBRs):

            # Format time
            T = lib.formatTime(t)

            # Compare to time limit (is it within DIA?)
            if T >= self.then and T <= self.now:

                # Check for units mismatch
                if self.TBRs[t][1] != units:

                    # TODO: deal with % TBRs?
                    sys.exit("TBR units mismatch. Exiting...")

                # Store active TBR
                TBRs[t] = self.TBRs[t]

            # Find last TBR enacted before DIA, which may overlap
            elif T < self.then:

                # Store its corresponding time
                last = t

        # Add last TBR
        TBRs[last] = self.TBRs[last]

        # Update TBRs
        self.TBRs = TBRs



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



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple TBRs
        [t, rates, units, durations] = self.decouple()

        # End of TBR profile should be current TBR
        if t[-1] != self.now:

            # Generate fake current TBR
            t.append(self.now)
            rates.append(None)
            units.append(None)
            durations.append(None)

        # Get number of TBRs
        n = len(t)
        
        # Start building TBR profile and inject natural TBR ends when needed
        for i in range(n):

            # Add time
            self.t.append(t[i])

            # Add rate
            self.y.append(rates[i])

            # Not computable for current TBR!
            if i < n - 1:

                # Read planed duration
                d = datetime.timedelta(minutes = durations[i])

                # Compute time between current TBR and next one
                dt = t[i + 1] - t[i]

                # Add a "None" to profile (to be replaced later by normal basal)
                if d < dt:

                    # Add time
                    self.t.append(t[i] + d)

                    # Add rate
                    self.y.append(None)



    def cut(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of TBRs
        n = len(self.t)

        # Find index "i" of first TBR within DIA
        for i in range(n):

            # Is it within DIA?
            if self.t[i] >= self.then:

                # Index found, exit
                break

        # Start of TBR profile should be at beginning of DIA
        if self.t[i] != self.then:

            # Add time
            self.t.insert(i, self.then)

            # Add rate
            self.y.insert(i, self.y[i - 1])

        # Discard TBRs outside of DIA
        del self.t[:i]
        del self.y[:i]



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of TBRs
        n = len(self.t)

        # Give user info
        print "TBR profile:"

        # Show TBR profile
        for i in range(n):
            print str(self.t[i]) + " - " + str(self.y[i])



class BolusProfile(Profile):

    # TODO: - Take into account bolus enacting time
    #       - Deal with uncompleted bolus

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Initialize boluses
        self.boluses = None

        # Initialize current time
        self.now = None

        # Initialize time at which insulin action ends
        self.then = None

        # Define bolus delivery rate
        self.rate = 40.0 # (s/U)



    def compute(self, now, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store current time
        self.now = now

        # Compute time limit of insulin action
        self.then = now - datetime.timedelta(hours = DIA)

        # Reset bolus profile
        self.reset()

        # Load necessary components
        self.load()

        # Filter boluses and keep only active ones
        self.filter()

        # Build bolus profile steps
        self.build()

        # Cut boluses outside of DIA
        self.cut()

        # Show bolus profile
        self.show()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load treatments report
        Reporter.load("treatments.json")

        # Read past boluses
        self.boluses = Reporter.getEntry([], "Boluses")

        # Give user info
        print "Number of boluses enacted: " + str(len(self.boluses))



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize temporary dictionary for active boluses
        boluses = {}

        # Keep boluses that are within DIA (+1 in case it overlaps DIA)
        for t in sorted(self.boluses):

            # Format time
            T = lib.formatTime(t)

            # Compare to time limit (is it within DIA?)
            if T >= self.then and T <= self.now:

                # Store active bolus
                boluses[t] = self.boluses[t]

            # Find last bolus enacted before DIA, which may overlap
            elif T < self.then:

                # Store its corresponding time
                last = t

        # Add last bolus
        boluses[last] = self.boluses[last]

        # Update boluses
        self.boluses = boluses



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize bolus components
        t = []
        boluses = []

        # Decouple bolus components
        for i in sorted(self.boluses):

            # Get time
            t.append(lib.formatTime(i))

            # Get bolus
            boluses.append(self.boluses[i])

        # Return decoupled boluses
        return [t, boluses]



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple boluses
        [t, boluses] = self.decouple()

        # End of bolus profile should be current time
        if t[-1] != self.now:

            # Generate fake current bolus
            t.append(self.now)
            boluses.append(0)

        # Get number of boluses
        n = len(t)
        
        # Start building bolus profile and inject natural bolus ends according
        # to bolus delivery rate
        for i in range(n):

            # Add time
            self.t.append(t[i])

            # If bolus
            if boluses[i]:

                # Add rate
                self.y.append(1 / self.rate)

            else:

                # Add rate
                self.y.append(0)

            # Not computable for current TBR!
            if i < n - 1:

                # Compute delivery time
                d = datetime.timedelta(seconds = self.rate * boluses[i])

                # Compute time between current TBR and next one
                dt = t[i + 1] - t[i]

                # Add a "None" to profile (to be replaced later by normal basal)
                if d < dt:

                    # Add time
                    self.t.append(t[i] + d)

                    # Add rate
                    self.y.append(0)



    def cut(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of boluses
        n = len(self.t)

        # Find index "i" of first bolus within DIA
        for i in range(n):

            # Is it within DIA?
            if self.t[i] >= self.then:

                # Index found, exit
                break

        # Start of bolus profile should be at beginning of DIA
        if self.t[i] != self.then:

            # Add time
            self.t.insert(i, self.then)

            # Add rate
            self.y.insert(i, self.y[i - 1])

        # Discard boluses outside of DIA
        del self.t[:i]
        del self.y[:i]



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of boluses
        n = len(self.t)

        # Give user info
        print "Bolus profile:"

        # Show bolus profile
        for i in range(n):
            print str(self.t[i]) + " - " + str(self.y[i])



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
