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
        #self.BG.predict(self.IDC, self.IOB, self.ISF)

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

        # Build TBR profile
        self.TBR.build(past, now, self.basal)

        # Build bolus profile
        self.bolus.build(past, now)

        # Build net profile using suspend times
        self.net.build(past, now, self.TBR.subtract(self.basal).add(self.bolus))

        # Define IDC
        self.IDC = WalshIDC(self.DIA)

        # Build IOB profile
        self.IOB.build(past, now)

        # Build COB profile
        #self.COB.build(past, now)

        # Build ISF profile (over the next DIA)
        self.ISF.build(now, future)

        # Build CSF profile (over the next DIA)
        #self.CSF.build(now, future)

        # Build BG targets profile (over the next DIA)
        self.BGTargets.build(now, future)

        # Build BG profile
        self.BG.build(past, now)



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
        n = len(self.ISF.T)

        # Initialize factor between recommended bolus and BG difference with
        # average target
        factor = 0

        # Compute factor
        for i in range(n - 1):

            # Compute ISF time ranges
            a = self.ISF.t[i] - self.IDC.DIA
            b = self.ISF.t[i + 1] - self.IDC.DIA

            # Update factor with current step
            factor += self.ISF.y[i] * (self.IDC.f(a) - self.IDC.f(b))

        # Compute eventual BG based on complete IOB decay
        naiveBG = self.BG.expect(self.IDC, self.IOB, self.ISF)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        deviationBG = self.BG.predict(self.IDC, self.IOB, self.ISF)[0]

        # Update eventual BG
        eventualBG = naiveBG + deviationBG

        # Find average of target to reach after natural insulin decay
        target = sum(self.BGTargets.y[-1]) / 2.0

        # Compute BG difference with average target
        dBG = target - eventualBG

        # Compute necessary bolus
        bolus = dBG / factor

        # Give user info
        print "Time: " + lib.formatTime(self.BGTargets.T[-1])
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
        axes[0].plot(self.BG.t, self.BG.y,
                     marker = "o", ms = 3.5, lw = 0, c = "red")

        # Add BG predictions to plot
        axes[0].plot(self.BG.t_, self.BG.y_,
                     marker = "o", ms = 3.5, lw = 0, c = "black")

        # Add net insulin profile to plot
        axes[1].step(self.net.t, np.append(0, self.net.y[:-1]),
                     lw = 2, ls = "-", c = "#ff7500")

        # Add IOB to plot
        axes[2].plot([-self.IDC.DIA, 0], [0, 0],
                     lw = 2, ls = "-", c = "purple")

        # Add IOB predictions to plot
        axes[2].plot(self.IOB.t, self.IOB.y,
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
        self.T = []

        # Initialize normalized time axis
        self.t = []

        # Initialize y-axis
        self.y = []

        # Initialize derivative
        self.dydt = []

        # Initialize step durations
        self.d = []

        # Initialize profile type
        self.type = "Step"

        # Initialize time reference
        self.norm = "End"

        # Initialize profile start
        self.start = start

        # Initialize profile end
        self.end = end

        # Initialize zero
        self.zero = None

        # Initialize data
        self.data = None

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

        # Compute profile derivative
        self.derivate()



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
        self.T = []

        # Reset normalized time axis
        self.t = []

        # Reset y-axis
        self.y = []

        # Reset derivative
        self.dydt = []

        # Reset step durations
        self.d = []

        # Reset data
        self.data = None



    def update(self, T, y, d = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Update profile components.
        """

        # Give user info
        print "Updating..."

        # Update components
        self.T = T
        self.y = y

        # If duration steps given
        if d is not None:

            # Update them
            self.d = d

        # Renormalize
        self.normalize()

        # Rederivate
        self.derivate()



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
        """

        # Give user info
        print "Decoupling components..."

        # Decouple components
        for t in sorted(self.data):

            # Get time and convert it to datetime object if possible
            self.T.append(lib.formatTime(t))

            # Get value
            self.y.append(self.data[t])

        # If time is not mapped
        if type(self.T[0]) is datetime.time:

            # Map it
            self.map()



    def map(self, now = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MAP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Mapping time..."

        # If no current time given
        if now is None:

            # Set end of profile as default
            now = self.end

        # Initialize profile components
        t = []
        y = []

        # Get number of entries
        n = len(self.T)

        # Rebuild profile
        for i in range(n):

            # Get time
            T = self.T[i]

            # Generate datetime object
            T = datetime.datetime.combine(now, T)

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
        self.update(T, y, d)



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
            self.update(T, y)

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
        """

        # Give user info
        print "Cutting..."

        # If no limits given
        if a is None and b is None:

            # Set default limits
            a = self.start
            b = self.end

            # Set extract boolean
            extract = False

        # Otherwise
        else:

            # Set extract boolean
            extract = True

        # Verify limit types
        if type(a) is not type(b):

            # Exit
            sys.exit("Type of ends do not match. Exiting...")

        # Get desired axis
        if type(a) is datetime.datetime:

            # Verify if normalization exists
            if self.T:

                # Define axis
                axis = self.T

            # Otherwise
            else:

                # Exit
                sys.exit("Cannot cut profile using normalized time limits " +
                         "when said profile was not normalized yet. Exiting...")

        else:

            # Define axis
            axis = self.t

        # Initialize cut-off profile components
        T = []
        y = []

        # Get number of steps
        n = len(axis)

        # Initialize index of last step before profile
        index = None

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Inclusion criteria
            if a <= axis[i] <= b:

                # Add time
                T.append(axis[i])

                # Add value
                y.append(self.y[i])

            # Update last step
            elif axis[i] < a:

                # Store index
                index = i

        # Ensure ends of step profile fit
        if self.type == "Step":

            # Start of profile
            if len(T) == 0 or T[0] != a:

                # Add time
                T.insert(0, a)

                # Extend last step's value
                y.insert(0, self.y[index])

            # End of profile
            if T[-1] != b:

                # Add time
                T.append(b)

                # Add rate
                y.append(y[-1])

        # Return new profile
        if extract:

            # Define new profile
            new = copy.copy(self)

            # Assign cutted axes
            new.update(T, y)

            # Return cutted profile
            return new

        # Update profile
        else:

            # Do it
            self.update(T, y)



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
        self.update(T, y)



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
            self.update(T, y)

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
                sys.exit("Time axis cannot be normalized since profile does " +
                         "not have a norm. Exiting...")

        # Before using given reference time, verify its type
        elif type(T) is not datetime.datetime:

            # Exit
            sys.exit("Time axis can only be normalized using a datetime " +
                     "object. Exiting...")

        # Reset normalization
        self.t = []

        # Get number of steps in profile
        n = len(self.T)

        # Normalize time
        for i in range(n):

            # Compare time to reference
            if self.T[i] >= T:

                # Compute positive time difference (s)
                dt = (self.T[i] - T).seconds

            else:

                # Compute negative time difference (s)
                dt = -(T - self.T[i]).seconds

            # Add step (h)
            self.t.append(dt / 3600.0)

        # Show current state of profile
        self.show()



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

        Show both profiles axes.
        """

        # Give user info
        print "Standard t-axis:"

        # Show profile
        for i in range(len(self.T)):

            # Give user info
            print str(self.y[i]) + " - (" + lib.formatTime(self.T[i]) + ")"

        # Give user info
        print "Normalized t-axis:"

        # If normalization exists
        if self.t:

            # Show profile
            for i in range(len(self.t)):

                # Give user info
                print str(self.y[i]) + " - (" + str(self.t[i]) + ")"



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
        new = Profile(self.start, self.end)

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
        n = len(self.T)

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
        n = len(self.T)

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
        n = len(self.T)

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
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # If resume
            if self.y[i]:

                # Convert to none and fill later
                self.y[i] = None



class IOBProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Initialize future components
        self.T_ = []
        self.t_ = []
        self.y_ = []
        self.dydt_ = []

        # Define type
        self.type = "Dot"

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
        t = net.t
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

        # Initialize new partial net insulin profile
        new = Profile()

        # Initialize components
        T = []
        y = []

        # Define timestep (h)
        dt = 5.0 / 60.0

        # Compute number of steps
        n = int(IDC.DIA / dt) + 1

        # Generate time axis
        axis = np.linspace(IDC.DIA, 0, n)

        # Convert time axis to datetime objects
        axis = [net.end - datetime.timedelta(hours = x) for x in axis]

        # Compute IOB decay
        for i in range(n):

            # Reset partial profile
            new.reset()

            # Set limits of partial profile (moving window)
            new.start = axis[i]
            new.end = axis[i] + datetime.timedelta(hours = IDC.DIA)

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
            new.normalize()

            # Compute IOB for current time
            IOB = self.compute(new, IDC)

            # Store prediction time
            T.append(new.end)

            # Store IOB
            y.append(IOB)

        # Update profile
        self.update(T, y)

        # Give user info
        print "Predicted IOB(s):"

        # Give user info
        for i in range(n):

            # Get current time and IOB
            t = lib.formatTime(self.T[i])
            y = self.y[i]

            # Print IOB
            print str(y) + " U (" + str(t) + ")"



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
        t = lib.formatTime(self.T[0])

        # Round value
        y = round(self.y[0], 3)

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(["IOB"], t, y)



class COBProfile(Profile):
    pass



class ISFProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define norm
        self.norm = "Start"

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



class CSFProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define norm
        self.norm = "Start"

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



class BGTargets(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__()

        # Define norm
        self.norm = "Start"

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
        self.T_ = []
        self.t_ = []
        self.y_ = []
        self.dydt_ = []

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
            if self.T[-(n + 1)] < self.end - datetime.timedelta(minutes = T):

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
            BGI = np.mean(self.dydt_[-(n - 1):])

        else:

            # Last dBG/dt
            BGI = self.dydt_[-1]

        # Return dBG/dt
        return BGI



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
        BG = self.y[-1]

        # Derivate
        self.dydt_ = lib.derivate(self.y, self.t)

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

        BG expectation after a certain time dt (h) based on IOB decay
        """

        # Give user info
        print "Expecting BG..."

        # If no prediction time is given
        if dt is None:

            # Default is DIA
            dt = IDC.DIA

        # Give user info
        print "Expectation time: " + str(dt) + " h"

        # Read latest BG
        BG = self.y[-1]

        # Give user info
        print "Initial BG: " + str(BG) + " " + self.units
        print "Initial IOB: " + str(round(IOB.y[0], 1)) + " U"

        # Define prediction limit to cut ISF profile
        a = ISF.T[0]
        b = a + datetime.timedelta(hours = dt)

        # Cut ISF profile
        isf = ISF.cut(a, b)

        # Get number of ISF steps
        n = len(isf.T)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Print timestep
            print ("Timestep: " + lib.formatTime(isf.T[i]) + " @ " +
                                  lib.formatTime(isf.T[i + 1]))

            # Print ISF
            print "ISF: " + str(isf.y[i]) + " " + isf.units

            # Adapt normalized time to fit IDC time domain
            a = isf.t[i + 1] - IDC.DIA
            b = isf.t[i] - IDC.DIA

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

        Note: why small difference between decay and predict?
        """

        # FIXME t-axes are false!

        # Give user info
        print "Decaying BG..."

        # Read latest BG
        BG = self.y[-1]

        # Give user info
        print "Initial BG: " + str(BG)

        # Get number of ISF steps
        n = len(IOB.T)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Give user info
            print ("Time: " + lib.formatTime(IOB.T[i]) + " @ " +
                              lib.formatTime(IOB.T[i + 1]))

            # Assign times
            self.T_.append(IOB.T[i + 1])
            self.t_.append(IOB.t[i + 1])

            # Compute ISF
            isf = ISF.f(IOB.T[i])

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



    def predict(self, IDC, IOB, ISF, dt = 0.5):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREDICT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: prediction time should be set to 0.5 h
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

        # Return deviations
        return [deviationBG, deviationBGI]



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
