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
import matplotlib as mpl
import matplotlib.pyplot as plt
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

        # Give calculator an IOB profile
        self.IOB = IOBProfile()

        # Give calculator a COB profile
        self.COB = COBProfile()

        # Give calculator an ISF profile
        self.ISF = ISFProfile()

        # Give calculator a CSF profile
        self.CSF = CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets()

        # Give calculator a BG profile
        self.BG = BGProfile()

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
        self.IOB.predict(self.net, self.IDC)

        # Store IOB
        #self.IOB.store()

        # Compute BG
        #self.BG.decay(self.IOB, self.ISF)
        #self.BG.expect(self.IDC, self.IOB, self.ISF)
        self.BG.predict(self.IDC, self.IOB, self.ISF)

        # Recommend action
        self.recommend()

        # Show infos
        self.show()



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
        self.basal.build(start, end)

        # Build TBR profile
        self.TBR.build(start, end, self.basal)

        # Build bolus profile
        self.bolus.build(start, end)

        # Build net profile using suspend times
        self.net.build(start, end, self.TBR.subtract(self.basal)
                                           .add(self.bolus))

        # Build IOB profile
        self.IOB.build(start, end)

        # Build COB profile
        #self.COB.build(start, end)

        # Build ISF profile (over the next DIA)
        self.ISF.build(end, future)

        # Build CSF profile (over the next DIA)
        #self.CSF.build(end, future)

        # Build BG targets profile (over the next DIA)
        self.BGTargets.build(end, future)

        # Build BG profile
        self.BG.build(start, end)



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

        # Get number of ISF steps
        n = len(self.ISF.t)

        # Initialize factor between recommended bolus and BG difference with
        # average target
        factor = 0

        # Compute factor
        for i in range(n - 1):

            # Compute ISF time ranges
            a = self.ISF.T[i] - self.IDC.DIA
            b = self.ISF.T[i + 1] - self.IDC.DIA

            # Update factor with current step
            factor += self.ISF.y[i] * (self.IDC.f(a) - self.IDC.f(b))

        # Compute eventual BG based on complete IOB decay
        naiveBG = self.BG.expect(self.IDC, self.IOB, self.ISF)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        deviationBG = (self.BG.project() -
                       self.BG.expect(self.IDC, self.IOB, self.ISF, 0.5))

        # Update eventual BG
        eventualBG = naiveBG + deviationBG

        # Find average of target to reach after natural insulin decay
        target = sum(self.BGTargets.y[-1]) / 2.0

        # Compute BG difference with average target
        dBG = target - eventualBG

        # Compute necessary bolus
        bolus = dBG / factor

        # Give user info
        print "Time: " + lib.formatTime(self.BGTargets.t[-1])
        print "BG target: " + str(self.BGTargets.y[-1]) + " " + self.BG.units
        print "BG target average: " + str(target) + " " + self.BG.units
        print "BG: " + str(round(self.BG.y[-1], 1)) + " " + self.BG.units
        print "Naive eventual BG: " + str(round(naiveBG, 1)) + " " + self.BG.units
        print "Eventual BG: " + str(round(eventualBG, 1)) + " " + self.BG.units
        print "dBG: " + str(round(dBG, 1)) + " " + self.BG.units
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
            # TB (m)
            maxT = 30

            # Give user info
            print "Max basal: " + str(self.max["Basal"]) + " U/h"
            print "3x max daily basal: " + str(3 * max(self.ISF.y)) + " U/h"
            print "4x current basal: " + str(4 * self.ISF.y[0]) + " U/h"
            print "Resulting max basal: " + str(maxTB) + " U/h"
            print "Time required with resulting max basal: " + str(T) + " m"
            print "Max time to enact recommendation: " + str(maxT) + " m"

            # Decide if external action is required
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

            # Give user info
            # TODO: compute how much time to cut basal
            print "Low TBR to enact..."



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize plot
        mpl.rc("font", size = 10, family = "Ubuntu")
        fig = plt.figure(0, figsize = (10, 8))
        axes = [plt.subplot(221), plt.subplot(222),
                plt.subplot(223), plt.subplot(224)]

        # Define titles
        titles = ["BG", "Net Insulin Profile", "IOB", "COB"]

        # Define axis labels
        x = ["(h)"] * 4
        y = ["(" + self.BG.units + ")",
             "(U/h)",
             "(U)",
             "(g)"]

        # Define axis limits
        xlim = [[-self.IDC.DIA, self.IDC.DIA]] * 4
        ylim = [[2, 20], None, None, None]

        # Define subplots
        for i in range(4):

            # Set titles
            axes[i].set_title(titles[i], fontweight = "semibold")

            # Set x-axis labels
            axes[i].set_xlabel(x[i])

            # Set y-axis labels
            axes[i].set_ylabel(y[i])

            # Set x-axis limits
            #axes[i].set_xlim(xlim[i])

        # Set y-axis limits
        axes[0].set_ylim(ylim[0])

        # Add BGs to plot
        axes[0].plot(self.BG.T, self.BG.y,
                     marker = "o", ms = 3.5, lw = 0, c = "red")

        # Add BG predictions to plot
        axes[0].plot(self.BG.T_, self.BG.y_,
                     marker = "o", ms = 3.5, lw = 0, c = "black")

        # Add net insulin profile to plot
        axes[1].step(self.net.T, np.append(0, self.net.y[:-1]),
                     lw = 2, ls = "-", c = "#ff7500")

        # Add IOB to plot
        axes[2].plot([-self.IDC.DIA, 0], [0, 0],
                     lw = 2, ls = "-", c = "purple")

        # Add IOB predictions to plot
        axes[2].plot(self.IOB.T, self.IOB.y,
                     lw = 2, ls = "-", c = "black")

        # Add COB to plot
        axes[3].plot([-self.IDC.DIA, 0], [0, 0],
                     lw = 2, ls = "-", c = "#99e500")

        # Add COB predictions to plot
        axes[3].plot([0, self.IDC.DIA], [0, 0],
                     lw = 2, ls = "-", c = "black")

        # Tighten up
        plt.tight_layout()

        # Show plot
        plt.show()



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

        # Initialize derivate
        self.dydt = []

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

        # Reset profile
        self.reset()

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



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Reset profile components.
        """

        # Give user info
        print "Resetting..."

        # Reset time axis
        self.t = []

        # Reset normalized time axis
        self.T = []

        # Reset y-axis
        self.y = []

        # Reset derivate
        self.dydt = []

        # Reset step durations
        self.d = []

        # Reset data
        self.data = None



    def update(self, t, y, d = []):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Update profile components.
        """

        # Give user info
        print "Updating..."

        # Update components
        self.t = t
        self.y = y
        self.d = d

        # If normalization exists
        if self.T:

            # Renormalize
            self.normalize()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Load profile from specified report.
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
        """

        # Give user info
        print "Decoupling components..."

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

        # If step durations are set
        if self.d:

            # Give user info
            print "Injecting..."

            # Initialize temporary components
            t = []
            y = []

            # Get number of steps
            n = len(self.t)

            # Add end to time axis in order to correctly compute last dt (number
            # of steps has to be computed before that!)
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

        # No step durations
        else:

            # Give user info
            print "No step durations available."



    def cut(self, a = None, b = None, normalized = False, extract = False):

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

        # Set limits
        if not a and not b:

            # Default
            a = self.start
            b = self.end

        # Get desired axis
        if normalized:

            # Define axis
            axis = self.T

        else:

            # Define axis
            axis = self.t

        # Get number of steps
        n = len(axis)

        # Initialize index of last step before profile
        index = None

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Inclusion criteria
            if a <= axis[i] <= b:

                # Add time
                t.append(axis[i])

                # Add value
                y.append(self.y[i])

            # Update last step
            elif axis[i] < a:

                # Store index
                index = i

        # Ensure ends of step profile fit
        if self.type == "Step":

            # Start of profile
            if len(t) == 0 or t[0] != a:

                # Add time
                t.insert(0, a)

                # Extend last step's value
                y.insert(0, self.y[index])

            # End of profile
            if t[-1] != b:

                # Add time
                t.append(b)

                # Add rate
                y.append(y[-1])

        # Update profile
        if not extract:

            # Do it
            self.update(t, y)

        # Return new profile
        else:

            # Define new profile
            # FIXME shallow copy?
            new = copy.copy(self)

            # Assign cutted axes
            new.update(t, y)

            # Return cutted profile
            return new



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

        # If step profile
        if self.type == "Step":

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

        # Dot profiles
        else:

            # Give user info
            print "Only step profiles can be smoothed."



    def normalize(self, T = "End"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Normalize profile's time axis (in hours).
        """

        # Give user info
        print "Normalizing..."

        # Reset normalization
        self.T = []

        # Decide which reference time to use for normalization
        if T == "End":

            # From end
            T = self.end

        elif T == "Start":

            # From start
            T = self.start

        # Get number of steps in profile
        n = len(self.t)

        # Normalize time
        for i in range(n):

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
        self.show()



    def derivate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DERIVATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Derivate dot typed profiles using their normalized time axis.
        """

        # FIXME use me?

        # Check if profile is differentiable
        if self.type == "Dot" and self.T:

            # Give user info
            print "Derivating..."

            # Derivate
            self.dydt = lib.derivate(self.y, self.T)

        # Otherwise
        else:

            # Exit
            sys.exit("Only normalized dot typed profile can be derivated.")



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Show both profiles axes.
        """

        # Show profile
        for i in range(len(self.t)):

            # Give user info
            print str(self.y[i]) + " - (" + lib.formatTime(self.t[i]) + ")"

        # Make some space to read
        print

        # If normalization exists
        if self.T:

            # Show profile
            for i in range(len(self.T)):

                # Give user info
                print str(self.y[i]) + " - (" + str(self.T[i]) + ")"



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



