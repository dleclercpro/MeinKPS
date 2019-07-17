#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    step

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
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger
from .profile import Profile



# Define instances
Logger = logger.Logger("Profiles/step.py")



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

        # Info
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

        # Info
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

        # Info
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

        # Info
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
            raise IOError("Cannot compute f(t): axes' length do not fit.")

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
            raise ValueError("The value of f(" + lib.formatTime(t) + ") " +
                "does not exist.")

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

        # Info
        Logger.debug("Adding:")

        # Do operation
        return self.operate(lambda x, y: x + y, list(args))



    def subtract(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Subtracting:")

        # Do operation
        return self.operate(lambda x, y: x - y, list(args))



    def multiply(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MULTIPLY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Multiplying:")

        # Do operation
        return self.operate(lambda x, y: x * y, list(args))



    def divide(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DIVIDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
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



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()