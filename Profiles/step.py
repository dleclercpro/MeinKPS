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
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger
import errors
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

        # If step durations exist: inject zeros between steps
        if self.durations:
            self.inject()

        # Cut entries outside of time limits, and enforce start/end of profile
        self.pad(self.cut())

        # Fill profile if needed
        if filler is not None:
            self.fill(filler)

        # Smooth profile
        self.smooth()

        # Normalize profile
        self.normalize()



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
        T, y = [], []

        # Pad end of time axis with infinitely far away datetime, in order to
        # correctly allow last step duration
        self.T += [datetime.datetime.max]

        # Rebuild profile and inject zeros where needed
        for i in range(len(self.T) - 1):

            # Add step
            T += [self.T[i]]
            y += [self.y[i]]

            # Get current step duration
            d = self.durations[i]

            # Compute time between current and next steps
            dT = self.T[i + 1] - self.T[i]

            # Step is a canceling one: replace it with a zero (default step)
            if d == datetime.timedelta(0):
                y[-1] = self.zero

            # Step ended before next one start: inject zero in profile
            elif d < dT:
                T += [self.T[i] + d]
                y += [self.zero]

        # Update profile
        self.T, self.y = T, y



    def pad(self, last = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Force profile limits as defined.
        """

        # Info
        Logger.debug("Padding: " + repr(self))

        # Make sure limits are defined
        if self.start is None or self.end is None:
            raise ValueError("Cannot pad, since profile limits undefined.")

        # No previous step was found: use profile zero (default) value
        if last is None:
            last = self.zero

        # Start of profile: extend precedent step's value
        if not self.T or self.T[0] != self.start:
            self.T = [self.start] + self.T
            self.y = [last] + self.y

        # End of profile
        if self.T[-1] != self.end:
            self.T += [self.end]
            self.y += [self.y[-1]]



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Fill holes in profile y-axis (replace 'None' values with the ones
            of filler profile).
        """

        # Is filling needed?
        if any([y is None for y in self.y]):

            # Info
            Logger.debug("Filling: " + repr(self))

            # Get number of steps in profile and filler
            n = len(self.T)
            m = len(filler.T)

            # Initialize new profile components
            T, y = [], []

            # Fill profile
            for i in range(n):

                # Restore step
                T += [self.T[i]]
                y += [self.y[i]]

                # Filling criteria
                if y[-1] is None:

                    # Fill step value
                    y[-1] = filler.f(T[-1])

                    # Before end of profile...
                    if i < n - 1:

                        # ...look for additional steps to fill
                        for j in range(m):

                            # Filling criteria
                            if self.T[i] < filler.T[j] < self.T[i + 1]:
                                T += [filler.T[j]]
                                y += [filler.y[j]]

                            # Stop looking in filler
                            elif self.T[i + 1] <= filler.T[j]:
                                break

            # Update profile
            self.T, self.y = T, y



    def smooth(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SMOOTH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Remove redundant steps in profile's axes.
        """

        # Info
        Logger.debug("Smoothing: " + repr(self))

        # Initialize components for smoothed profile
        T = [self.T[0]]
        y = [self.y[0]]

        # Look for redundancies
        for i in range(1, len(self.T) - 1):

            # If not redundant, add step
            if self.y[i] != y[-1]:
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

        # Define time axis to use based on input type
        if type(t) is datetime.datetime:
            axis = self.T

        elif lib.isRealNumber(t):
            axis = self.t
            
        else:
            raise TypeError("Invalid time t to compute f(t) for.")

        # Get number of steps
        n = len(axis)

        # Make sure axes fit
        if n != len(self.y):
            raise ArithmeticError("Cannot compute f(t): axes' lengths do not " +
                "fit.")

        # Compute profile value corresponding to given time:
        for i in range(n):
            if i == n - 1 and axis[i] == t or axis[i] <= t < axis[i + 1]:
                return self.y[i]

        # Result not found
        raise ValueError("The value of f(" + lib.formatTime(t) + ") does not " +
            "exist.")



    def operate(self, op, profiles):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            OPERATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Execute a given operation on profiles, and return the resulting
            profile.
        """

        # Test profile limits
        if not all([self.match(p) for p in profiles]):
            raise errors.MismatchedLimits

        # Deep copy original profile to use as baseline
        new = copy.deepcopy(self)

        # Combine all time axes, and recompute y-axis of baseline
        new.T = lib.unique(lib.flatten([p.T for p in profiles + [self]]))
        new.y = [self.f(T) for T in new.T]

        # Execute operation on baseline using given profiles
        for p in profiles:
            new.y = [op(new.f(T), p.f(T)) for T in new.T]

        # Normalize it if possible
        if new.norm is not None:
            new.normalize()

        return new



    def add(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        Logger.debug("Adding:")
        return self.operate(lambda x, y: x + y, list(args))



    def subtract(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUBTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        Logger.debug("Subtracting:")
        return self.operate(lambda x, y: x - y, list(args))



    def multiply(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MULTIPLY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        Logger.debug("Multiplying:")
        return self.operate(lambda x, y: x * y, list(args))



    def divide(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DIVIDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        Logger.debug("Dividing:")
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
        ax.step(self.t, self.y, where = "post", label = repr(self),
            lw = 2, ls = "-", c = color)

        # More than one line: add legend
        if len(ax.lines) > 1:
            ax.legend()

        # Ready to show?
        if show:
            plt.show()