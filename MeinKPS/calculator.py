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

        # Give IOB profile operations
        self.add = Add()
        self.subtract = Subtract()



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
        self.TBRProfile.compute(self.then, self.now, self.basalProfile)

        # Build bolus profile
        #self.bolusProfile.compute(self.then, self.now)

        # Compute net basal profile
        self.subtract.do(self.TBRProfile, self.basalProfile)



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
        self.t = []

        # Initialize y-axis
        self.y = []

        # Initialize step durations
        self.d = []

        # Initialize start of profile
        self.start = None

        # Initialize end of profile
        self.end = None

        # Initialize zero
        self.zero = None

        # Initialize data
        self.data = None

        # Initialize report info
        self.report = None
        self.path = None
        self.key = None



    def compute(self, start, end, filler = None):

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

        # Inject zeros between profile steps if required
        self.inject()

        # Cut steps outside of profile and make sure limits are respected
        self.cut()

        # If filling needed
        if filler:

            # Fill profile
            self.fill(filler)



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Resetting profile..."

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

        # Give user info
        print "Loading profile..."

        # Load report
        Reporter.load(self.report)

        # Read data
        self.data = Reporter.getEntry(self.path, self.key)

        # Give user info
        print "'" + self.__class__.__name__ + "' loaded."



    def decouple(self, convert = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Decoupling profile..."

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

        # Give user info
        print "Filtering..."

        # Initialize profile components
        t = []
        y = []
        d = []

        # Initialize index for last step
        index = -1

        # Get number of steps
        n = len(self.t)

        # Keep steps within start and end (+1 in case of overlapping)
        for i in range(n):

            # Compare to time limits
            if self.t[i] >= self.start and self.t[i] <= self.end:

                # Store time
                t.append(self.t[i])

                # Store value
                y.append(self.y[i])

                # If durations set
                if self.d:

                    # Store duration
                    d.append(self.d[i])

                # Store index of last step before start
                if index == -1:

                    # Store it
                    index = i - 1

        # Add last step's time
        t.insert(0, self.t[index])

        # Add last step's value
        y.insert(0, self.y[index])

        # If durations set
        if self.d:

            # Add last step's duration
            d.insert(0, self.d[index])

        # Update profile
        self.t = t
        self.y = y
        self.d = d

        # Show current state of profile
        self.show()



    def inject(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Injecting..."

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
                dt = self.end - self.t[i]

            # Inject zero in profile
            if self.d and self.d[i] < dt:

                # Add time
                t.append(self.t[i] + self.d[i])

                # Add zero
                y.append(self.zero)

        # Update profile
        self.t = t
        self.y = y

        # Show current state of profile
        self.show()



    def cut(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Cutting..."

        # Initialize cut-off profile components
        t = []
        y = []

        # Get number of steps
        n = len(self.t)

        # Initialize index of last step before profile
        last = -1

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Inclusion criteria
            if self.start <= self.t[i] and self.t[i] <= self.end:

                # Add time
                t.append(self.t[i])

                # Add value
                y.append(self.y[i])

                # If last index not yet found
                if last == -1:

                    # Store index
                    last = i - 1

        # Start of profile
        if not t or t[0] != self.start:

            # Add time
            t.insert(0, self.start)

            # Add rate
            y.insert(0, self.y[last])

        # End of profile
        if t[-1] != self.end:

            # Add time
            t.append(self.end)

            # Add rate
            y.append(y[-1])

        # Update profile
        self.t = t
        self.y = y

        # Show current state of profile
        self.show()



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Profile and filler are assumed to have same start/end limits!
        """

        # Give user info
        print "Filling..."

        # Initialize new profile components
        t = []
        y = []

        # Get number of steps within profile
        m = len(self.t)

        # Get number of steps within filler
        n = len(filler.t)

        # Fill profile
        for i in range(m - 1):

            # Filling criteria
            if self.y[i] is None:

                # Look for missing value
                for j in range(n - 1):

                    # Missing value criteria
                    if filler.t[j] <= self.t[i] and self.t[i] < filler.t[j + 1]:

                        # Add time
                        t.append(self.t[i])

                        # Add value
                        y.append(filler.y[j])

                        # Missing value found: exit
                        break

                # Look for additional steps to fill
                for j in range(n - 1):

                    # Filling criteria
                    if self.t[i] < filler.t[j] and filler.t[j] < self.t[i + 1]:

                        # Add time
                        t.append(filler.t[j])

                        # Add value
                        y.append(filler.y[j])

            else:

                # Add time
                t.append(self.t[i])

                # Add value
                y.append(self.y[i])

        # Deal with end of profile
        if self.y[-1] is None:

            # Add time
            t.append(filler.t[-1])

            # Add value
            y.append(filler.y[-1])

        # Update profile
        self.t = t
        self.y = y

        # Show current state of profile
        self.show()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of profile steps
        n = len(self.t)

        # Show profile
        for i in range(n):

            # Give user info
            print str(self.y[i]) + " - (" + str(self.t[i]) + ")"

        # Make some space to read
        print



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

        # Initialize profile components
        t = []
        y = []

        # Initialize time differences to now
        delta = []

        # Get number of steps
        n = len(self.t)

        # Rebuild profile
        for i in range(n):

            # Get time step
            T = self.t[i]

            # Generate time object
            T = datetime.time(hour = int(T[:2]), minute = int(T[3:]))

            # Generate datetime object
            T = datetime.datetime.combine(self.end, T)

            # Add time step
            t.append(T)

            # Add value
            y.append(self.y[i])

        # Initialize current basal index
        index = -1

        # Find current basal
        for i in range(n):

            # Current basal criteria
            if t[i % n] <= self.end and self.end < t[(i + 1) % n]:

                # Store index
                index = i

                # Index found, exit
                break

        # Give user info
        print "Current basal: " + str(y[index]) + " (" + str(t[index]) + ")"

        # Update basal steps
        for i in range(n):

            # Find basal steps in future and bring them in the past
            if t[i] > t[index]:

                # Update basal
                t[i] -= datetime.timedelta(days = 1)

        # Zip and sort basal profile
        z = sorted(zip(t, y))

        # Update basal profile
        self.t = [x for x, y in z]
        self.y = [y for x, y in z]



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Map basal profile onto DIA
        self.map()

        # Finish filtering
        super(self.__class__, self).filter()



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

        # Initialize units
        self.u = []



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(True)

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # Get duration
            self.d.append(datetime.timedelta(minutes = self.y[i][2]))

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

        # Start filtering
        super(self.__class__, self).filter()

        # Get number of steps
        n = len(self.t)

        # Check for incorrect units
        for i in range(n):

            # Units currently supported
            if self.u[i] != "U/h":

                # Give user info
                sys.exit("TBR units mismatch. Exiting...")



class BolusProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define bolus profile zero
        self.zero = 0

        # Define bolus delivery rate
        self.rate = 40.0 # (s/U)

        # Define report info
        self.report = "treatments.json"
        self.path = []
        self.key = "Boluses"



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(True)

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # Compute delivery time
            self.d.append(datetime.timedelta(seconds = self.rate * self.y[i]))

            # Convert bolus to delivery rate
            self.y[i] = 1 / self.rate



class Operation(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize operation
        self.operation = None

        # Initialize new profile times
        self.t = []

        # Initialize new profile values
        self.y = []



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Smoothing..."

        # Initialize components for smoothed profile
        t = []
        y = []

        # Get number of steps in new profile
        n = len(self.t)

        # Look for redundancies
        for i in range(1, n - 1):

            # Non-redundancy criteria
            if self.y[i - 1] != self.y[i] or self.y[i] != self.y[i + 1]:

                # Add time
                t.append(self.t[i])

                # Add value
                y.append(self.y[i])

        # Restore start/end of profile
        t.insert(0, self.t[0])
        y.insert(0, self.y[0])
        t.append(self.t[-1])
        y.append(self.y[-1])

        # Update profile
        self.t = t
        self.y = y

        # Get new number of steps after smoothing
        n = len(self.t)

        # Print smoothed profile
        for i in range(n):

            # Give user info
            print str(self.y[i]) + " - (" + lib.formatTime(self.t[i]) + ")"



    def do(self, base, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Regroup profiles to do operation with
        profiles = list(kwds)

        # Give user info
        print "Doing '" + self.__class__.__name__ + "' on...:"

        # Give user info
        print "'" + base.__class__.__name__ + "'"

        # Show base profile
        base.show()

        # Give user info
        print "...using:"

        # Show profiles
        for p in profiles:

            # Give user info
            print "'" + p.__class__.__name__ + "'"

            # Show profile
            p.show()

        # Find all steps
        self.t = lib.uniqify(base.t + lib.flatten([x.t for x in profiles]))

        # Get global number of steps
        m = len(self.t)

        # Get number of steps within base profile
        n = len(base.t)

        # Get number of profiles to subtract
        o = len(profiles)

        # Compute each step of new profile
        for i in range(m):

            # Initialize result for current step
            result = 0

            # Look for current index within base profile
            for j in range(n):

                # For all steps except last one
                if j < n - 1:

                    # Matching criteria
                    if (base.t[j] <= self.t[i] and
                        self.t[i] < base.t[j + 1]):

                        # Add to result
                        result += base.y[j]

                        # Matching step found, exit
                        break

                # For last step
                else:

                    # Add to result
                    result += base.y[j]

            # Look for current index within each profile
            for j in range(o):

                # Get components of current profile to subtract
                t = profiles[j].t
                y = profiles[j].y

                # Get number of steps within current profile
                p = len(t)

                # Match with global step
                for k in range(p):

                    # For all steps except last one
                    if k < p - 1:

                        # Matching criteria
                        if t[k] <= self.t[i] and self.t[i] < t[k + 1]:

                            # Do operation on result
                            result = self.operation(result, y[k])

                            # Matching step found, exit
                            break

                    # For last step
                    else:

                        # Do operation on result
                        result = self.operation(result, y[k])

            # Store result for current step
            self.y.append(result)

        # Give user info
        print "New profile:"

        # Print new profile
        for i in range(m):

            # Give user info
            print str(self.y[i]) + " - (" + lib.formatTime(self.t[i]) + ")"

        # Make some space to read
        print

        # Flatten new profile (remove redundant steps)
        self.smooth()



class Add(Operation):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initializing
        super(self.__class__, self).__init__()

        # Define operation
        self.operation = lambda x, y: x + y



class Subtract(Operation):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initializing
        super(self.__class__, self).__init__()

        # Define operation
        self.operation = lambda x, y: x - y



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
