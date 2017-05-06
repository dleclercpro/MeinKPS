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
import time



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
        self.CSF = CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets()

        # Give calculator a BG profile
        self.BGProfile = BGProfile()

        # Give calculator an IOB
        self.IOB = IOB(self)

        # Give calculator a COB
        self.COB = COB(self)

        # Give calculator a BG
        self.BG = BG(self)

        # Initialize units
        self.units = {"BG": None,
                      "Carbs": None,
                      "ISF": None,
                      "CSF": None}

        # Initialize maxes
        self.max = {"Basal": None,
                    "Bolus": None}



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
        #self.IOB.store()

        # Compute COB
        #self.COB.compute()

        # Compute BG
        #self.BG.decay(5.0)
        self.BG.predict(5.0)

        # Analyze BG
        self.BG.analyze()

        # Recommend action
        #self.recommend(5.0)



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

        # Read units
        self.units["BG"] = Reporter.getEntry([], "BG Units")

        # Give user info
        print "BG units: " + str(self.units["BG"])

        # Read max basal
        self.max["Basal"] = Reporter.getEntry(["Settings"], "Max Basal")

        # Give user info
        print "Max basal: " + str(self.max["Basal"]) + " U/h"

        # Read max bolus
        self.max["Bolus"] = Reporter.getEntry(["Settings"], "Max Bolus")

        # Give user info
        print "Max bolus: " + str(self.max["Bolus"]) + " U"



    def prepare(self, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute start of insulin action
        start = end - datetime.timedelta(hours = self.DIA)

        # Compute future end
        future = end + datetime.timedelta(hours = self.DIA)

        # Define IDC
        self.IDC = WalshIDC(self.DIA)

        # Build basal profile
        self.basal.compute(start, end)

        # Build TBR profile
        self.TBR.compute(start, end, self.basal)

        # Build bolus profile
        self.bolus.compute(start, end)

        # Build net profile using suspend times
        self.net.compute(start, end, self.TBR.subtract(self.basal)
                                             .add(self.bolus))

        # Build ISF profile (in the future)
        self.ISF.compute(end, future)

        # Build BG targets profile (in the future)
        self.BGTargets.compute(end, future)

        # Build BG profile
        self.BGProfile.compute(start, end)



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

        # Get number of ISF steps
        n = len(self.ISF.t)

        # Initialize factor between recommended bolus and BG difference with
        # average target
        factor = 0

        # Compute factor
        for i in range(n - 1):

            # Update factor with current step
            factor += self.ISF.y[i] * (self.IDC.f(self.ISF.T[i + 1]) -
                                       self.IDC.f(self.ISF.T[i]))

        # Compute eventual BG based on IOB
        BG = self.BG.predict(BG0)

        # Find average of target to reach after natural insulin decay
        target = sum(self.BGTargets.y[-1]) / 2.0

        # Compute BG difference with average target
        dBG = target - BG

        # Compute necessary bolus
        bolus = dBG / factor

        # Give user info
        print "Time: " + lib.formatTime(self.BGTargets.t[-1])
        print "BG target: " + str(self.BGTargets.y[-1]) + " " + self.units["BG"]
        print "BG target average: " + str(target) + " " + self.units["BG"]
        print "BG: " + str(round(BG0, 1)) + " " + self.units["BG"]
        print "Eventual BG: " + str(round(BG, 1)) + " " + self.units["BG"]
        print "dBG: " + str(round(dBG, 1)) + " " + self.units["BG"]
        print "Recommended bolus: " + str(round(bolus, 1)) + " U"

        # If more insulin needed
        if bolus > 0:

            # Find maximal basal allowed
            maxTB = min(self.max["Basal"],
                        3 * max(self.ISF.y),
                        4 * self.ISF.y[0])

            # Find time required to enact equivalent of recommended bolus with
            # max TB (m)
            T = abs(int(round(bolus / maxTB * 60)))

            # Define maximum time allowed to enact equivalent of bolus with max
            # TB
            maxT = 30

            # Give user info
            print "Max basal: " + str(self.max["Basal"]) + " U/h"
            print "3x max daily basal: " + str(3 * max(self.ISF.y)) + " U/h"
            print "4x current basal: " + str(4 * self.ISF.y[0]) + " U/h"
            print "Resulting max basal: " + str(maxTB) + " U/h"
            print "Time required with resulting max basal: " + str(T) + " m"
            print "Max time to enact recommendation: " + str(maxT) + " m"

            # Compare with 
            if T > maxT:

                # Give user info
                print ("External action required: maximal time allowed for " +
                       "TB to enact insulin recommendation exceeded.")

            else:

                # Give user info
                print ("No external action required: maximal time allowed " +
                       "for TB to enact insulin recommendation not exceeded.")

        # If less insulin needed
        elif bolus < 0:

            self.basal.show()

        # If insulin is fine
        else:
            pass



class Profile(object):

    def __init__(self, start = None, end = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time axis
        self.t = []

        # Initialize normalized time axis
        self.T = []

        # Initialize y-axis
        self.y = []

        # Initialize step durations
        self.d = []

        # Initialize profile type
        self.type = None

        # Initialize start of profile
        self.start = start

        # Initialize end of profile
        self.end = end

        # Initialize zero
        self.zero = None

        # Initialize data
        self.data = None

        # Initialize time mapping
        self.mapped = None

        # Initialize units
        self.units = None

        # Initialize report info
        self.report = None
        self.path = []
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

        # Filter profile components
        self.filter()

        # If step durations are set
        if self.d:

            # Inject zeros between profile steps
            self.inject()

        # Cut entries outside of time limits
        self.cut()

        # If filling needed
        if filler:

            # Fill profile
            self.fill(filler)

        # If step profile
        if self.type == "Step":

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

        # Reset y-axis
        self.y = []

        # Reset step durations
        self.d = []

        # Reset data
        self.data = None



    def update(self, t, y, d = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Update profile components.
        """

        # Update components
        self.t = t
        self.y = y

        # If durations set
        if d:

            # Update them as well
            self.d = d

        # Show current state of profile
        self.show()



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



    def decouple(self):

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
            if self.mapped:

                # Get time
                self.t.append(lib.formatTime(t))

            else:

                # Get time
                self.t.append(t)

            # Get value
            self.y.append(self.data[t])

        # If time is not mapped
        if not self.mapped:

            # Map it
            self.map(self.end)



    def map(self, now):

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

        # Get number of entries
        n = len(self.t)

        # Rebuild profile
        for i in range(n):

            # Get time
            T = self.t[i]

            # Generate time object
            T = datetime.time(hour = int(T[:2]), minute = int(T[3:]))

            # Generate datetime object
            T = datetime.datetime.combine(self.end, T)

            # Add time
            t.append(T)

            # Add value
            y.append(self.y[i])

        # Initialize current index (-1 to handle between 23:00 and 00:00 of
        # following day)
        index = -1

        # Find current time
        for i in range(n - 1):

            # Current time criteria
            if t[i] <= now < t[i + 1]:

                # Store index
                index = i

                # Exit
                break

        # Update time
        for i in range(n):

            # Find times in future and bring them in the past
            if t[i] > t[index]:

                # Update time
                t[i] -= datetime.timedelta(days = 1)

        # Zip and sort profile
        z = sorted(zip(t, y))

        # Update profile
        self.update([x for x, y in z],
                    [y for x, y in z])



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

        # Get number of entries
        n = len(self.t)

        # Keep entries within start and end (+1 in case of overlapping)
        for i in range(n):

            # Compare to time limits
            if self.start <= self.t[i] <= self.end:

                # Add entry
                t.append(self.t[i])
                y.append(self.y[i])

                # If durations set
                if self.d:

                    # Add duration
                    d.append(self.d[i])

            # Check for last entry
            elif self.t[i] < self.start:

                # Store index
                index = i

        # If no last entry was found
        if index is not None:

            # Add last entry
            t.insert(0, self.t[index])
            y.insert(0, self.y[index])

            # If durations set
            if self.d:

                # Add last entry's duration
                d.insert(0, self.d[index])

        # Update profile
        self.update(t, y, d)



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
        self.update(t, y)



    def cut(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Cut remaining excess entries in profile and ensure the latter starts and
        ends according to the previously defined limit times.  
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

            # Update last step
            elif self.t[i] < self.start:

                # Store index
                index = i

        # Ensure ends of step profiles fit
        if self.type == "Step":

            # Start of profile
            if len(t) == 0 or t[0] != self.start:

                # Add time
                t.insert(0, self.start)

                # Extend last step's value
                y.insert(0, self.y[index])

            # End of profile
            if t[-1] != self.end:

                # Add time
                t.append(self.end)

                # Add rate
                y.append(y[-1])

        # Update profile
        self.update(t, y)



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
        self.update(t, y)



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
        self.update(t, y)



    def normalize(self, end = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Normalize profile's time axis (in hours).
        """

        # Give user info
        print "Normalizing..."

        # Get number of steps in profile
        n = len(self.t)

        # Normalize time
        for i in range(n):

            # Decide which reference time to use for normalization
            if end:

                # From end
                T = self.end

            else:

                # From start
                T = self.start

            # Compare time to reference
            if self.t[i] >= T:

                # Compute positive time difference (s)
                dt = (self.t[i] - T).seconds

            else:

                # Compute negative time difference (s)
                dt = -(T - self.t[i]).seconds

            # Add step (h)
            self.T.append(dt / 3600.0)

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
        y = None

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
            y = self.y[index]

        # Give user info
        #print "f(" + str(t) + ") = " + str(y)

        # Return it
        return y



    def operate(self, operation, profiles):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            OPERATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Profiles on which operations are made must have same limits.
              They also cannot have "None" values within them!
        """

        # Read base profile name
        baseName = self.__class__.__name__

        # Give user info
        print "'" + baseName + "'"

        # Show base profile
        self.show()

        # Give user info
        print "with: "

        # Show profiles
        for p in profiles:

            # Read profile name
            profileName = p.__class__.__name__

            # Give user info
            print "'" + profileName + "'"

            # Show profile
            p.show()

            # If limits do not fit
            if p.start != self.start or p.end != self.end:

                # Exit
                sys.exit("Operation impossible due to '" + profileName + "': " +
                         "limits do not fit with '" + baseName + "'. " +
                         "Exiting...")

        # Generate new profile with same limits
        new = Profile(self.start, self.end)

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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = False

        # Define units
        self.units = "U/h"

        # Define report info
        self.report = "pump.json"
        self.key = "Basal Profile (" + choice + ")"



class TBRProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = True

        # Renitialize units
        self.units = []

        # Define report info
        self.report = "treatments.json"
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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = True

        # Define units
        self.units = "U/h"

        # Define report info
        self.report = "treatments.json"
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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = True

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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = False

        # Define report info
        self.report = "pump.json"



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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = False

        # Define report info
        self.report = "pump.json"



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

        # Define type
        self.type = "Step"

        # Define time mapping
        self.mapped = False

        # Define report info
        self.report = "pump.json"



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



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start normalizing
        super(self.__class__, self).normalize(False)



class BGProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define type
        self.type = "Dot"

        # Define time mapping
        self.mapped = True

        # Define report info
        self.report = "BG.json"



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load("pump.json")

        # Read units
        self.units = Reporter.getEntry([], "BG Units")

        # Load rest
        super(self.__class__, self).load()



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

        Gives fraction of active insulin remaining in body t hours after
        enacting it. Takes negative input!
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
            self.m3 = -2.925e-1
            self.m2 = -6.332e-1
            self.m1 = -5.553e-2
            self.m0 = 9.995e-1

        elif DIA == 4:

            self.m4 = -4.290e-3
            self.m3 = -5.465e-2
            self.m2 = -1.984e-1
            self.m1 = 5.452e-2
            self.m0 = 9.995e-1

        elif DIA == 5:

            self.m4 = -3.823e-3
            self.m3 = -5.011e-2
            self.m2 = -1.998e-1
            self.m1 = -2.694e-2
            self.m0 = 9.930e-1

        elif DIA == 6:

            self.m4 = -1.935e-3
            self.m3 = -3.052e-2
            self.m2 = -1.474e-1
            self.m1 = -3.819e-2
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

        # Link with net insulin profile
        net = self.calculator.net

        # Initialize partial net insulin profile
        part = Profile()

        # Link with DIA
        DIA = self.calculator.DIA

        # Define timestep (h)
        dt = 5.0 / 60.0

        # Compute number of steps
        n = int(DIA / dt) + 1

        # Generate time axis
        t = np.linspace(DIA, 0, n)

        # Convert time axis to datetime objects
        t = [net.end - datetime.timedelta(hours = x) for x in t]

        # Compute IOB decay
        for i in range(n):

            # Reset partial profile
            part.reset()

            # Set limits of partial profile (moving window)
            part.start = t[i]
            part.end = t[i] + datetime.timedelta(hours = DIA)

            # Initialize start/end times
            part.t.append(t[i])
            part.t.append(net.end)

            # Initialize start/end values
            part.y.append(None)
            part.y.append(0)

            # Fill profile
            part.fill(net)

            # Smooth profile
            part.smooth()

            # Normalize profile
            part.normalize()

            # Compute IOB for current time
            IOB = self.compute(part)

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
            R = self.calculator.IDC.F(t[i + 1]) - self.calculator.IDC.F(t[i])

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



    def analyze(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ANALYZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        [dBGdt, dt] = lib.derivate(self.calculator.BGProfile.y,
                                   self.calculator.BGProfile.T)
        dBGdt /= 60.0
        dt *= 60.0

        print dBGdt
        print dt



    def decay(self, BG):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECAY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Use IOB and ISF to predict where BG will land after insulin activity is
        over, assuming a natural decay.
        """

        # Give user info
        print "Predicting BG..."
        print "Initial BG: " + str(BG)

        # Reset BG values
        self.reset()

        # Store initial BG
        self.y.append(BG)

        # Link with profiles
        IOB = self.calculator.IOB
        ISF = self.calculator.ISF

        # Link with units
        self.units = self.calculator.units["BG"]

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



    def predict(self, BG):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # FIXME: why small difference with decay?

        # Give user info
        print "Predicting BG..."
        print "Initial BG: " + str(BG)

        # Link with profiles
        IDC = self.calculator.IDC
        IOB = self.calculator.IOB
        ISF = self.calculator.ISF

        # Link with units
        self.units = self.calculator.units["BG"]

        # Get number of ISF steps
        n = len(ISF.t)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Print timestep
            print ("Timestep: " + lib.formatTime(ISF.t[i]) + " @ " +
                                  lib.formatTime(ISF.t[i + 1]))

            # Print ISF
            print "ISF: " + str(ISF.y[i]) + " " + ISF.units

            # Adapt normalized time to fit IDC time domain
            a = ISF.T[i + 1] - self.calculator.DIA
            b = ISF.T[i] - self.calculator.DIA

            # Compute IOB change
            dIOB = IOB.y[0] * (IDC.f(b) - IDC.f(a))

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
