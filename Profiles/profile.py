#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    profile

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
import datetime
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger



# Define instances
Logger = logger.Logger("Profiles/profile.py")



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

        raise NotImplementedError



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
                raise ValueError("Profile t-axis cannot be normalized: " +
                    "profile does not have a norm.")

        # Before using given reference time, verify its type
        if type(T) is not datetime.datetime:
            raise TypeError("Time axis can only be normalized using a " +
                "datetime object.")

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