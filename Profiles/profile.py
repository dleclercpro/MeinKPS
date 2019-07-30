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
import path



# Define instances
Logger = logger.Logger("Profiles.profile")



class Profile(object):

    name = None

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resettable components
        self.reset()

        # Initialize zero (default y-axis value)
        self.zero = None

        # Initialize units
        self.units = None

        # Initialize source directory to load data from
        self.src = path.REPORTS



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

        # Info
        Logger.debug("Defining time references of: " + repr(self))

        # Test start/end types
        if type(start) is not datetime.datetime or type(start) is not type(end):
            raise TypeError("Start/end times have to be datetime objects.")

        # Does time order make sense?
        if not start < end:
            raise ValueError("Start has to be before end time.")

        # Define start/end times
        self.start = start
        self.end = end

        # Reset days covered by profile
        self.days = []

        # First day to cover (always one before start date)
        day = start.date() - datetime.timedelta(days = 1)

        # Fill days until end date is reached
        while day <= end.date():
            self.days.append(day)

            # Update day
            day += datetime.timedelta(days = 1)

        # Normalized profile
        if self.norm is not None:

            # Compute time difference
            dT = end - start

            # Define plot x-axis default limits
            self.xlim = [lib.normalizeTime(t, self.norm) for t in
                [self.norm - dT, self.norm + dT]]



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

        # Decouple data, convert string times to datetimes, and sort them in
        # chronological order
        [self.T, self.y] = lib.unzip([(lib.formatTime(T), y) for (T, y) in
            sorted(self.data.items())])



    def cut(self, a = None, b = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CUT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Cut off all values that do not fit within [a, b]. Keep track of the
            last entry before start of profile.
        """

        # Info
        Logger.debug("Cutting: " + repr(self))

        # No start given
        if a is None:
            a = self.start

        # No end given
        if b is None:
            b = self.end

        # Test limit types
        if type(a) is not datetime.datetime or type(a) is not type(b):
            raise TypeError("Limit times to use while cutting profile have " +
                "to be datetime objects.")

        # Group axes and filter them
        data = zip(self.T, self.y)
        olderData = [x for x in data if x[0] < a]
        filteredData = [x for x in data if a <= x[0] <= b]

        # Cut-off steps outside of start and end limits
        [self.T, self.y] = lib.unzip(filteredData)

        # Find last value before beginning of profile
        last = olderData[-1][1] if olderData else None

        # Return step value before beginning of profile
        return last



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Normalize profile's time axis.
        """

        # Info
        Logger.debug("Normalizing: " + repr(self))

        # Before using given reference time, verify its type
        if self.norm is None or type(self.norm) is not datetime.datetime:
            raise TypeError("Time axis can only be normalized using a " +
                "datetime object.")

        # Normalize time to hours since norm
        self.t = [lib.normalizeTime(T, self.norm) for T in self.T]



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Print various versions of profile.
        """

        # Define axes dictionary
        versions = {"Standard t-axis": zip(self.T, self.y),
                    "Normalized t-axis": zip(self.t, self.y),
                    "Derivative": zip(self.t[:-1], self.dydt)}

        # Loop on each profile component
        for version, entries in versions.items():

            # If not empty
            if entries:
                Logger.debug(repr(self) + " - " + version)

                # Show entries
                for entry in entries:

                    # Get time and value
                    t = entry[0]
                    y = entry[1]

                    # Format time if necessary
                    if type(t) is not float:
                        t = lib.formatTime(t)

                    # Format value if necessary
                    if type(y) is float or type(y) is np.float64:
                        y = round(y, 2)

                    # Info
                    Logger.debug(str(y) + " (" + str(t) + ")")



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