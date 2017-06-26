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
import copy
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

        # Initialize DIA
        self.DIA = None

        # Initialize IDC
        self.IDC = None

        # Give calculator a basal profile
        self.basal = BasalProfile("Standard")

        # Give calculator a TB profile
        self.TB = TBProfile()

        # Give calculator a bolus profile
        self.bolus = BolusProfile()

        # Give calculator a net profile
        self.net = SuspendProfile()

        # Give calculator an IOB profile
        self.IOB = FutureIOBProfile(PastIOBProfile())

        # Give calculator a COB profile
        self.COB = COBProfile()

        # Give calculator an ISF profile
        self.ISF = ISFProfile()

        # Give calculator a CSF profile
        self.CSF = CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets()

        # Give calculator a BG profile
        self.BG = FutureBGProfile(PastBGProfile())

        # Initialize pump's max values
        self.max = {"Basal": None,
                    "Bolus": None}



    def run(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load components
        self.load()

        # Prepare components
        self.prepare(now)

        # Recommend TB and return it
        return self.recommend()



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

        # Read max basal
        self.max["Basal"] = Reporter.getEntry(["Settings"], "Max Basal")

        # Give user info
        print "Max basal: " + str(self.max["Basal"]) + " U/h"

        # Read max bolus
        self.max["Bolus"] = Reporter.getEntry(["Settings"], "Max Bolus")

        # Give user info
        print "Max bolus: " + str(self.max["Bolus"]) + " U"



    def prepare(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute past start of insulin action
        past = now - datetime.timedelta(hours = self.DIA)

        # Compute future end of insulin action
        future = now + datetime.timedelta(hours = self.DIA)

        # Build basal profile
        self.basal.build(past, now)

        # Build TB profile
        self.TB.build(past, now, self.basal)

        # Build bolus profile
        self.bolus.build(past, now)

        # Build net profile using suspend times
        self.net.build(past, now, self.TB.subtract(self.basal).add(self.bolus))

        # Define IDC
        self.IDC = WalshIDC(self.DIA)

        # Build past IOB profile
        self.IOB.past.build(past, now)

        # Build future IOB profile
        self.IOB.build(self.net, self.IDC)

        # Build COB profile
        #self.COB.build(past, now)

        # Build ISF profile (over the next DIA)
        self.ISF.build(now, future)

        # Build CSF profile (over the next DIA)
        #self.CSF.build(now, future)

        # Build BG targets profile (over the next DIA)
        self.BGTargets.build(now, future)

        # Build past BG profile
        self.BG.past.build(past, now)

        # Build future BG profile
        self.BG.build(self.IOB, self.ISF)



    def recommend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECOMMEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recommend a bolus based on latest BG and future target average, taking
        into account ISF step curve over the next DIA hours (assuming natural
        decay of insulin).
        """

        # Give user info
        print "Recommending treatment..."

        # Compute eventual BG after complete IOB decay
        naiveBG = self.BG.expect(self.IDC.DIA, self.IOB)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        [deltaBG, BGI, expectedBGI] = self.BG.analyze(self.IOB, self.ISF)

        # Update eventual BG
        eventualBG = naiveBG + deltaBG

        # Compute BG difference with average target
        dBG = np.mean(self.BGTargets.y[-1]) - eventualBG

        # Compute necessary dose
        dose = self.BG.dose(dBG, self.ISF, self.IDC)

        # Give user info
        print "Target: " + str(self.BGTargets.y[-1]) + " " + self.BG.u
        print "Current BG: " + str(self.BG.past.y[-1]) + " " + self.BG.u
        print "Current ISF: " + str(self.ISF.y[0]) + " " + self.BG.u + "/U"
        print "Naive eventual BG: " + str(round(naiveBG, 1)) + " " + self.BG.u
        print "Eventual BG: " + str(round(eventualBG, 1)) + " " + self.BG.u
        print "dBG: " + str(round(dBG, 1)) + " " + self.BG.u
        print "Recommended dose: " + str(round(dose, 1)) + " U"

        # Define time to enact equivalent of dose (m)
        T = 0.5

        # Give user info
        print "Enactment time: " + str(T) + " h"

        # Find required basal difference to enact over given time (round to
        # pump's precision)
        dTB = round(dose / T, 2)

        # Compute TB to enact 
        TB = self.basal.y[-1] + dTB

        # Give user info
        print "Current basal: " + str(self.basal.y[-1]) + " U/h"
        print "Required basal difference: " + str(dTB) + " U/h"
        print "Temporary basal to enact: " + str(TB) + " U/h"

        # Convert enactment time to minutes
        T *= 60

        # If less insulin is needed
        if dose < 0:

            # Define minimal basal allowed (U/h)
            minTB = 0

            # Is required TB allowed?
            if TB < minTB:

                # Give user info
                print ("External action required: negative basal required. " +
                       "Eat something!")

                # Stop insulin delivery
                return [minTB, "U/h", T]

        # If more insulin is needed
        elif dose > 0:

            # Find maximal basal allowed (U/h)
            maxTB = min(self.max["Basal"],
                        3 * self.basal.max,
                        4 * self.basal.y[0])

            # Give user info
            print "Theoretical max basal: " + str(self.max["Basal"]) + " U/h"
            print "3x max daily basal: " + str(3 * self.basal.max) + " U/h"
            print "4x current basal: " + str(4 * self.basal.y[0]) + " U/h"
            print "Max basal selected: " + str(maxTB) + " U/h"

            # Is required TB allowed?
            if TB > maxTB:

                # Give user info
                print ("External action required: maximal basal exceeded. " +
                       "Enact dose manually!")

                # Max out TB
                return [maxTB, "U/h", T]

        # No modification to insulin dosage necessary
        else:

            # Give user info
            print ("No modification to insulin dosage necessary.")

            # No TB recommendation
            return None

        # Look for conflictual info
        if (np.sign(BGI) == -1 and eventualBG > max(self.BGTargets.y[-1]) or
            np.sign(BGI) == 1 and eventualBG < min(self.BGTargets.y[-1])):

            # Give user info
            print ("Conflictual information: BG decreasing/rising although " +
                   "expected to land higher/lower than target range.")

            # No TB recommendation
            return None

        # Otherwise everything is fine
        else:

            # Give user info
            print ("Loop may enact TB recommendation.")

            # Return TB recommendation
            return [TB, "U/h", T]



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



    def verify(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Verify that given time is within insulin's range of action.
        """

        # If too old
        if t < -self.DIA:

            # Bring it back up
            t = -self.DIA

        # If too new
        elif t > 0:

            # Bring it back down
            t = 0

        # Return verified time
        return t



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Gives fraction of active insulin remaining in body t hours after
        enacting it. Takes negative input!
        """

        # Verify time
        t = self.verify(t)

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

        # Verify time
        t = self.verify(t)

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



class Profile(object):

    def __init__(self, start = None, end = None, norm = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize time axis
        self.T = []

        # Initialize normalized time axis
        self.t = []

        # Initialize y-axis
        self.y = []

        # Initialize derivative
        self.dydt = []

        # Initialize step durations
        self.d = []

        # Initialize units
        self.u = None

        # Initialize profile start
        self.start = start

        # Initialize profile end
        self.end = end

        # Initialize time reference
        self.norm = norm

        # Initialize min/max values
        self.min = None
        self.max = None

        # Initialize zero
        self.zero = None

        # Initialize data
        self.data = None

        # Initialize report info
        self.report = None
        self.path = []
        self.key = None

        # Initialize profile type
        self.type = "Step"



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Reset profile components.
        """

        # Give user info
        print "Resetting..."

        # Reset components
        self.T = []
        self.t = []
        self.y = []
        self.dydt = []



    def build(self, start, end, filler = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Building..."

        # Define start of profile
        self.start = start

        # Define end of profile
        self.end = end

        # Load profile components
        self.load()

        # Decouple profile components
        self.decouple()

        # Filter profile components
        self.filter()

        # Inject zeros between profile steps
        self.inject()

        # Cut entries outside of time limits
        self.cut()

        # If filling needed
        if filler:

            # Fill profile
            self.fill(filler)

        # Smooth profile
        self.smooth()

        # Normalize profile
        self.normalize()

        # Compute profile derivative
        self.derivate()

        # Show profile
        self.show()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Load profile components from specified report.
        """

        # Give user info
        print "Loading..."

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

        FIXME: does not work when no entry stored.
        """

        # Give user info
        print "Decoupling components..."

        # Reset components
        self.reset()

        # Decouple components
        for t in sorted(self.data):

            # Get time and convert it to datetime object if possible
            self.T.append(lib.formatTime(t))

            # Get value
            self.y.append(self.data[t])

        # If time is not mapped
        if len(self.T) and type(self.T[0]) is datetime.time:

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

        # If past profile
        if self.norm == "Start":

            # Define now
            now = self.start

        # If past profile
        elif self.norm == "End":

            # Define now
            now = self.end

        # Initialize profile components
        T = []
        y = []

        # Get number of entries
        n = len(self.T)

        # Rebuild profile
        for i in range(n):

            # Add time
            T.append(datetime.datetime.combine(now, self.T[i]))

            # Add value
            y.append(self.y[i])

        # Initialize current index (-1 to handle between 23:00 and 00:00 of
        # following day)
        index = -1

        # Find current time
        for i in range(n - 1):

            # Current time criteria
            if T[i] <= now < T[i + 1]:

                # Store index
                index = i

                # Exit
                break

        # Update time
        for i in range(n):

            # Find times in future and bring them in the past
            if T[i] > T[index]:

                # Update time
                T[i] -= datetime.timedelta(days = 1)

        # Zip and sort profile
        z = sorted(zip(T, y))

        # Update profile
        self.T = [x for x, y in z]
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
        T = []
        y = []
        d = []

        # Initialize index for last step
        index = None

        # Get number of entries
        n = len(self.T)

        # Keep entries within start and end (+1 in case of overlapping)
        for i in range(n):

            # Compare to time limits
            if self.start <= self.T[i] <= self.end:

                # Add entry
                T.append(self.T[i])
                y.append(self.y[i])

                # If durations set
                if self.d:

                    # Add duration
                    d.append(self.d[i])

            # Check for last entry
            elif self.T[i] < self.start:

                # Store index
                index = i

        # If no last entry was found
        if index is not None:

            # Add last entry
            T.insert(0, self.T[index])
            y.insert(0, self.y[index])

            # If durations set
            if self.d:

                # Add last entry's duration
                d.insert(0, self.d[index])

        # Update profile
        self.T = T
        self.y = y
        self.d = d



    def inject(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Inject zeros after theoretical end of steps. Spot canceling steps and
        set their value to "None". Will only work if step durations are defined!
        """

        # If step durations are set
        if self.d:

            # Give user info
            print "Injecting..."

            # Initialize temporary components
            T = []
            y = []

            # Get number of steps
            n = len(self.T)

            # Add end to time axis in order to correctly compute last dt (number
            # of steps has to be computed before that!)
            self.T.append(self.end)

            # Rebuild profile and inject zeros where needed
            for i in range(n):

                # Add step
                T.append(self.T[i])
                y.append(self.y[i])

                # Get current step duration
                d = self.d[i]

                # Compute time between current and next steps
                dt = self.T[i + 1] - self.T[i]

                # If step is a canceling one
                if d == 0:

                    # Replace value with zero
                    y[-1] = self.zero

                # Inject zero in profile
                elif d < dt:

                    # Add zero
                    T.append(self.T[i] + d)
                    y.append(self.zero)

            # Update profile
            self.T = T
            self.y = y

        # No step durations
        else:

            # Give user info
            print "No step durations available."



    def cut(self, a = None, b = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Cut remaining excess entries in profile and ensure the latter starts and
        ends according to the previously defined limit times.

        FIXME: does not work when first entry happens later than profile start.
        """

        # Give user info
        print "Cutting..."

        # If no limits given
        if a is None and b is None:

            # Set default limits
            a = self.start
            b = self.end

        # Verify limit types
        if type(a) is not type(b):

            # Exit
            sys.exit("Type of ends do not match. Exiting...")

        # Get desired axis
        if type(a) is not datetime.datetime:

            # Exit
            sys.exit("Cannot cut profile using normalized time limits yet. " +
                     "Exiting...")

        # Initialize cut-off profile components
        T = []
        y = []

        # Get number of steps
        n = len(self.T)

        # Initialize index of last step before profile
        index = None

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Inclusion criteria
            if a <= self.T[i] <= b:

                # Add time
                T.append(self.T[i])

                # Add value
                y.append(self.y[i])

            # Update last step
            elif self.T[i] < a:

                # Store index
                index = i

        # Ensure ends of step profile fit
        if self.type == "Step":

            # Start of profile
            if len(T) == 0 or T[0] != a:

                # Add time
                T.insert(0, a)

                # If precedent step was found
                if index is not None:

                    # Extend precedent step's value
                    y.insert(0, self.y[index])

                # Otherwise
                else:

                    # Add missing value
                    y.insert(0, None)

            # End of profile
            if T[-1] != b:

                # Add time
                T.append(b)

                # Add rate
                y.append(y[-1])

        # Update profile
        self.T = T
        self.y = y



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Filling..."

        # Initialize new profile components
        T = []
        y = []

        # Get number of steps within profile
        m = len(self.T)

        # Get number of steps within filler
        n = len(filler.T)

        # Add end to time axis in order to correctly compute last dt (number of
        # steps has to be computed before that!)
        self.T.append(self.end)

        # Fill profile
        for i in range(m):

            # Filling criteria
            if self.y[i] is None:

                # Fill step
                T.append(self.T[i])
                y.append(filler.f(self.T[i]))

                # Look for additional steps to fill
                for j in range(n):

                    # Filling criteria
                    if (self.T[i] < filler.T[j] < self.T[i + 1]):

                        # Add step
                        T.append(filler.T[j])
                        y.append(filler.y[j])

            # Step exists in profile
            else:

                # Add step
                T.append(self.T[i])
                y.append(self.y[i])

        # Update profile
        self.T = T
        self.y = y



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Smooth profile (remove redundant steps).
        """

        # If step profile
        if self.type == "Step":

            # Give user info
            print "Smoothing..."

            # Initialize components for smoothed profile
            T = []
            y = []

            # Restore start of profile
            T.append(self.T[0])
            y.append(self.y[0])

            # Get number of steps in profile
            n = len(self.T)

            # Look for redundancies
            for i in range(1, n - 1):

                # Non-redundancy criteria
                if self.y[i] != self.y[i - 1]:

                    # Add step
                    T.append(self.T[i])
                    y.append(self.y[i])

            # Restore end of profile
            T.append(self.T[-1])
            y.append(self.y[-1])

            # Update profile
            self.T = T
            self.y = y

        # Dot profiles
        else:

            # Give user info
            print "Only step profiles can be smoothed."



    def normalize(self, T = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Normalize profile's time axis (h).
        """

        # Give user info
        print "Normalizing..."

        # Check if profile is normalizable
        if self.T:

            # Verify if norm was left empty
            if T is None:

                # Decide which reference time to use for normalization
                if self.norm == "Start":

                    # From start
                    T = self.start

                elif self.norm == "End":

                    # From end
                    T = self.end

                else:

                    # Exit
                    sys.exit("Time axis cannot be normalized: profile does " +
                             "not have a norm. Exiting...")

            # Before using given reference time, verify its type
            elif type(T) is not datetime.datetime:

                # Exit
                sys.exit("Time axis can only be normalized using a datetime " +
                         "object. Exiting...")

            # Initialize normalized axis
            t = []

            # Get number of steps in profile
            n = len(self.T)

            # Normalize time
            for i in range(n):

                # Add step (h)
                t.append(lib.normalizeTime(self.T[i], T))

            # Update normalized axis
            self.t = t

        # Otherwise
        else:

            # Give user info
            print "Profiles without time axes cannot be normalized."



    def derivate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DERIVATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Derivate dot typed profiles using their normalized time axis.
        """

        # Check if profile is differentiable
        if self.t and self.type == "Dot":

            # Give user info
            print "Derivating..."

            # Derivate
            self.dydt = lib.derivate(self.y, self.t)

        # Otherwise
        else:

            # Give user info
            print "Only normalized dot typed profiles can be derivated."



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Show profile components.
        """

        # Define profile dictionary
        profile = {"Standard t-axis": [self.T, self.y],
                   "Normalized t-axis": [self.t, self.y],
                   "Derivative": [self.t, self.dydt]}

        # Loop on each profile component
        for p in profile:

            # Get axes
            axes = profile[p]

            # If component exists
            if axes[0] and axes[1]:

                # Give user info
                print p

                # Read number of entries
                n = len(axes[1])

                # Show profile
                for i in range(n):

                    # Get time
                    t = axes[0][i]

                    # Format time if necessary
                    if type(t) is not float:

                        # Format it
                        t = lib.formatTime(t)

                    # Get value
                    y = axes[1][i]

                    # Format value if necessary
                    if type(y) is float or type(y) is np.float64:

                        # Format it
                        y = round(y, 1)

                    # Give user info
                    print str(y) + " - (" + str(t) + ")"



    def f(self, t):

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
        if type(t) is datetime.datetime:

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
            sys.exit("Cannot compute f(t): axes' length do not fit. Exiting...")

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

        # Return result
        return y



    def validate(self, operands):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VALIDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read base profile name
        base = self.__class__.__name__

        # Give user info
        print "'" + base + "'"

        # Show base profile
        self.show()

        # Give user info
        print "with: "

        # Show profiles
        for p in operands:

            # Read profile name
            profile = p.__class__.__name__

            # Give user info
            print "'" + profile + "'"

            # Show profile
            p.show()

            # If limits do not fit
            if p.start != self.start or p.end != self.end:

                # Exit
                sys.exit("Operation impossible due to '" + profile + "': " +
                         "limits do not fit with '" + base + "'. " +
                         "Exiting...")



    def operate(self, operation, operands):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            OPERATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Profiles on which operations are made must have same limits.
              They also cannot have "None" values within them!
        """

        # Verify validity of operation
        self.validate(operands)

        # Generate new profile with same limits
        new = Profile(self.start, self.end, self.norm)

        # Merge all steps
        new.T = lib.uniqify(self.T + lib.flatten([p.T for p in operands]))

        # Get global number of steps
        n = len(new.T)

        # Compute each step of new profile
        for i in range(n):

            # Compute partial result with base profile
            result = self.f(new.T[i])

            # Look within each profile
            for p in operands:

                # Compute partial result on current profile
                result = operation(result, p.f(new.T[i]))

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

        # Give user info
        print "Adding:"

        # Do operation
        return self.operate(operation, list(kwds))



    def subtract(self, *kwds):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define operation
        operation = lambda x, y: x - y

        # Give user info
        print "Subtracting:"

        # Do operation
        return self.operate(operation, list(kwds))



class PastProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastProfile, self).__init__()

        # Define time reference
        self.norm = "End"



class FutureProfile(Profile):

    def __init__(self, past = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureProfile, self).__init__()

        # Define time reference
        self.norm = "Start"

        # Link with past profile
        self.past = past



class BasalProfile(PastProfile):

    def __init__(self, profile):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BasalProfile, self).__init__()

        # Define units
        self.u = "U/h"

        # Define report info
        self.report = "pump.json"
        self.key = "Basal Profile (" + profile + ")"



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(BasalProfile, self).decouple()

        # Get min/max factors
        self.min = min(self.y)
        self.max = max(self.y)



class TBProfile(PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(TBProfile, self).__init__()

        # Renitialize units
        self.u = []

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
        super(TBProfile, self).decouple()

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # Get duration
            self.d.append(datetime.timedelta(minutes = self.y[i][2]))

            # Get units
            self.u.append(self.y[i][1])

            # Get rate
            self.y[i] = self.y[i][0]



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start filtering
        super(TBProfile, self).filter()

        # Get number of steps
        n = len(self.T)

        # Check for incorrect units
        for i in range(n):

            # Units currently supported
            if self.u[i] != "U/h":

                # Give user info
                sys.exit("TB units mismatch. Exiting...")



class BolusProfile(PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BolusProfile, self).__init__()

        # Define units
        self.u = "U/h"

        # Define profile zero
        self.zero = 0

        # Define bolus delivery rate
        self.rate = 90.0

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
        super(BolusProfile, self).decouple()

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # Compute delivery time
            self.d.append(datetime.timedelta(hours = 1 / self.rate * self.y[i]))

            # Convert bolus to delivery rate
            self.y[i] = self.rate



class SuspendProfile(PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(SuspendProfile, self).__init__()

        # Define units
        self.u = "U/h"

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
        super(SuspendProfile, self).decouple()

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # If resume
            if self.y[i]:

                # Convert to none and fill later
                self.y[i] = None



class ISFProfile(FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(ISFProfile, self).__init__()

        # Define report info
        self.report = "pump.json"
        self.key = "ISF"



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.u = Reporter.getEntry(["Units"], "BG") + "/U"

        # Load rest
        super(ISFProfile, self).load()



class CSFProfile(FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(CSFProfile, self).__init__()

        # Define report info
        self.report = "pump.json"
        self.key = "CSF"



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.u = Reporter.getEntry(["Units"], "Carbs")

        # In case of grams
        if self.u == "g":

            # Adapt units
            self.u = self.u + "/U"

        # In case of exchanges
        elif self.u == "exchange":

            # Adapt units
            self.u = "U/" + self.u

        # Load rest
        super(CSFProfile, self).load()



class BGTargets(FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BGTargets, self).__init__()

        # Define report info
        self.report = "pump.json"
        self.key = "BG Targets"



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load(self.report)

        # Read units
        self.u = Reporter.getEntry(["Units"], "BG")

        # Load rest
        super(BGTargets, self).load()



class PastIOBProfile(PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastIOBProfile, self).__init__()

        # Define units
        self.u = "U"

        # Define type
        self.type = "Dot"

        # Define report info
        self.report = "treatments.json"
        self.key = "IOB"



class FutureIOBProfile(FutureProfile):

    def __init__(self, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureIOBProfile, self).__init__(past)

        # Define timestep (h)
        self.dt = 5.0 / 60.0

        # Define units
        self.u = "U"

        # Define type
        self.type = "Dot"

        # Define report info
        self.report = "treatments.json"
        self.path = ["IOB"]



    def build(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Predicting IOB..."

        # Reset previous IOB predictions
        self.reset()

        # Assign start/end limits using net insulin profile
        self.start = net.end
        self.end = net.end + datetime.timedelta(hours = IDC.DIA)

        # Compute number of steps
        n = int(IDC.DIA / self.dt) + 1

        # Generate time axis
        t = np.linspace(0, IDC.DIA, n)

        # Convert to datetime objects
        t = [datetime.timedelta(hours = x) for x in t]

        # Compute IOB decay
        for i in range(n):

            # Compute prediction time
            T = net.end + t[i]

            # Copy net insulin profile
            new = copy.copy(net)

            # Reset it
            new.reset()

            # Initialize start/end times
            new.T.append(new.start)
            new.T.append(new.end)

            # Initialize start/end values
            new.y.append(None)
            new.y.append(0)

            # Fill profile
            new.fill(net)

            # Smooth profile
            new.smooth()

            # Normalize profile
            new.normalize(T)

            # Compute IOB for current time
            IOB = self.compute(new, IDC)

            # Store prediction time
            self.T.append(T)

            # Store IOB
            self.y.append(IOB)

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Store current IOB
        self.store()

        # Show
        self.show()



    def compute(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple net insulin profile components
        t = net.t
        y = net.y

        # Initialize IOB
        IOB = 0

        # Get number of steps
        n = len(t) - 1

        # Compute IOB
        for i in range(n):

            # Compute remaining IOB factor based on integral of IDC
            r = IDC.F(t[i + 1]) - IDC.F(t[i])

            # Compute active insulin remaining for current step
            IOB += r * y[i]

        print "IOB: " + str(IOB) + " U"

        # Return IOB
        return IOB



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: only stores current IOB for later displaying purposes.
        """

        # Give user info
        print "Adding current IOB to report: '" + self.report + "'..."

        # Format time
        T = lib.formatTime(self.T[0])

        # Round value
        y = round(self.y[0], 3)

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(self.path, T, y)



class COBProfile(Profile):
    pass



class PastBGProfile(PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastBGProfile, self).__init__()

        # Initialize number of valid recent BGs
        self.n = 0

        # Define type
        self.type = "Dot"

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
        self.u = Reporter.getEntry(["Units"], "BG")

        # Load rest
        super(PastBGProfile, self).load()



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define maximum age of BGs (m)
        T = 20

        # Read number of BGs
        N = len(self.T)

        # Initialize number of recent BGs
        n = 0

        # Check age of most recent BGs
        for i in range(N):

            # They should not be older than a certain duration
            if self.T[-(i + 1)] < self.end - datetime.timedelta(minutes = T):

                # Exit
                break

            # If so, update count
            else:

                # Update
                n += 1

        # Give user info
        print "Found " + str(n) + " BGs within last " + str(T) + " m."

        # Check for insufficient data
        if n == 0:

            # Exit
            sys.exit("Not enough recent BGs to take action. Exiting...")

        # Otherwise
        else:

            # Store number of valid recent BGs
            self.n = n



    def impact(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            IMPACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Check for insufficient data
        if self.n < 2:

            # Exit
            sys.exit("Not enough recent BGs to compute BGI. Exiting...")

        # Otherwise
        else:

            # Return BGI (mean of most recent values of dBG/dt)
            return np.mean(self.dydt[-(self.n - 1):])



class FutureBGProfile(FutureProfile):

    def __init__(self, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureBGProfile, self).__init__(past)

        # Define type
        self.type = "Dot"



    def link(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LINK
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link units
        self.u = self.past.u



    def build(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Use IOB and ISF to predict where BG will land after insulin activity is
        over, assuming a natural decay.
        """

        # Give user info
        print "Decaying BG..."

        # Verify number of recent BGs
        self.past.verify()

        # Link with past profile
        self.link()

        # Reset previous BG predictions
        self.reset()

        # Assign start/end limits using net insulin profile
        self.start = IOB.start
        self.end = IOB.end

        # Get number of ISF steps
        n = len(IOB.T) - 1

        # Read latest BG
        BG = self.past.y[-1]

        # Give user info
        print ("Initial BG: " + str(BG) + " " + self.u + " " +
               "(" + lib.formatTime(self.past.T[-1]) + ")")

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n):

            # Get step limits
            a = IOB.T[i]
            b = IOB.T[i + 1]

            # Give user info
            print "Time: " + lib.formatTime(a) + " @ " + lib.formatTime(b)

            # Compute ISF
            isf = ISF.f(a)

            # Print ISF
            print "ISF: " + str(isf) + " " + ISF.u

            # Compute IOB change
            dIOB = IOB.y[i + 1] - IOB.y[i]

            # Give user info
            print "dIOB: " + str(round(dIOB, 1)) + " " + IOB.u

            # Compute BG change
            dBG = isf * dIOB

            # Give user info
            print "dBG: " + str(round(dBG, 1)) + " " + self.u

            # Add BG impact
            BG += dBG

            # Print eventual BG
            print "BG: " + str(round(BG, 1)) + " " + self.u

            # Store current BG
            self.T.append(b)
            self.y.append(BG)

            # Make some air
            print

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Show
        self.show()



    def project(self, dt):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PROJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        BG projection based on expected duration dt (h) of current BG trend
        """

        # Give user info
        print "Projection time: " + str(dt) + " h"

        # Read latest BG
        BG = self.past.y[-1]

        # Compute derivative to use when predicting future BG
        dBGdt = self.past.impact()

        # Predict future BG
        BG += dBGdt * dt

        # Return BG projection based on dBG/dt
        return BG



    def expect(self, dt, IOB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        BG expectation after a certain time dt (h) based on IOB decay
        """

        # Give user info
        print "Expectation time: " + str(dt) + " h"

        # Get number of steps corresponding to expected BG
        n = dt / IOB.dt - 1

        # Check if expectation fits with previously computed BGs
        if int(n) != n or n < 0:

            # Exit
            sys.exit("Required BG expectation does not fit on time axis of " +
                     "predicted BG profile. Exiting...")

        # Return expected BG
        return self.y[int(n)]



    def analyze(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ANALYZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Analyze and compute BG-related values.
        """

        # Give user info
        print
        print "Analyzing BG..."

        # Define prediction time (h)
        dt = 0.5

        # Compute projected BG based on latest CGM readings
        projectedBG = self.project(dt)

        # Compute BG variation due to IOB decay
        expectedBG = self.expect(dt, IOB)

        # Read BGI
        BGI = self.past.impact()

        # Compute BGI (dBG/dt) based on IOB decay
        expectedBGI = IOB.dydt[0] * ISF.y[0]

        # Compute deviation between BGs
        deltaBG = projectedBG - expectedBG

        # Compute deviation between BGIs
        deltaBGI = BGI - expectedBGI

        # Give user info (about BG)
        print "Expected BG: " + str(round(expectedBG, 1)) + " " + self.u
        print "Projected BG: " + str(round(projectedBG, 1)) + " " + self.u
        print "BG deviation: " + str(round(deltaBG, 1)) + " " + self.u

        # Give user info (about BGI)
        print ("Expected BGI: " + str(round(expectedBGI, 1)) + " " + self.u +
               "/h")
        print ("BGI: " + str(round(BGI, 1)) + " " + self.u +
               "/h")
        print ("BGI deviation: " + str(round(deltaBGI, 1)) + " " + self.u +
               "/h")
        print

        # Return computations
        return [deltaBG, BGI, expectedBGI]



    def dose(self, dBG, ISF, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute bolus to bring back BG to target using ISF and IDC.
        """

        # Initialize conversion factor between dose and BG difference to target
        f = 0

        # Get number of ISF steps
        n = len(ISF.t) - 1

        # Compute factor
        for i in range(n):

            # Compute step limits
            a = ISF.t[i] - IDC.DIA
            b = ISF.t[i + 1] - IDC.DIA

            # Update factor with current step
            f += ISF.y[i] * (IDC.f(a) - IDC.f(b))

        # Compute bolus
        bolus = dBG / f

        # Return bolus
        return bolus



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a calculator
    calculator = Calculator()

    # Get current time
    now = datetime.datetime.now()

    # Run calculator
    calculator.run(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
