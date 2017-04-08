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

        # Initialize last time
        self.then = None

        # Initialize DIA
        self.DIA = None

        # Give IOB a basal profile
        self.basalProfile = BasalProfile("Standard")

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

        # Load necessary components
        self.load()

        # Get current time
        self.now = datetime.datetime.now()

        # Compute last time
        self.then = self.now - datetime.timedelta(hours = self.DIA)

        # Build basal profile
        self.basalProfile.compute(self.then, self.now)

        # Build TBR profile
        #self.TBRProfile.compute(self.then, self.now)

        # Build bolus profile
        #self.bolusProfile.compute(self.then, self.now)



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

        # Initialize start of profile
        self.start = None

        # Initialize end of profile
        self.end = None

        # Initialize data
        self.data = None

        # Initialize report info
        self.report = None
        self.path = None
        self.key = None



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



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report
        Reporter.load(self.report)

        # Read data
        self.data = Reporter.getEntry(self.path, self.key)

        # Get number of profile steps
        n = len(self.data)

        # Give user info
        print "Number of steps in '" + self.__class__.__name__ + "': " + str(n)



    def decouple(self, convert = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple components
        for i in sorted(self.data):

            # Convert time to datetime object
            if convert:

                # Get time
                self.t.append(lib.formatTime(i))

            else:

                # Get time
                self.t.append(i)

            # Get rest
            self.y.append(self.data[i])



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



    def build(self, d = None, zero = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize temporary components
        t = []
        y = []

        # Get number of steps
        n = len(self.t)
        
        # Build profile and inject zeros where needed
        for i in range(n):

            # Add time
            t.append(self.t[i])

            # Add data
            y.append(self.y[i])

            # For all steps
            if i < n - 1:

                # Compute time between current and next steps
                dt = self.t[i + 1] - self.t[i]

            # For profile end
            else:

                # Compute time between current step and profile end
                dt = self.start - self.t[i]

            # Inject zero in profile
            if d and d[i] < dt:

                # Add time
                t.append(self.t[i] + d)

                # Add zero
                y.append(zero)

        # Update profile components
        self.t = t
        self.y = y



    def cut(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # End of profile
        if self.t[-1] != self.end:

            # Generate current step
            self.t.append(self.end)
            self.y.append(self.y[-1])

        # Get number of steps
        n = len(self.t)

        # Inject start of profile
        for i in range(n):

            # Find index of first step within profile
            if self.t[i] >= self.start:

                # Index found, exit
                break

        # Start of profile
        if self.t[i] != self.start:

            # Add time
            self.t.insert(i, self.start)

            # Add rate
            self.y.insert(i, self.y[i - 1])

        # Discard steps outside profile
        del self.t[:i]
        del self.y[:i]



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of profile steps
        n = len(self.t)

        # Give user info
        print "Profile '" + self.__class__.__name__ + "':"

        # Show profile
        for i in range(n):
            print str(self.t[i]) + " - " + str(self.y[i])



    def compute(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define start of profile
        self.start = start

        # Define end of profile
        self.end = end

        # Reset profile
        self.reset()

        # Load profile components
        self.load()

        # Decouple profile components
        self.decouple()

        # Filter profile steps
        self.filter()

        # Build profile and inject zeros between steps if required
        self.build()

        # Cut steps outside of profile and make sure limits are respected
        self.cut()

        # Show profile
        self.show()



class BasalProfile(Profile):

    def __init__(self, choice):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define report info
        self.report = "pump.json"
        self.path = []
        self.key = "Basal Profile (" + choice + ")"



    def map(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MAP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of basal steps
        n = len(self.t)

        # Convert times
        for i in range(n):

            # Get current time step
            T = self.t[i]

            # Generate time object
            T = datetime.time(hour = int(T[:2]), minute = int(T[3:]))

            # Generate datetime object
            T = datetime.datetime.combine(self.end, T)

            # Update current time step
            self.t[i] = T

        # Initialize current basal index
        index = None

        # Find current basal
        for i in range(n):

            # Current basal criteria
            if self.t[i % n] <= self.end and self.t[(i + 1) % n] > self.end:

                # Store index
                index = i

                # Index found, exit
                break

        # Give user info
        print ("Current basal: " + str(self.y[index]) + " (" +
                                   str(self.t[index]) + ")")

        # Update basal steps
        for i in range(n):

            # Find basal in future
            if self.t[i] > self.t[index]:

                # Update basal
                self.t[i] -= datetime.timedelta(days = 1)



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Map basal profile onto DIA
        self.map()

        # Initialize temporary profile components
        t = []
        y = []

        # Get number of basal steps
        n = len(self.t)

        # Keep basal steps that are within DIA (+1 in case it overlaps DIA)
        for i in range(n):

            # Compare to time limit (is it within DIA?)
            if self.t[i] >= self.start and self.t[i] <= self.end:

                # Store time
                t.append(self.t[i])

                # Store active basal
                y.append(self.y[i])

            # Find last basal step before DIA, which may overlap
            elif self.t[i] < self.start:

                # Store its corresponding time
                last = i

        # Add last time
        t.append(self.t[last])

        # Add last basal
        y.append(self.y[last])

        # Zip and sort basal profile lists
        z = sorted(zip(t, y))

        # Reassign basal profile
        self.t = [x for x, y in z]
        self.y = [y for x, y in z]



class TBRProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define report info
        self.report = "treatments.json"
        self.path = []
        self.key = "Temporary Basals"

        # Initialize TBR units
        self.u = []

        # Initialize TBR durations
        self.d = []



    def decouple(self, convert = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(convert)

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # Get duration
            self.d.append(self.y[i][2])

            # Get units
            self.u.append(self.y[i][1])

            # Update to rate
            self.y[i] = self.y[i][0]



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

        # Get number of steps
        n = len(self.t)

        # Keep TBRs that are within DIA (+1 in case it overlaps DIA)
        for i in range(n):

            # Format time
            T = lib.formatTime(self.t[i])

            # Compare to time limit (is it within DIA?)
            if T >= self.start and T <= self.end:

                # Check for units mismatch
                if self.u[i] != units:

                    # TODO: deal with % TBRs?
                    sys.exit("TBR units mismatch. Exiting...")

                # Store active TBR
                TBRs[self.t[i]] = self.y[i]

            # Find last TBR enacted before DIA, which may overlap
            elif T < self.start:

                # Store its corresponding time
                last = t

        # Add last TBR
        TBRs[last] = self.data[last]

        # Update TBRs
        self.data = TBRs



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple TBRs
        [t, TBRs] = self.decouple(True)

        # End of TBR profile should be current TBR
        if t[-1] != self.end:

            # Generate current TBR
            t.append(self.end)
            TBRs.append([None] * 3)

        # Get number of TBRs
        n = len(t)
        
        # Start building TBR profile and inject natural TBR ends when needed
        for i in range(n):

            # Add time
            self.t.append(t[i])

            # Add rate
            self.y.append(TBRs[i][0])

            # Not computable for current TBR!
            if i < n - 1:

                # Read planed duration
                d = datetime.timedelta(minutes = TBRs[i][2])

                # Compute time between current TBR and next one
                dt = t[i + 1] - t[i]

                # Add a "None" to profile (to be replaced later by normal basal)
                if d < dt:

                    # Add time
                    self.t.append(t[i] + d)

                    # Add rate
                    self.y.append(None)



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

        # Define report info
        self.report = "treatments.json"
        self.path = []
        self.key = "Boluses"

        # Define bolus delivery rate
        self.rate = 40.0 # (s/U)



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize temporary dictionary for active boluses
        boluses = {}

        # Keep boluses that are within DIA (+1 in case it overlaps DIA)
        for t in sorted(self.data):

            # Format time
            T = lib.formatTime(t)

            # Compare to time limit (is it within DIA?)
            if T >= self.start and T <= self.end:

                # Store active bolus
                boluses[t] = self.data[t]

            # Find last bolus enacted before DIA, which may overlap
            elif T < self.start:

                # Store its corresponding time
                last = t

        # Add last bolus
        boluses[last] = self.data[last]

        # Update boluses
        self.data = boluses



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple boluses
        [t, boluses] = self.decouple(True)

        # End of bolus profile should be current time
        if t[-1] != self.end:

            # Generate fake current bolus
            t.append(self.end)
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
            if self.t[i] >= self.start:

                # Index found, exit
                break

        # Start of bolus profile should be at beginning of DIA
        if self.t[i] != self.start:

            # Add time
            self.t.insert(i, self.start)

            # Add rate
            self.y.insert(i, self.y[i - 1])

        # Discard boluses outside of DIA
        del self.t[:i]
        del self.y[:i]



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
