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
import matplotlib as mpl
import matplotlib.pyplot as plt
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

        # Initialize current time
        self.now = None

        # Initialize start of insulin action
        self.start = None

        # Initialize end of insulin action
        self.end = None

        # Initialize DIA
        self.DIA = None

        # Initialize IDC
        self.IDC = None

        # Give calculator a basal profile
        self.basal = BasalProfile("Standard")

        # Give calculator a TBR profile
        self.TBR = TBRProfile()

        # Give calculator a bolus profile
        self.bolus = BolusProfile()

        # Give calculator a net profile
        self.net = NetProfile()

        # Give calculator an ISF profile
        self.ISF = ISFProfile()

        # Give calculator a CSF profile
        #self.CSF = CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets()

        # Give calculator an IOB
        self.IOB = IOB(self)

        # Give calculator a COB
        self.COB = COB(self)

        # Give calculator a BG
        self.BG = BG(self)



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



    def prepare(self, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store end of insuline action
        self.end = end

        # Compute start of insulin action
        self.start = self.end - datetime.timedelta(hours = self.DIA)

        # Define IDC
        self.IDC = WalshIDC(self.DIA)

        # Build basal profile
        self.basal.compute(self.start, self.end)

        # Build TBR profile
        self.TBR.compute(self.start, self.end, self.basal)

        # Build bolus profile
        self.bolus.compute(self.start, self.end)

        # Build net profile using suspend times
        self.net.compute(self.start, self.end,
            self.TBR.subtract(self.basal).add(self.bolus))

        # Build ISF profile (in the future)
        self.ISF.compute(self.end,
                         self.end + datetime.timedelta(hours = self.DIA))

        # Build BG targets profile (in the future)
        self.BGTargets.compute(self.end,
                               self.end + datetime.timedelta(hours = self.DIA))



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define current time
        self.now = datetime.datetime.now()

        # Load components
        self.load()

        # Prepare components
        self.prepare(self.now)

        # Predict IOB decay
        self.IOB.predict()

        # Store IOB
        self.IOB.store()

        # Compute COB
        #self.COB.compute()

        # Compute BG
        #self.BG.predict(5.0)
        self.BG.predict(350.0)
        self.BG.shortPredict(350.0) # FIXME: why small difference with predict?
        self.BG.recommend(15.0)



class Profile(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time axis
        self.t = []

        # Initialize normalized time axis
        self.T = []

        # Initialize step durations
        self.d = []

        # Initialize y-axis
        self.y = []

        # Initialize start of profile
        self.start = None

        # Initialize end of profile
        self.end = None

        # Initialize zero
        self.zero = None

        # Initialize data
        self.data = None

        # Initialize units
        self.units = None

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

        # If step durations are set
        if self.d:

            # Inject zeros between profile steps
            self.inject()

        # Cut steps outside of profile and make sure limits are respected
        self.cut()

        # If filling needed
        if filler:

            # Fill profile
            self.fill(filler)

        # Smooth profile
        self.smooth()

        # Normalize profile
        self.normalize()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Reset profile components.
        """

        # Give user info
        print "Resetting profile..."

        # Reset time axis
        self.t = []

        # Reset normalized time axis
        self.T = []

        # Reset step durations
        self.d = []

        # Reset y-axis
        self.y = []

        # Reset data
        self.data = None



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Load profile from specified report.
        """

        # Give user info
        print "Loading profile..."

        # Load report
        Reporter.load(self.report)

        # Read data
        self.data = Reporter.getEntry(self.path, self.key)

        # Give user info
        print "'" + self.__class__.__name__ + "' loaded."



    def decouple(self, mapped = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Decouple profile components.
        """

        # Give user info
        print "Decoupling profile..."

        # Decouple components
        for t in sorted(self.data):

            # If time is mapped, convert it to datetime object
            if mapped:

                # Get time
                self.t.append(lib.formatTime(t))

            else:

                # Get time
                self.t.append(t)

            # Get value
            self.y.append(self.data[t])

        # If time is not mapped
        if not mapped:

            # Map it
            self.map()



    def map(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MAP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Mapping time..."

        # Initialize profile components
        t = []
        y = []

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

        # Initialize current index (-1 to handle between 23:00 and 00:00 of
        # following day)
        index = -1

        # Find current step
        for i in range(n - 1):

            # Current step criteria
            if t[i] <= self.end < t[i + 1]:

                # Store index
                index = i

                # Exit
                break

        # Give user info
        print "Current step: " + str(y[index]) + " (" + str(t[index]) + ")"

        # Update steps
        for i in range(n):

            # Find steps in future and bring them in the past
            if t[i] > t[index]:

                # Update time
                t[i] -= datetime.timedelta(days = 1)

        # Zip and sort profile
        z = sorted(zip(t, y))

        # Update profile
        self.t = [x for x, y in z]
        self.y = [y for x, y in z]



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Filter profile entries only to keep the ones between previously defined
        profile start and end. Keep last one before start of profile in case of
        overlapping.
        """

        # Give user info
        print "Filtering..."

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
            if self.start <= self.t[i] <= self.end:

                # Add step
                t.append(self.t[i])
                y.append(self.y[i])

                # If durations set
                if self.d:

                    # Add duration
                    d.append(self.d[i])

            # Check for last step
            elif self.t[i] < self.start:

                # Store index
                index = i

        # If last step was found
        if index is not None:

            # Add last step
            t.insert(0, self.t[index])
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

        Inject zeros after theoretical end of steps. Spot canceling steps and
        set their value to "None". Will only work if step durations are defined!
        """

        # Give user info
        print "Injecting..."

        # Initialize temporary components
        t = []
        y = []

        # Get number of steps
        n = len(self.t)

        # Add end to time axis in order to correctly compute last dt (number of
        # steps has to be computed before that!)
        self.t.append(self.end)

        # Rebuild profile and inject zeros where needed
        for i in range(n):

            # Add step
            t.append(self.t[i])
            y.append(self.y[i])

            # Get current step duration
            d = self.d[i]

            # Compute time between current and next steps
            dt = self.t[i + 1] - self.t[i]

            # If step is a canceling one
            if d == 0:

                # Replace value with zero
                y[-1] = self.zero

            # Inject zero in profile
            elif d < dt:

                # Add zero
                t.append(self.t[i] + d)
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

        Cut remaining excess steps in profile and set the latter's start and end
        based on their previously defined times.  
        """

        # Give user info
        print "Cutting..."

        # Initialize cut-off profile components
        t = []
        y = []

        # Get number of steps
        n = len(self.t)

        # Initialize index of last step before profile
        index = None

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Inclusion criteria
            if self.start <= self.t[i] <= self.end:

                # Add time
                t.append(self.t[i])

                # Add value
                y.append(self.y[i])

            # Check for last step
            elif self.t[i] < self.start:

                # Store index
                index = i

        # Start of profile
        if len(t) == 0 or t[0] != self.start:

            # Add time
            t.insert(0, self.start)

            # If last step was found
            if index is not None:

                # Extend last step's value
                y.insert(0, self.y[index])

            # Otherwise, store a None value
            else:

                # Add value
                y.insert(0, None)

        # End of profile (will always have a last value, since start of profile
        # has just been taken care of, thus no need to check for length of time
        # component)
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

        # Add end to time axis in order to correctly compute last dt (number of
        # steps has to be computed before that!)
        self.t.append(self.end)

        # Fill profile
        for i in range(m):

            # Filling criteria
            if self.y[i] is None:

                # Fill step
                t.append(self.t[i])
                y.append(filler.f(self.t[i], False))

                # Look for additional steps to fill
                for j in range(n):

                    # Filling criteria
                    if (self.t[i] < filler.t[j] < self.t[i + 1]):

                        # Add step
                        t.append(filler.t[j])
                        y.append(filler.y[j])

            # Step exists in profile
            else:

                # Add step
                t.append(self.t[i])
                y.append(self.y[i])

        # Update profile
        self.t = t
        self.y = y

        # Show current state of profile
        self.show()



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Smooth profile (remove redundant steps).
        """

        # Give user info
        print "Smoothing..."

        # Initialize components for smoothed profile
        t = []
        y = []

        # Restore start of profile
        t.append(self.t[0])
        y.append(self.y[0])

        # Get number of steps in profile
        n = len(self.t)

        # Look for redundancies
        for i in range(1, n - 1):

            # Non-redundancy criteria
            if self.y[i] != self.y[i - 1]:

                # Add step
                t.append(self.t[i])
                y.append(self.y[i])

        # Restore end of profile
        t.append(self.t[-1])
        y.append(self.y[-1])

        # Update profile
        self.t = t
        self.y = y

        # Show current state of profile
        self.show()



    def normalize(self, end = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Normalize profile's time axis (in hours from now).
        """

        # Give user info
        print "Normalizing..."

        # Get number of steps in profile
        n = len(self.t)

        # Normalize time
        for i in range(n):

            # Decide which end to use to normalize
            if end:

                # Compute time difference (from end)
                dt = (self.t[-1] - self.t[i])

            else:

                # Compute time difference (from start)
                dt = (self.t[i] - self.t[0])

            # Add step (in hours)
            self.T.append(dt.seconds / 3600.0)

        # Show current state of profile
        self.show(True)



    def show(self, normalized = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Show both profiles axes.
        """

        # Get number of profile steps
        n = len(self.t)

        # Show profile
        for i in range(n):

            # Show normalization
            if normalized:

                # Give user info
                print str(self.y[i]) + " - (" + str(self.T[i]) + ")"

            # Otherwise
            else:

                # Give user info
                print str(self.y[i]) + " - (" + str(self.t[i]) + ")"

        # Make some space to read
        print



    def f(self, t, normalized = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute profile's value (y) for a given time (t).
        """

        # Initialize result
        f = None

        # Initialize index
        index = None

        # Get desired axis
        if normalized:

            # Define axis
            axis = self.T

        else:

            # Define axis
            axis = self.t

        # Get number of steps in profile
        n = len(axis)

        # Make sure axes fit
        if n != len(self.y):

            # Exit
            sys.exit("Cannot compute f(t): axes' length do not fit.")

        # Compute profile value
        for i in range(n):

            # For all steps
            if i < n - 1:

                # Index identification criteria
                if axis[i] <= t < axis[i + 1]:

                    # Store index
                    index = i

                    # Exit
                    break

            # For last step
            else:

                # Index identification criteria
                if t == axis[-1]:

                    # Store index
                    index = -1

        # If index was found
        if index is not None:

            # Compute corresponding value
            f = self.y[index]

        # Give user info
        #print "f(" + str(t) + ") = " + str(f)

        # Return it
        return f



    def operate(self, operation, profiles):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            OPERATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Profiles on which operations are made cannot have "None" values
              within them!
        """

        # Give user info
        print "'" + self.__class__.__name__ + "'"

        # Show base profile
        self.show()

        # Give user info
        print "with: "

        # Show profiles
        for p in profiles:

            # Give user info
            print "'" + p.__class__.__name__ + "'"

            # Show profile
            p.show()

        # Generate new profile
        new = Profile()

        # Find all steps
        new.t = lib.uniqify(self.t + lib.flatten([p.t for p in profiles]))

        # Get global number of steps
        n = len(new.t)

        # Compute each step of new profile
        for i in range(n):

            # Compute partial result with base profile
            result = self.f(new.t[i], False)

            # Look within each profile
            for p in profiles:

                # Compute partial result on current profile
                result = operation(result, p.f(new.t[i], False))

            # Store result for current step
            new.y.append(result)

        # Normalize new profile
        new.normalize()

        # Return new profile
        return new



    def add(self, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define operation
        operation = lambda x, y: x + y

        # Regroup profiles to do operation with
        profiles = list(kwds)

        # Give user info
        print "Adding:"

        # Do operation
        return self.operate(operation, profiles)



    def subtract(self, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define operation
        operation = lambda x, y: x - y

        # Regroup profiles to do operation with
        profiles = list(kwds)

        # Give user info
        print "Subtracting:"

        # Do operation
        return self.operate(operation, profiles)



class BasalProfile(Profile):

    def __init__(self, choice):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define units
        self.units = "U/h"

        # Define report info
        self.report = "pump.json"
        self.path = []
        self.key = "Basal Profile (" + choice + ")"



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(False)



class TBRProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Renitialize units
        self.units = []

        # Define report info
        self.report = "treatments.json"
        self.path = []
        self.key = "Temporary Basals"



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple()

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # Get duration
            self.d.append(datetime.timedelta(minutes = self.y[i][2]))

            # Get units
            self.units.append(self.y[i][1])

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
            if self.units[i] != "U/h":

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

        # Define profile zero
        self.zero = 0

        # Define bolus delivery rate
        self.rate = 90.0

        # Define units
        self.units = "U/h"

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
        super(self.__class__, self).decouple()

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # Compute delivery time
            self.d.append(datetime.timedelta(hours = 1 / self.rate * self.y[i]))

            # Convert bolus to delivery rate
            self.y[i] = self.rate



class NetProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define units
        self.units = "U/h"

        # Define report info
        self.report = "history.json"
        self.path = ["Pump"]
        self.key = "Suspend/Resume"



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple()

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # If resume
            if self.y[i]:

                # Convert to none and fill later
                self.y[i] = None



class ISFProfile(Profile):

    def __init__(self):

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


    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.units = Reporter.getEntry([], "BG Units") + "/U"

        # Define report info
        self.key = "ISF (" + self.units + ")"

        # Load rest
        super(self.__class__, self).load()



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(False)



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start normalizing
        super(self.__class__, self).normalize(False)



class CSFProfile(Profile):

    def __init__(self):

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


    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.units = Reporter.getEntry([], "Carb Units")

        # In case of grams
        if self.units == "g":

            # Adapt units
            self.units = self.units + "/U"

        # In case of exchanges
        elif self.units == "exchange":

            # Adapt units
            self.units = "U/" + self.units

        # Define report info
        self.key = "CSF (" + self.units + ")"

        # Load rest
        super(self.__class__, self).load()



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(False)



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start normalizing
        super(self.__class__, self).normalize(False)



class BGTargets(Profile):

    def __init__(self):

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



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.units = Reporter.getEntry([], "BG Units")

        # Define report info
        self.key = "BG Targets (" + self.units + ")"

        # Load rest
        super(self.__class__, self).load()



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(self.__class__, self).decouple(False)



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start normalizing
        super(self.__class__, self).normalize(False)



class IDC(object):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Modelization of IDC as a 4th-order polynomial.
        """

        # Initialize 4th-order parameters
        self.m0 = None
        self.m1 = None
        self.m2 = None
        self.m3 = None
        self.m4 = None

        # Define DIA
        self.DIA = DIA



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Gives fraction of active insulin remaining "t" hours after enacting it.
        """

        # Compute f(t) of IDC
        f = (self.m4 * t ** 4 +
             self.m3 * t ** 3 +
             self.m2 * t ** 2 +
             self.m1 * t ** 1 +
             self.m0)

        # Return f(t)
        return f



    def F(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute F(t) of IDC
        F = (self.m4 * t ** 5 / 5 +
             self.m3 * t ** 4 / 4 +
             self.m2 * t ** 3 / 3 +
             self.m1 * t ** 2 / 2 +
             self.m0 * t ** 1 / 1)

        # Return F(t) of IDC
        return F



class WalshIDC(IDC):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(DIA)

        # Define parameters of IDC for various DIA
        if DIA == 3:

            self.m4 = -4.151e-2
            self.m3 = 2.925e-1
            self.m2 = -6.332e-1
            self.m1 = 5.553e-2
            self.m0 = 9.995e-1

        elif DIA == 4:

            self.m4 = -4.290e-3
            self.m3 = 5.465e-2
            self.m2 = -1.984e-1
            self.m1 = -5.452e-2
            self.m0 = 9.995e-1

        elif DIA == 5:

            self.m4 = -3.823e-3
            self.m3 = 5.011e-2
            self.m2 = -1.998e-1
            self.m1 = 2.694e-2
            self.m0 = 9.930e-1

        elif DIA == 6:

            self.m4 = -1.935e-3
            self.m3 = 3.052e-2
            self.m2 = -1.474e-1
            self.m1 = 3.819e-2
            self.m0 = 9.970e-1

        # Bad DIA
        else:

            # Exit
            sys.exit("No IDC found for DIA = " + str(DIA) + " h. Exiting...")



class IOB(object):

    def __init__(self, calculator):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time axis
        self.t = None

        # Initialize values
        self.y = None

        # Define report
        self.report = "treatments.json"

        # Link with calculator
        self.calculator = calculator



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Resetting IOB values..."

        # Reset time axis
        self.t = []

        # Reset values
        self.y = []



    def predict(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Predicting IOB..."

        # Reset values
        self.reset()

        # Initialize partial net insulin profile
        partProfile = Profile()

        # Link with net insulin profile
        netProfile = self.calculator.net

        # Link with DIA
        DIA = self.calculator.DIA

        # Define timestep (h)
        dt = 5.0 / 60.0

        # Compute number of steps
        n = int(DIA / dt)

        # Generate time axis
        t = np.linspace(DIA, dt, n)

        # Convert time axis to datetime objects
        t = [self.calculator.end - datetime.timedelta(hours = x) for x in t]

        # Compute IOB decay
        for i in range(n):

            # Reset partial net insulin profile
            partProfile.reset()

            # Define start/end times and their corresponding values
            partProfile.t.extend([t[i]] * 2)
            partProfile.t[-1] += datetime.timedelta(hours = DIA)
            partProfile.y.extend([None] * 2)

            # To fake natural decay, set net insulin rate to 0 at current time
            # for IOB computations in the future
            if partProfile.t[-1] > self.calculator.end:

                # Add time
                partProfile.t.insert(1, self.calculator.end)

                # Add value
                partProfile.y.insert(1, 0)

            # Fill profile
            partProfile.fill(netProfile)

            # Smooth profile
            partProfile.smooth()

            # Normalize profile
            partProfile.normalize()

            # Compute IOB for current time
            IOB = self.compute(partProfile)

            # Compute IOB prediction time
            T = t[i] + datetime.timedelta(hours = DIA)

            # Store prediction time
            self.t.append(T)

            # Store IOB
            self.y.append(IOB)

        # Give user info
        print "Predicted IOB(s):"

        # Give user info
        for i in range(n):

            # Get current time and IOB
            t = lib.formatTime(self.t[i])
            y = self.y[i]

            # Print IOB
            print str(y) + " U (" + str(t) + ")"



    def compute(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple profile components
        t = profile.T
        y = profile.y

        # Initialize current IOB
        IOB = 0

        # Get number of steps
        n = len(t)

        # Compute IOB
        for i in range(n - 1):

            # Compute remaining IOB factor based on integral of IDC
            R = abs(self.calculator.IDC.F(t[i + 1]) -
                    self.calculator.IDC.F(t[i]))

            # Compute active insulin remaining for current step
            IOB += R * y[i]

        print "IOB: " + str(IOB)

        # Return IOB
        return IOB



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding IOB to report: '" + self.report + "'..."

        # Format time
        t = lib.formatTime(self.t[0])

        # Round value
        y = round(self.y[0], 3)

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(["IOB"], t, y)



class COB(object):

    def __init__(self, calculator):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize DCA
        self.DCA = None

        # Link with calculator
        self.calculator = calculator



    def compute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



class BG(object):

    def __init__(self, calculator):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.y = None

        # Initialize prediction
        self.prediction = None

        # Initialize recommendation
        self.recommendation = None

        # Initialize units
        self.units = None

        # Define report
        self.report = "pump.json"

        # Link with calculator
        self.calculator = calculator



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset values
        self.y = []

        # Reset prediction
        self.prediction = None

        # Reset recommendation
        self.recommendation = None



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.units = Reporter.getEntry([], "BG Units")



    def predict(self, BG):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Use IOB and ISF to predict where BG will land after insulin activity is
        over, assuming a natural decay.
        """

        # Give user info
        print "Predicting BG..."
        print "Initial BG: " + str(BG)

        # Reset BG values
        self.reset()

        # Load components
        self.load()

        # Store initial BG
        self.y.append(BG)

        # Link with profiles
        IOB = self.calculator.IOB
        ISF = self.calculator.ISF

        # Get number of ISF steps
        n = len(IOB.t)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Give user info
            print ("Time: " + lib.formatTime(IOB.t[i + 1]))

            # Compute ISF
            isf = ISF.f(IOB.t[i], False)

            # Print ISF
            print "ISF: " + str(isf) + " " + ISF.units

            # Compute IOB change
            dIOB = IOB.y[i + 1] - IOB.y[i]

            # Give user info
            print "dIOB: " + str(dIOB) + " U"

            # Compute BG change
            dBG = isf * dIOB

            # Give user info
            print "dBG: " + str(dBG) + " " + self.units

            # Add BG impact
            BG += dBG

            # Print eventual BG
            print "BG: " + str(round(BG, 1)) + " " + self.units

            # Store current BG
            self.y.append(BG)

            # Make some air
            print

        # Give user info
        print "Eventual BG: " + str(round(BG, 1)) + " " + self.units

        # Return eventual BG
        return BG



    def shortPredict(self, BG):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHORTPREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Predicting BG..."
        print "Initial BG: " + str(BG)

        # Load components
        self.load()

        # Link with profiles
        IDC = self.calculator.IDC
        IOB = self.calculator.IOB
        ISF = self.calculator.ISF

        # Get number of ISF steps
        n = len(ISF.t)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Print timestep
            print ("Timestep: " + lib.formatTime(ISF.t[i]) + " @ " +
                                  lib.formatTime(ISF.t[i + 1]))

            # Print ISF
            print "ISF: " + str(ISF.y[i]) + " " + ISF.units

            # Compute IOB change
            dIOB = IOB.y[0] * (IDC.f(ISF.T[i + 1]) - IDC.f(ISF.T[i]))

            # Give user info
            print "dIOB: " + str(dIOB) + " U"

            # Compute BG change
            dBG = ISF.y[i] * dIOB

            # Give user info
            print "dBG: " + str(dBG) + " " + self.units

            # Add BG impact
            BG += dBG

            # Print eventual BG
            print "BG: " + str(round(BG, 1)) + " " + self.units

            # Make some air
            print

        # Give user info
        print "Eventual BG: " + str(round(BG, 1)) + " " + self.units

        # Return eventual BG
        return BG



    def recommend(self, BG0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECOMMEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recommend a bolus based on current BG and future target average, taking
        into account ISF step curve over the next DIA hours (assuming natural
        decay of insulin).
        """

        # Give user info
        print "Recommending treatment..."

        # Load components
        self.load()

        # Link with profiles
        BGTargets = self.calculator.BGTargets
        IDC = self.calculator.IDC
        ISF = self.calculator.ISF

        # Get number of ISF steps
        n = len(ISF.t)

        # Initialize factor between recommended bolus and BG difference with
        # average target
        factor = 0

        # Compute factor
        for i in range(n - 1):

            # Update factor with current step
            factor += ISF.y[i] * (IDC.f(ISF.T[i + 1]) - IDC.f(ISF.T[i]))

        # Compute eventual BG based on IOB
        BG = self.shortPredict(BG0)

        # Find average of target to reach after natural insulin decay
        target = sum(BGTargets.y[-1]) / 2.0

        # Compute BG difference with average target
        dBG = target - BG

        # Compute necessary bolus
        bolus = dBG / factor

        # Give user info
        print "Time: " + lib.formatTime(BGTargets.t[-1])
        print "BG Target: " + str(BGTargets.y[-1]) + " " + str(self.units)
        print "BG Target Average: " + str(target) + " " + str(self.units)
        print "BG: " + str(round(BG0, 1)) + " " + str(self.units)
        print "Eventual BG: " + str(round(BG, 1)) + " " + str(self.units)
        print "dBG: " + str(round(dBG, 1)) + " " + str(self.units)
        print "Recommended bolus: " + str(round(bolus, 1)) + " U"



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a calculator
    calculator = Calculator()

    # Run calculator
    calculator.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
