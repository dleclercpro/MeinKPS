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
Logger = logger.Logger("Profiles.step")



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
        self.durations = []



    def build(self, start, end, filler = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start building
        super(StepProfile, self).build(start, end)

        # If step durations present: inject zeros between profile steps
        if self.durations:
            self.inject()

        # Cut entries outside of time limits, then ensure ends of profile fit
        self.pad(start, end, self.cut())

        # Filling required?
        if filler is not None:
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
            Inject zeros after theoretical end of steps.
        """

        # Info
        Logger.debug("Injecting zeros in: " + repr(self))

        # Initialize temporary components
        T = []
        y = []

        # Pad end of axes with infinitely far away entry in order to correctly
        # compute last step duration
        self.T += [datetime.datetime.max]
        self.y += [None]

        # Rebuild profile and inject zeros where needed
        for i in range(len(self.T) - 1):

            # Add step
            T += [self.T[i]]
            y += [self.y[i]]

            # Get current step duration
            d = self.durations[i]

            # Compute time between current and next steps
            dt = self.T[i + 1] - self.T[i]

            # Step is a canceling one: replace it with a zero (default step)
            if d == datetime.timedelta(0):
                y[-1] = self.zero

            # Step ended before next one start: inject zero in profile
            elif d < dt:
                T += [self.T[i] + d]
                y += [self.zero]

        # Update profile
        self.T, self.y = T, y



    def pad(self, a, b, last = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Force specific profile limits after profile is cut.
        """

        # Info
        Logger.debug("Padding: " + repr(self))

        # No previous step was found: use profile zero (default) value
        if last is None:
            last = self.zero

        # Start of profile: extend precedent step's value
        if len(self.T) == 0 or self.T[0] != a:
            self.T = [a] + self.T
            self.y = [last] + self.y

        # End of profile
        if self.T[-1] != b:
            self.T += [b]
            self.y += [self.y[-1]]



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Fill holes in profile y-axis (replace 'None' values with the ones
            of filler profile).
            
            Note: Only cut and padded profile can be filled! The last entry has
                  to delimit the end of the last step.
        """

        # Info
        Logger.debug("Filling: " + repr(self))

        # Initialize new profile components
        T = []
        y = []

        # Pad axes end with last entry in order to compute last step correctly
        self.T += [self.T[-1]]
        self.y += [None]

        # Fill profile
        for i in range(len(self.T)):

            # Add step time
            T += [self.T[i]]
            y += [self.y[i]]

            # Filling criteria
            if y[-1] is None:

                # Fill step value
                y[-1] = filler.f(T[-1])

                # Look for additional steps to fill
                for j in range(len(filler.T)):

                    # Filling criteria
                    if self.T[i] < filler.T[j] < self.T[i + 1]:
                        T += [filler.T[j]]
                        y += [filler.y[j]]

        # Update profile
        self.T, self.y = T, y



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Smooth profile (remove redundant steps) after it is cut and padded.
        """

        # Info
        Logger.debug("Smoothing: " + repr(self))

        # Initialize components for smoothed profile
        T = []
        y = []

        # Restore start of profile
        T += [self.T[0]]
        y += [self.y[0]]

        # Look for redundancies
        for i in range(1, len(self.T) - 1):

            # Non-redundancy criteria
            if self.y[i] != y[-1]:

                # Add step
                T += [self.T[i]]
                y += [self.y[i]]

        # Restore end of profile
        T += [self.T[-1]]
        y += [self.y[-1]]

        # Update profile
        self.T, self.y = T, y



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
            axis = self.T

        # Normalized axis
        elif lib.isRealNumber(t):
            axis = self.t

        # Otherwise
        else:
            raise TypeError("Invalid time t to compute f(t) for.")

        # Get number of steps in profile
        n = len(axis) - 1

        # Make sure axes fit
        if n != len(self.y) - 1:
            raise ArithmeticError("Cannot compute f(t): axes' lengths do not " +
                "fit.")

        # Compute profile value
        for i in range(n):

            # Index identification criteria
            if axis[i] <= t < axis[i + 1]:

                # Store index
                index = i
                break

        # Index identification criteria (end time)
        if t == axis[-1]:

            # Store index
            index = -1

        # Check if result could be found
        if index is None:
            raise ValueError("The value of f(" + lib.formatTime(t) + ") " +
                "does not exist.")

        # Return corresponding value
        return self.y[index]



    def op(self, op, profiles):

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
            new.y += [y]

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
        return self.op(lambda x, y: x + y, list(args))



    def subtract(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Subtracting:")

        # Do operation
        return self.op(lambda x, y: x - y, list(args))



    def multiply(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MULTIPLY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Multiplying:")

        # Do operation
        return self.op(lambda x, y: x * y, list(args))



    def divide(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DIVIDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Dividing:")

        # Do operation
        return self.op(lambda x, y: x / y, list(args))



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
        ax.step(self.t, self.y, where = "post", label = repr(self),
            lw = 2, ls = "-", c = color)

        # More than one line: add legend
        if len(ax.lines) > 1:
            ax.legend()

        # Ready to show?
        if show:
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