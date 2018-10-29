#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    base

    Author:   David Leclerc

    Version:  0.2

    Date:     31.08.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import copy
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger
import errors
import reporter



# Define instances
Logger = logger.Logger("Profiles/base.py", "DEBUG")
Reporter = reporter.Reporter()



class Profile(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize zero (default value)
        self.zero = None

        # Initialize units
        self.units = None

        # Initialize report info
        self.report = None
        self.branch = []



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Reset profile data.
        """

        # Give user info
        Logger.debug("Resetting...")

        # Reset time axis
        self.T = []

        # Reset normalized time axis
        self.t = []

        # Reset y-axis
        self.y = []

        # Reset derivative
        self.dydt = []

        # Reset start/end times
        self.start = None
        self.end = None

        # Reset time norm
        self.norm = None

        # Reset range of days covered
        self.days = []

        # Reset plot limits
        self.xlim = []
        self.ylim = []

        # Reset loaded data
        self.data = {}



    def build(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Building '" + self.__class__.__name__ + "'...")

        # Reset profile
        self.reset()

        # Define time references
        self.define(start, end)

        # Load data
        self.load()

        # Decouple profile components
        self.decouple()



    def define(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Based on profile type, define its time references.
        """

        # Give user info
        Logger.debug("Defining time references...")

        # Define start/end times
        self.start = start
        self.end = end

        # First day to cover for always one before start date
        day = start.date() - datetime.timedelta(days = 1)

        # Fill them until end date is reached
        while day <= end.date():

            # Add day
            self.days.append(day)

            # Update it
            day += datetime.timedelta(days = 1)



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Load profile data.
        """

        # N/A for abstract profile class
        pass



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decouple profile data into components.
        """

        # Give user info
        Logger.debug("Decoupling components...")

        # Decouple components
        for t in sorted(self.data):

            # Get time and convert it to datetime object if possible
            self.T.append(lib.formatTime(t))

            # Get value
            self.y.append(self.data[t])



    def cut(self, a = None, b = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Cut remaining excess entries in profile.
        """

        # Give user info
        Logger.debug("Cutting...")

        # If no start given
        if a is None:

            # Set default start limit
            a = self.start

        # If no end given
        if b is None:

            # Set default end limit
            b = self.end

        # Initialize cut-off profile components
        T = []
        y = []

        # Initialize last step value before beginning of profile
        last = None

        # Get number of steps
        n = len(self.T)

        # Cut-off steps outside of start and end limits
        for i in range(n):

            # Update last step
            if self.T[i] < a:

                # Store last value
                last = self.y[i]

            # Inclusion criteria
            elif a <= self.T[i] <= b:

                # Add time
                T.append(self.T[i])

                # Add value
                y.append(self.y[i])

        # Update profile
        self.T = T
        self.y = y

        # Return core infos
        return [a, b, last]



    def normalize(self, T = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Normalize profile's time axis.
        """

        # Give user info
        Logger.debug("Normalizing...")

        # Verify if norm was left empty
        if T is None:

            # Get time reference
            T = self.norm

            # If no time reference
            if T is None:

                # Exit
                raise errors.NoNorm()

        # Before using given reference time, verify its type
        if type(T) is not datetime.datetime:

            # Exit
            raise errors.BadTypeNormalization()

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



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Show profile components.
        """

        # Define profile dictionary
        profiles = {"Standard t-axis": [self.T, self.y],
                    "Normalized t-axis": [self.t, self.y],
                    "Derivative": [self.t[:-1], self.dydt]}

        # Loop on each profile component
        for p in profiles:

            # Get axes
            axes = profiles[p]

            # Read number of entries
            nx = len(axes[0])
            ny = len(axes[1])

            # If profile exists
            if nx > 0 and nx == ny:

                # Give user info
                Logger.debug(p)

                # Show profile
                for i in range(nx):

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
                        y = round(y, 2)

                    # Give user info
                    Logger.debug(str(y) + " - (" + str(t) + ")")



    def plot(self, n, size, title = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define subplot
        ax = plt.subplot(size[0], size[1], n)

        # Define title
        title = title or self.__class__.__name__

        # Define axis labels
        x = "(h)"
        y = "(" + self.units + ")"

        # Set title
        ax.set_title(title, fontweight = "semibold")

        # Set axis labels
        ax.set_xlabel(x)
        ax.set_ylabel(y)

        # If x-axis limits defined
        if self.xlim:

            # Set x-axis limit
            ax.set_xlim(min(ax.get_xlim()[0], self.xlim[0]),
                        max(ax.get_xlim()[1], self.xlim[1]))

        # If y-axis limits defined
        if self.ylim:

            # Set y-axis limit
            ax.set_ylim([min(ax.get_ylim()[0], self.ylim[0]),
                         max(ax.get_ylim()[1], self.ylim[1])])

        # Return figure and subplot
        return ax



class StepProfile(Profile):

    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start resetting
        super(StepProfile, self).reset()

        # Reset step durations
        self.d = []



    def build(self, start, end, filler = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start building
        super(StepProfile, self).build(start, end)

        # If step durations present
        if self.d:

            # Inject zeros between profile steps
            self.inject()

        # Cut entries outside of time limits
        self.cut()

        # Filling required?
        if filler is not None:

            # Fill profile
            self.fill(filler)

        # Smooth profile
        self.smooth()

        # Normalize profile
        self.normalize()

        # Show profile
        self.show()



    def inject(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Inject zeros after theoretical end of steps. Will only work if step
            durations are defined!
        """

        # Give user info
        Logger.debug("Injecting...")

        # Initialize temporary components
        T = []
        y = []

        # Get number of steps
        n = len(self.T)

        # Pad end of axes with infinitely far away entry in order to correctly
        # compute last step duration
        self.T.append(datetime.datetime.max)
        self.y.append(None)

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
            if d == datetime.timedelta(0):

                # Replace value with zero (default) value
                y[-1] = self.zero

            # Inject zero in profile
            elif d < dt:

                # Add zero
                T.append(self.T[i] + d)
                y.append(self.zero)

        # Update profile
        self.T = T
        self.y = y



    def cut(self, a = None, b = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Cut remaining excess entries in profile and ensure the latter starts
            and ends according to the previously defined limit times.
        """

        # Cut profile
        [start, end, last] = super(StepProfile, self).cut(a, b)

        # Ensure ends of profile fit
        self.pad(start, end, last)



    def pad(self, a, b, last):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Force specific profile limits after profile is cut.
        """

        # Give user info
        Logger.debug("Padding...")

        # If no previous step was found
        if last is None:

            # Use profile zero (default) value
            last = self.zero

        # Start of profile
        if len(self.T) == 0 or self.T[0] != a:

            # Add time
            self.T.insert(0, a)
            
            # Extend precedent step's value
            self.y.insert(0, last)

        # End of profile
        if self.T[-1] != b:

            # Add time
            self.T.append(b)

            # Add rate
            self.y.append(self.y[-1])



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: Only cut and padded profile can be filled! The last entry has
                  to delimit the end of the last step.
        """

        # Give user info
        Logger.debug("Filling...")

        # Initialize new profile components
        T = []
        y = []

        # Get number of steps within profile
        m = len(self.T)

        # Get number of steps within filler
        n = len(filler.T)

        # Pad axes end with last entry in order to compute last step correctly
        self.T.append(self.T[-1])
        self.y.append(None)

        # Fill profile
        for i in range(m):

            # Add step time
            T.append(self.T[i])

            # Filling criteria
            if self.y[i] is None:

                # Fill step value
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

                # Add step value
                y.append(self.y[i])

        # Update profile
        self.T = T
        self.y = y



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Smooth profile (remove redundant steps) after it is cut and padded.
        """

        # Give user info
        Logger.debug("Smoothing...")

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
            if self.y[i] != y[-1]:

                # Add step
                T.append(self.T[i])
                y.append(self.y[i])

        # Restore end of profile
        T.append(self.T[-1])
        y.append(self.y[-1])

        # Update profile
        self.T = T
        self.y = y



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Compute profile's value (y) for a given time (t).
        """

        # Initialize index
        index = None

        # Datetime axis
        if type(t) is datetime.datetime:

            # Define axis
            axis = self.T

        # Normalized axis
        else:

            # Define axis
            axis = self.t

        # Get number of steps in profile
        n = len(axis) - 1

        # Make sure axes fit
        if n != len(self.y) - 1:

            # Exit
            raise errors.ProfileAxesLengthMismatch()

        # Compute profile value
        for i in range(n):

            # Index identification criteria
            if axis[i] <= t < axis[i + 1]:

                # Store index
                index = i

                # Exit
                break

        # Index identification criteria (end time)
        if t == axis[-1]:

            # Store index
            index = -1

        # Check if result could be found
        if index is None:

            # Error
            raise errors.BadFunctionCall(lib.formatTime(t))

        # Compute corresponding value
        y = self.y[index]

        # Return result
        return y



    def operate(self, op, profiles):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            OPERATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: Profiles on which operations are made cannot have "None"
                  values within them!
        """

        # Copy profile on which operation is done
        new = copy.deepcopy(self)

        # Reset its components
        new.reset()

        # Re-define time references
        new.define(self.start, self.end)

        # Merge all steps
        new.T = lib.uniqify(self.T + lib.flatten([p.T for p in profiles]))

        # Compute each step of new profile
        for T in new.T:

            # Compute partial result with base profile
            y = self.f(T)

            # Look within each profile
            for p in profiles:

                # Compute partial result on current profile
                y = op(y, p.f(T))

            # Store result for current step
            new.y.append(y)

        # Get min/max values
        [new.min, new.max] = [min(new.y), max(new.y)]

        # Normalize it
        new.normalize()

        # Return new profile
        return new



    def add(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Adding:")

        # Do operation
        return self.operate(lambda x, y: x + y, list(args))



    def subtract(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Subtracting:")

        # Do operation
        return self.operate(lambda x, y: x - y, list(args))



    def multiply(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MULTIPLY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Multiplying:")

        # Do operation
        return self.operate(lambda x, y: x * y, list(args))



    def divide(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DIVIDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Dividing:")

        # Do operation
        return self.operate(lambda x, y: x / y, list(args))



    def plot(self, n = 1, size = [1, 1], show = True, title = None,
                   color = "black"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start plotting
        ax = super(StepProfile, self).plot(n, size, title)

        # Add data to plot
        ax.step(self.t, self.y, where = "post", label = self.__class__.__name__,
                lw = 2, ls = "-", c = color)

        # More than one line
        if len(ax.lines) > 1:

            # Add legend
            ax.legend()

        # Ready to show?
        if show:

            # Show plot
            plt.show()



class DotProfile(Profile):

    def build(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start building
        super(DotProfile, self).build(start, end)

        # Cut entries outside of time limits
        self.cut()

        # Normalize profile
        self.normalize()

        # Compute profile derivative
        self.derivate()

        # Show profile
        self.show()



    def derivate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DERIVATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Derivate dot typed profiles using their normalized time axis.
        """

        # Give user info
        Logger.debug("Derivating...")

        # Derivate
        self.dydt = lib.derivate(self.y, self.t)



    def plot(self, n = 1, size = [1, 1], show = True, title = None,
                   color = "black"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start plotting
        ax = super(DotProfile, self).plot(n, size, title)

        # Add data to plot
        ax.plot(self.t, self.y, label = self.__class__.__name__,
                marker = "o", ms = 3.5, lw = 0, c = color)

        # More than one line
        if len(ax.lines) > 1:
            
            # Add legend
            ax.legend()

        # Ready to show?
        if show:

            # Show plot
            plt.show()



class PastProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initializing
        super(PastProfile, self).__init__()

        # Define whether data should strictly be loaded within given time range
        # or try and find the latest available
        self.strict = True



    def define(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define profile time references.
        """

        # Start defining
        super(PastProfile, self).define(start, end)

        # Compute dT
        dT = end - start

        # Define norm
        self.norm = end

        # Define plot x-axis default limits
        self.xlim = [lib.normalizeTime(t, end) for t in [end - dT, end + dT]]



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Load profile components from specified report(s).
        """

        # Give user info
        Logger.debug("Loading...")

        # If strictly looking for dates within range of profile
        if self.strict:

            # Get corresponding reports
            for day in self.days:

                # Try getting data
                try:

                    # Get current data
                    data = Reporter.get(self.report, self.branch, None, day)

                    # Load data
                    self.data = lib.mergeDicts(self.data, data)

                # Otherwise
                except:

                    # Skip
                    pass

        # If looking for last stored data
        else:

            # Load data
            self.data = Reporter.getRecent(self.norm, self.report, self.branch)

        # Give user info
        Logger.debug("Loaded " + str(len(self.data)) + " data point(s).")



class FutureProfile(Profile):

    def define(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define profile time references.
        """

        # Start defining
        super(FutureProfile, self).define(start, end)

        # Compute dT
        dT = end - start
        
        # Define norm
        self.norm = start

        # Define plot x-axis default limits
        self.xlim = [lib.normalizeTime(t, start) for t in [start - dT,
                                                           start + dT]]



class DailyProfile(StepProfile):

    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Loading...")

        # Load data
        self.data = Reporter.get(self.report, self.branch)

        # Give user info
        Logger.debug("Loaded " + str(len(self.data)) + " data point(s).")



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decouple profile components.
        """

        # Start decoupling
        super(DailyProfile, self).decouple()

        # Map time
        self.map()



    def map(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MAP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Mapping time...")

        # Initialize profile components
        T = []
        y = []

        # Get number of entries
        n = len(self.T)

        # Loop on range of days covered by profile
        for day in self.days:

            # Rebuild profile
            for i in range(n):

                # Add time
                T.append(datetime.datetime.combine(day, self.T[i]))

                # Add value
                y.append(self.y[i])

        # Zip and sort profile
        z = sorted(zip(T, y))

        # Update profile
        self.T = [x for x, y in z]
        self.y = [y for x, y in z]



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Get older time
    then = now - datetime.timedelta(days = 1)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()