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

    name = None

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize zero (default y-axis value)
        self.zero = None

        # Initialize units
        self.units = None

        # Initialize resettable components
        self.reset()



    def __repr__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            REPR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return "'" + self.__class__.__name__ + "'"



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Reset profile data.
        """

        # Info
        Logger.debug("Resetting: " + repr(self))

        # Reset axes
        self.T = []
        self.t = []
        self.y = []
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
            Build profile, from 'start' to 'end'. This method calls a reset,
            so the same profile object can be rebuilt on-the-fly.
        """

        # Info
        Logger.debug("Building: " + repr(self))

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

        # Test start/end types
        if type(start) is not datetime.datetime or type(start) is not type(end):
            raise TypeError("Start/end times have to be datetime objects.")

        # Info
        Logger.debug("Defining time references of: " + repr(self))

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
            Decouple profile data into components: convert string time values to
            datetime objects and get corresponding y-axis value.
        """

        # Info
        Logger.debug("Decoupling components of: " + repr(self))

        # Decouple components
        [self.T, self.y] = lib.unzip(sorted(self.data.items()))



    def cut(self, a = None, b = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Cut off all values that do not fit within [a, b]. Keep track of the
            last entry before start of profile.
        """

        # Test limit types
        if type(a) is not datetime.datetime or type(a) is not type(b):
            raise TypeError("Limit times to use while cutting profile have " +
                "to be datetime objects.")

        # Info
        Logger.debug("Cutting: " + repr(self))

        # No start given
        if a is None:
            a = self.start

        # No end given
        if b is None:
            b = self.end

        # Group axes and filter them
        data = zip(self.T, self.y)
        previousData = [x for x in data if x[0] < a]
        filteredData = [x for x in data if a <= x[0] <= b]

        # Find last value before beginning of profile
        last = previousData[-1][1] if previousData else None

        # Cut-off steps outside of start and end limits
        [self.T, self.y] = lib.unzip(filteredData)

        # Return core infos
        return [a, b, last]



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Normalize profile's time axis.
        """

        # Before using given reference time, verify its type
        if self.norm is None or type(self.norm) is not datetime.datetime:
            raise TypeError("Time axis can only be normalized using a " +
                "datetime object.")

        # Info
        Logger.debug("Normalizing: " + repr(self))

        # Normalize time to hours since norm
        self.t = [lib.normalizeTime(T, self.norm) for T in self.T]



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

                # Info
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

                    # Info
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
        title = title or repr(self)

        # Define axis labels
        x = "(h)"
        y = "(" + self.units + ")"

        # Set title and labels
        ax.set_title(title, fontweight = "semibold")
        ax.set_xlabel(x)
        ax.set_ylabel(y)

        # Set x-axis limits
        if self.xlim:
            ax.set_xlim(min(ax.get_xlim()[0], self.xlim[0]),
                        max(ax.get_xlim()[1], self.xlim[1]))

        # Set y-axis limits
        if self.ylim:
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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()