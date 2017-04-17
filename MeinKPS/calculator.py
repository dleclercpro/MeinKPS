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

        # Initialize important values for calculator
        self.BGScale = None
        self.BGTargets = None
        self.ISF = None
        self.CSF = None
        self.dt = None
        self.dBGdtMax = None

        # Give BG an ISF profile
        self.isf = ISFProfile()

        # Give calculator a BG
        self.bg = BG(self)

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

        # Get current time
        now = datetime.datetime.now()

        # Compute BG
        self.bg.predict(100, now, now + datetime.timedelta(minutes = 75))

        # Compute IOB
        #self.iob.compute()

        # Store IOB
        #self.iob.store()

        # Compute COB
        #self.cob.compute()



class BG(object):

    def __init__(self, calculator):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize start time
        self.start = None

        # Initialize end time
        self.end = None

        # Initialize DIA
        self.DIA = None

        # Initialize value
        self.value = None

        # Initialize units
        self.units = None

        # Link with calculator
        self.calculator = calculator



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



    def predict(self, BG, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Use IOB and ISF to predict where BG will land after insulin activity is
        over, assuming it simply decays from now on.
        """

        # Initialize eventual BG
        eventualBG = None

        # Load necessary components
        self.load()

        # Define start time
        self.start = start

        # Define end time
        self.end = end

        # Link with ISF and IOB
        ISF = self.calculator.isf
        IOB = self.calculator.iob

        # Prepare ISF profile
        ISF.compute(self.start, self.end)

        # Get number of ISF steps
        n = len(ISF.t)

        # Initialize IOBs
        IOBs = []

        # Predict IOB at each ISF change in the future
        for i in range(n):

            # Compute IOB
            IOBs.append(IOB.compute(ISF.t[i]))

        # Initialize BG impact
        BGI = 0

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Give user info
            print ("Time step: " + lib.formatTime(ISF.t[i]) + " - " +
                                   lib.formatTime(ISF.t[i + 1]))

            # Print ISF
            print "ISF: " + str(ISF.y[i]) + " " + ISF.units

            # Compute IOB change
            dIOB = IOBs[i + 1] - IOBs[i]

            # Give user info
            print "dIOB = " + str(dIOB) + " U"

            # Compute BG change
            dBG = ISF.y[i] * dIOB

            # Give user info
            print "dBG = " + str(dBG) + " " + ISF.units[:-2]

            # Add BG impact
            BGI += dBG

            # Make some air
            print

        # Give user info
        print ("BGI (" + str(self.start) + "): " + str(round(BGI, 1)) + " " +
               ISF.units[:-2])

        # Compute eventual BG
        eventualBG = round(BG + BGI, 1)

        # Print eventual BG
        print ("Eventual BG (" + str(self.end) + "): " +
               str(eventualBG) + " " + ISF.units[:-2])

        # Return eventual BG
        return eventualBG



class IOB(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize start time
        self.start = None

        # Initialize end time
        self.end = None

        # Initialize DIA
        self.DIA = None

        # Initialize value
        self.value = None

        # Give IOB a basal profile
        self.basalProfile = BasalProfile("Standard")

        # Give IOB a TBR profile
        self.TBRProfile = TBRProfile()

        # Give IOB a bolus profile
        self.bolusProfile = BolusProfile()

        # Give IOB a suspend profile
        self.netProfile = NetProfile()

        # Give IOB an IDC
        self.idc = WalshIDC()

        # Give IOB profile operations
        self.add = Add()
        self.subtract = Subtract()

        # Define report
        self.report = "treatments.json"



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Reset IOB value.
        """

        # Give user info
        print "Resetting IOB..."

        # Reset IOB
        self.value = 0



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



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Build basal profile
        self.basalProfile.compute(self.start, self.end)

        # Build TBR profile
        self.TBRProfile.compute(self.start, self.end, self.basalProfile)

        # Build bolus profile
        self.bolusProfile.compute(self.start, self.end)

        # Build net profile using suspend times and filling with sum of net
        # basal and bolus profiles
        self.netProfile.compute(self.start, self.end,
                                self.add.do(self.subtract.do(self.TBRProfile,
                                                             self.basalProfile),
                                                             self.bolusProfile))

        # Return net profile
        return [self.netProfile.T, self.netProfile.y]



    def compute(self, end = datetime.datetime.now()):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Computing IOB..."

        # Reset value
        self.reset()

        # Load necessary components
        self.load()

        # Define end time
        self.end = end

        # Compute start time
        self.start = self.end - datetime.timedelta(hours = self.DIA)

        # Define IDC
        self.idc.define(self.DIA)

        # Get net insulin profile
        [t, y] = self.prepare()

        # Get number of steps
        n = len(t)

        # Compute IOB
        for i in range(n - 1):

            # Compute remaining factor based on integral of IDC
            R = abs(self.idc.F(t[i + 1]) - self.idc.F(t[i]))

            # Compute active insulin remaining for current step
            self.value += R * y[i]

        # Give user info
        print "IOB (" + str(self.end) + "): " + str(round(self.value, 1)) + " U"

        # Return IOB
        return self.value



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding IOB to report: '" + self.report + "'..."

        # Format time
        t = lib.formatTime(self.end)

        # Round value
        y = round(self.value, 1)

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(["IOB"], t, y)



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



class IDC(object):

    def __init__(self):

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

        # Initialize DIA
        self.DIA = None



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

    def define(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store DIA
        self.DIA = DIA

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



    def decouple(self, convert = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Decouple profile components.
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

        # Initialize current index (-1 to handle between 23:00 and 00:00 of
        # following day)
        index = -1

        # Find current step
        for i in range(n - 1):

            # Current step criteria
            if t[i] <= self.end and self.end < t[i + 1]:

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



    def filter(self, mapped = True):

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

        # If profile uses general times, map them on current time axis
        if not mapped:

            # Map
            self.map()

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
            if self.start <= self.t[i] and self.t[i] <= self.end:

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
        
        # Rebuild profile and inject zeros where needed
        for i in range(n):

            # Add step
            t.append(self.t[i])
            y.append(self.y[i])

            # Get current step duration
            d = self.d[i]

            # For all steps, except last one
            if i < n - 1:

                # Compute time between current and next steps
                dt = self.t[i + 1] - self.t[i]

            # Last step
            else:

                # Compute time between last step and profile end
                dt = self.end - self.t[i]

            # If step is a canceling one
            if not d:

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
            if self.start <= self.t[i] and self.t[i] <= self.end:

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

                # Add value
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
        for i in range(m):

            # Filling criteria
            if self.y[i] is None:

                # For all steps, except end limit
                if i < m - 1:

                    # Fill step
                    t.append(self.t[i])
                    y.append(filler.f(self.t[i], False))

                    # Look for additional steps to fill
                    for j in range(n - 1):

                        # Filling criteria
                        if (self.t[i] < filler.t[j] and
                            filler.t[j] < self.t[i + 1]):

                            # Add step
                            t.append(filler.t[j])
                            y.append(filler.y[j])

                # For last step
                else:

                    # Add step
                    t.append(filler.t[-1])
                    y.append(filler.y[-1])

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
        for i in range(1, n):

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



    def normalize(self):

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

            # Compute time difference in hours
            dt = (self.t[-1] - self.t[i]).seconds / 3600.0

            # Add step
            self.T.append(dt)

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



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Filter after mapping
        super(self.__class__, self).filter(False)



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



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Filter after mapping
        super(self.__class__, self).filter(False)



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
        super(self.__class__, self).decouple(True)

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
        super(self.__class__, self).decouple(True)

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
        super(self.__class__, self).decouple(True)

        # Get number of steps
        n = len(self.t)

        # Decouple components
        for i in range(n):

            # If resume
            if self.y[i]:

                # Convert to none and fill later
                self.y[i] = None



class ProfileOperation(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize operation
        self.operation = None

        # Initialize new profile
        self.new = Profile()



    def do(self, base, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Profiles on which operations are made cannot have "None" values
              within them!
        """

        # Reset new profile
        self.new.reset()

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
        self.new.t = lib.uniqify(base.t + lib.flatten([p.t for p in profiles]))

        # Get global number of steps
        m = len(self.new.t)

        # Get number of profiles to subtract
        n = len(profiles)

        # Compute each step of new profile
        for i in range(m):

            # Compute partial result with base profile
            result = base.f(self.new.t[i], False)

            # Look within each profile
            for p in profiles:

                # Compute partial result on current profile
                result = self.operation(result, p.f(self.new.t[i], False))

            # Store result for current step
            self.new.y.append(result)

        # Normalize new profile
        self.new.normalize()

        # Return new profile
        return self.new



class Add(ProfileOperation):

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



class Subtract(ProfileOperation):

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

    # Instanciate a calculator
    calculator = Calculator()

    # Run calculator
    calculator.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
