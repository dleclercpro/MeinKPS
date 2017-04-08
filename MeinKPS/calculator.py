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
        self.TBRProfile.compute(self.then, self.now, self.basalProfile)

        # Build bolus profile
        self.bolusProfile.compute(self.then, self.now)

        # Compute net basal profile
        self.TBRProfile.subtract.do(self.basalProfile)



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

        # Give profile operations
        self.add = ProfileAdd(self)
        self.subtract = ProfileSubtract(self)



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

        # Show profile
        self.show()



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

        # Initialize profile components
        t = []
        y = []
        d = []

        # Initialize index for last step
        index = None

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

            # Find last step before start, which may overlap
            elif self.t[i] < self.start:

                # Store its corresponding time
                index = i

        # Add last step's time
        t.insert(0, self.t[index])

        # Add last step's value
        y.insert(0, self.y[index])

        # If durations set
        if self.d:

            # Add last step's duration
            d.insert(0, self.d[index])

        # Reassign profile
        self.t = t
        self.y = y
        self.d = d



    def inject(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INJECT
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
                dt = self.end - self.t[i]

            # Inject zero in profile
            if self.d and self.d[i] < dt:

                # Add time
                t.append(self.t[i] + self.d[i])

                # Add zero
                y.append(self.zero)

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



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of steps within profile
        m = len(self.t)

        # Get number of steps within filler
        n = len(filler.t)

        # Look for empty steps within profile
        for i in range(m):

            # Is step empty?
            if self.y[i] is None:

                # Look for missing value within filler
                for j in range(n):

                    # For all steps except last one
                    if j < n - 1:

                        # Matching criteria
                        if (filler.t[j] <= self.t[i] and
                            self.t[i] < filler.t[j + 1]):

                            # Replace missing value
                            self.y[i] = filler.y[j]

                            # Matching value found, exit
                            break

                    # For last step
                    else:

                        # Replace missing value
                        self.y[i] = filler.y[j]



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

        # Get number of steps
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

        # Zip and sort basal profile
        z = sorted(zip(self.t, self.y))

        # Reassign sorted basal profile
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



class ProfileOperation(object):

    def __init__(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize operation
        self.operation = None

        # Link with profile
        self.profile = profile



    def do(self, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of steps within base profile
        n = len(self.profile.t)

        # Regroup profiles to subtract
        profiles = list(kwds)

        # Get number of profiles to subtract
        o = len(profiles)

        # Find all steps
        steps = lib.uniqify(self.profile.t +
                            lib.flatten([x.t for x in profiles]))

        # Get global number of steps
        m = len(steps)

        # Initialize new profile
        new = []

        # Compute each step of new profile
        for i in range(m):

            # Initialize result for current step
            result = 0

            # Look for current index within base profile
            for j in range(n):

                # For all steps except last one
                if j < n - 1:

                    # Matching criteria
                    if (self.profile.t[j] <= steps[i] and
                        steps[i] < self.profile.t[j + 1]):

                        # If value exists
                        if self.profile.y[j]:

                            # Add to result
                            result += self.profile.y[j]

                        # Matching step found, exit
                        break

                # For last step
                else:

                    # If value exists
                    if self.profile.y[j]:

                        # Add to result
                        result += self.profile.y[j]

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
                        if t[k] <= steps[i] and steps[i] < t[k + 1]:

                            # If value exists
                            if y[k]:

                                # Do operation on result
                                result = self.operation(result, y[k])

                            # Matching step found, exit
                            break

                    # For last step
                    else:

                        # If value exists
                        if y[k]:

                            # Do operation on result
                            result = self.operation(result, y[k])

            # Store result for current step
            new.append(result)

        # Give user info
        print "New profile:"

        # Print new profile
        for i in range(m):
            print str(new[i]) + " - (" + lib.formatTime(steps[i]) + ")"

        # Return new profile
        return [steps, new]



class ProfileAdd(ProfileOperation):

    def __init__(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(profile)

        # Define operation
        self.operation = lambda x, y: x + y



class ProfileSubtract(ProfileOperation):

    def __init__(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(profile)

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