class IOBProfile(Profile):

    # TODO: load previous IOBs and do not store prediction(s)?

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

        # Define units
        self.units = "U"

        # Define report info
        self.report = "treatments.json"
        self.path = []
        self.key = "IOB"



    def compute(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple net insulin profile components
        t = net.T
        y = net.y

        # Initialize current IOB
        IOB = 0

        # Get number of steps
        n = len(t)

        # Compute IOB
        for i in range(n - 1):

            # Compute remaining IOB factor based on integral of IDC
            r = IDC.F(t[i + 1]) - IDC.F(t[i])

            # Compute active insulin remaining for current step
            IOB += r * y[i]

        print "IOB: " + str(IOB)

        # Return IOB
        return IOB



    def predict(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Predicting IOB..."

        # Reset values
        self.reset()

        # Get current time
        now = net.end

        # Define start/end of IOB prediction profile
        self.start = now
        self.end = now + datetime.timedelta(hours = IDC.DIA)

        # Initialize partial net insulin profile
        part = Profile()

        # Define timestep (h)
        dt = 1.0 / 60.0

        # Compute number of steps
        n = int(IDC.DIA / dt) + 1

        # Generate time axis
        t = np.linspace(IDC.DIA, 0, n)

        # Convert time axis to datetime objects
        t = [now - datetime.timedelta(hours = x) for x in t]

        # Compute IOB decay
        for i in range(n):

            # Reset partial profile
            part.reset()

            # Set limits of partial profile (moving window)
            part.start = t[i]
            part.end = t[i] + datetime.timedelta(hours = IDC.DIA)

            # Initialize start/end times
            part.t.append(part.start)
            part.t.append(part.end)

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
            IOB = self.compute(part, IDC)

            # Compute IOB prediction time
            T = t[i] + datetime.timedelta(hours = IDC.DIA)

            # Store prediction time
            self.t.append(T)

            # Store IOB
            self.y.append(IOB)

        # Normalize time axis
        self.normalize()

        # Derivate
        self.dydt = lib.derivate(self.y, self.T)

        # Give user info
        print "Predicted IOB(s):"

        # Give user info
        for i in range(n):

            # Get current time and IOB
            t = lib.formatTime(self.t[i])
            y = self.y[i]

            # Print IOB
            print str(y) + " U (" + str(t) + ")"



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



class COBProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize DCA
        self.DCA = None



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
        super(self.__class__, self).normalize("Start")



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
        super(self.__class__, self).normalize("Start")



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
        super(self.__class__, self).normalize("Start")



class BGProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Initialize future components
        self.t_ = []
        self.T_ = []
        self.y_ = []

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



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define minimum number of BGs required
        N = 2

        # Define maximum age of BGs (m)
        T = 20

        # Initialize number of valid BGs
        n = 0

        # Check age of most recent BGs
        while True:

            # They should not be older than a certain duration
            if self.t[-(n + 1)] < self.end - datetime.timedelta(minutes = T):

                # Exit
                break

            # Update number of BGs
            n += 1

        # Check for insufficient data
        if n < N:

            # Exit
            sys.exit("Not enough valid BGs to take action. Exiting...")

        # Return number of valid BGs
        return n



    def impact(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            IMPACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify and get number of valid BGs for analysis
        n = self.verify()

        # Compute most relevant BG derivative
        if n > 2:

            # Average dBG/dt
            dBGdt = np.mean(self.dydt[-(n - 1):])

        else:

            # Last dBG/dt
            dBGdt = self.dydt[-1]

        # Return dBG/dt
        return dBGdt



    def project(self, dt = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PROJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        BG projection based on expected duration dt (h) of current BG trend
        """

        # If no projection time is given
        if not dt:

            # Default is 30 m
            dt = 0.5

        # Give user info
        print "Projection time: " + str(dt) + " h"

        # Read latest BG
        BG = self.y[-1]

        # Derivate
        self.dydt = lib.derivate(self.y, self.T)

        # Compute derivative to use when predicting future BG
        dBGdt = self.impact()

        # Predict future BG
        BG += dBGdt * dt

        # Return BG projection based on dBG/dt
        return BG



    def expect(self, IDC, IOB, ISF, dt = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        BG expectation based on IOB decay
        """

        # Give user info
        print "Expecting BG..."

        # Read latest BG
        BG = self.y[-1]

        # Give user info
        print "Initial BG: " + str(BG) + " " + self.units
        print "Initial IOB: " + str(round(IOB.y[0], 1)) + " U"

        # If no prediction time is given
        if not dt:

            # Default is DIA
            dt = IDC.DIA

        # Give user info
        print "Expectation time: " + str(dt) + " h"

        # Define prediction limit to cut ISF profile
        a = ISF.t[0]
        b = a + datetime.timedelta(hours = dt)

        # Cut ISF profile
        isf = ISF.cut(a, b, False, True)

        # Get number of ISF steps
        n = len(isf.t)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Print timestep
            print ("Timestep: " + lib.formatTime(isf.t[i]) + " @ " +
                                  lib.formatTime(isf.t[i + 1]))

            # Print ISF
            print "ISF: " + str(isf.y[i]) + " " + isf.units

            # Adapt normalized time to fit IDC time domain
            a = isf.T[i + 1] - IDC.DIA
            b = isf.T[i] - IDC.DIA

            # Compute IOB change
            dIOB = IOB.y[0] * (IDC.f(b) - IDC.f(a))

            # Give user info
            print "dIOB: " + str(round(dIOB, 1)) + " U"

            # Compute BG change
            dBG = isf.y[i] * dIOB

            # Give user info
            print "dBG: " + str(round(dBG, 1)) + " " + self.units

            # Add BG impact
            BG += dBG

            # Print eventual BG
            print "BG: " + str(round(BG, 1)) + " " + self.units

        # Make some air
        print

        # Return expected BG
        return BG



    def decay(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECAY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        Use IOB and ISF to predict where BG will land after insulin activity is
        over, assuming a natural decay.
        """

        # FIXME: why small difference between decay and predict?

        # Give user info
        print "Decaying BG..."

        # Read latest BG
        BG = self.y[-1]

        # Give user info
        print "Initial BG: " + str(BG)

        # Get number of ISF steps
        n = len(IOB.t)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Give user info
            print ("Time: " + lib.formatTime(IOB.t[i]) + " @ " +
                              lib.formatTime(IOB.t[i + 1]))

            # Assign times
            self.t_.append(IOB.t[i + 1])
            self.T_.append(IOB.T[i + 1])

            # Compute ISF
            isf = ISF.f(IOB.t[i], False)

            # Print ISF
            print "ISF: " + str(isf) + " " + ISF.units

            # Compute IOB change
            dIOB = IOB.y[i + 1] - IOB.y[i]

            # Give user info
            print "dIOB: " + str(dIOB) + " " + IOB.units

            # Compute BG change
            dBG = isf * dIOB

            # Give user info
            print "dBG: " + str(dBG) + " " + self.units

            # Add BG impact
            BG += dBG

            # Print eventual BG
            print "BG: " + str(round(BG, 1)) + " " + self.units

            # Store current BG
            self.y_.append(BG)

            # Make some air
            print

        # Give user info
        print "Eventual BG: " + str(round(BG, 1)) + " " + self.units



    def predict(self, IDC, IOB, ISF, dt = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Predicting BG..."

        # Compute projected BG based on latest CGM readings
        projectedBG = self.project(dt)

        # Compute BG variation due to IOB decay
        expectedBG = self.expect(IDC, IOB, ISF, dt)

        # Read BGI
        BGI = self.impact()

        # Compute BGI (dBG/dt) based on IOB decay
        expectedBGI = IOB.dydt[0] * ISF.y[0]

        # Compute deviation between BGs
        deviationBG = projectedBG - expectedBG

        # Compute deviation between BGIs
        deviationBGI = BGI - expectedBGI

        # Give user info (about BG)
        print "Expected BG: " + str(round(expectedBG, 1)) + " " + self.units
        print "Projected BG: " + str(round(projectedBG, 1)) + " " + self.units
        print "BG deviation: " + str(round(deviationBG, 1)) + " " + self.units

        # Make some air
        print

        # Give user info (about BGI)
        print ("Expected BGI: " + str(round(expectedBGI, 1)) + " " +
               self.units + "/h")
        print ("BGI: " + str(round(BGI, 1)) + " " +
               self.units + "/h")
        print ("BGI deviation: " + str(round(deviationBGI, 1)) + " " +
               self.units + "/h")



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
