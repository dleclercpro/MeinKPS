#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    base

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import numpy as np
import datetime



# USER LIBRARIES
import lib
import errors
import reporter



# Instanciate a reporter
Reporter = reporter.Reporter()



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

        # Initialize dating
        self.dated = False

        # Initialize report info
        self.report = None
        self.branch = []

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

        # If dated
        if self.dated:

            # Define loading function
            load = Reporter.getLatest

        # Otherwise
        else:

            # Define loading function
            load = Reporter.get

        # Load data
        self.data = load(self.report, self.branch)

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

        # If future profile
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

        # Initialize current index (handle between 23:00 and 00:00 of
        # following day)
        index = n - 1

        # Find current time
        for i in range(n - 1):

            # Current time criteria
            if T[i] <= now < T[(i + 1)]:

                # Store index
                index = i

                # Exit
                break

        # Update time
        for i in range(n):

            # Find times in future and bring them in the past
            if self.norm == "End" and i > index:

                # Update time
                T[i] -= datetime.timedelta(days = 1)

            # Find times in past and bring them in the future
            elif self.norm == "Start" and i < index:

                # Update time
                T[i] += datetime.timedelta(days = 1)

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

        # If last step was found
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
                if d == datetime.timedelta(0):

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



    def pad(self, a, b, last = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Force specific profile limits.
        """

        # Only step profiles can be padded
        if self.type == "Step":

            # Give user info
            print "Padding..."

            # Start of profile
            if len(self.T) == 0 or self.T[0] != a:

                # Add time
                self.T.insert(0, a)

                # If precedent step was found
                if last is not None:

                    # Extend precedent step's value
                    self.y.insert(0, last)

                # Otherwise
                else:

                    # Add zero value
                    self.y.insert(0, self.zero)

            # End of profile
            if self.T[-1] != b:

                # Add time
                self.T.append(b)

                # Add rate
                self.y.append(self.y[-1])



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
            raise errors.ProfileEndsTypeMismatch(type(a), type(b))

        # Get desired axis
        if type(a) is not datetime.datetime:

            # Exit
            raise errors.NoNormalizedCut()

        # Initialize cut-off profile components
        T = []
        y = []

        # Initialize index of last step before profile
        index = None

        # Get number of steps
        n = len(self.T)

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

        # If last step
        if index is not None:

            # Define it
            last = self.y[index]

        # Otherwise
        else:

            # Define it
            last = None

        # Update profile
        self.T = T
        self.y = y

        # Ensure ends of step profile fit
        self.pad(a, b, last)



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
                    raise errors.NoNorm()

            # Before using given reference time, verify its type
            elif type(T) is not datetime.datetime:

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
                        y = round(y, 2)

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
            raise errors.ProfileAxesLengthMismatch()

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
                raise errors.ProfileLimitsMismatch(profile, base)



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