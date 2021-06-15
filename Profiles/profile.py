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
            Reset profile.
        """

        # Info
        Logger.debug("Resetting: " + repr(self))

        # Reset axes
        self.T = []
        self.t = []
        self.y = []

        # Reset start/end times
        self.start = None
        self.end = None

        # Reset time norm
        self.norm = None

        # Reset range of days covered
        self.dates = []

        # Reset plot limits
        self.xlim = []
        self.ylim = []



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

        # Load profile data
        self.load()



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
        if not all([type(T) is datetime.datetime for T in [start, end]]):
            raise TypeError("Start/end times have to be datetime objects.")

        # Does time order make sense?
        if not start < end:
            raise ValueError("Start has to be before end time.")

        # Store start/end times
        self.start = start
        self.end = end

        # Compute time difference between start/end times
        dT = end - start

        # Define dates covered by profile, including one before start, to ensure
        # beginning of profile is known
        self.dates = [start.date() + datetime.timedelta(days = d)
            for d in range(-1, dT.days + 1)]



    def match(self, p):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MATCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Check whether limits of current and given profiles match.

            Note: this function assumes both standard and normalized time axes
                  are defined for both profiles.
        """

        # Test time axes limits
        try:

            # Initialize default result
            isMatching = True

            # Normalized time axis exists on at least one profile
            if self.t or p.t:
                isMatching = self.t[0] == p.t[0] and self.t[-1] == p.t[-1]

            return (self.start == p.start and self.end == p.end and
                    self.T[0] == p.T[0] and self.T[-1] == p.T[-1] and
                    isMatching)

        # Limits do not match
        except:
            return False



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Load data to use while building profile's axes.
        """

        raise NotImplementedError



    def decouple(self, data):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decouple profile data into axes: convert string time values to
            datetime objects, sorted out in chronological order, and get their
            associated values.
        """

        # Info
        Logger.debug("Decoupling data into axes of: " + repr(self))

        # Decouple data
        [self.T, self.y] = lib.unzip([(lib.formatTime(T), y) for (T, y) in
            sorted(data.items())])



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

        # No start/end given
        if a is None:
            a = self.start
        
        if b is None:
            b = self.end

        # Test limit types
        if type(a) is not type(b):
            raise TypeError("Limit times must have the same type.")

        # Find time axis to use
        if type(a) is datetime.datetime:
            axis = self.T

        elif lib.isRealNumber(a):
            axis = self.t
        
        else:
            raise TypeError("Invalid limit type to cut profile.")

        # Group axes
        data = zip(axis, self.y)

        # Filter axes, while keeping data before starting limit
        precedingData = [(t, y) for (t, y) in data if t < a]
        filteredData = [(t, y) for (t, y) in data if a <= t <= b]

        # Cut off steps outside of start and end limits
        if type(a) is datetime.datetime:
            [self.T, self.y] = lib.unzip(filteredData)

            # In case no norm is defined don't try to cut normalized time axis
            if self.norm:
                self.normalize()

        else:
            [self.t, self.y] = lib.unzip(filteredData)
            self.standardize()

        # Find value right before beginning of profile
        (_, last) = precedingData[-1] if precedingData else (None, None)

        # Return it
        return last



    def standardize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STANDARDIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Using its normalized time axis, define profile's standard time axis,
            based on datetime objects.
        """

        Logger.debug("Standardizing: " + repr(self))

        self.T = lib.standardizeTimeAxis(self.t, self.norm)



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Normalize profile's standard time axis to number of hours since/
            until norm).
        """

        Logger.debug("Normalizing: " + repr(self))

        self.t = lib.normalizeTimeAxis(self.T, self.norm)



    def shift(self, delta):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHIFT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Shift profile's time axes in the past/future.
        """

        # Info
        Logger.debug("Shifting: " + repr(self))

        # Type checking
        if type(delta) is datetime.timedelta:
            dT = delta
            dt = delta.total_seconds() / 3600.0

        elif lib.isRealNumber(delta):
            dT = datetime.timedelta(hours = delta)
            dt = delta

        else:
            raise TypeError("Cannot shift profile's time axes using type: " +
                str(type(delta)))

        # Shift start/end times (but not the norm!)
        self.start += dT
        self.end += dT

        # Shift time axes
        self.T = [T + dT for T in self.T]
        self.t = [t + dt for t in self.t]



    def show(self, version = "Standard"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Print various versions of profile.
        """

        # Get time axis
        if version == "Standard":
            timeAxis = self.T

        elif version == "Normalized":
            timeAxis = self.t

        else:
            raise TypeError("Invalid time axis type to use.")

        # Info
        Logger.info(repr(self) + " - " + version)

        # Show profile
        for (t, y) in zip(timeAxis, self.y):

            # Format time if necessary
            if version == "Standard":
                t = lib.formatTime(t)

            # Format value if necessary
            if lib.isRealNumber(y):
                y = round(y, 2)

            # Show entry
            Logger.info(str(y) + " (" + str(t) + ")")



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

        # In order to plot, a time reference is necessary
        if self.norm is None:
            raise ValueError("Impossible to plot profile without a time " +
                "reference.")

        # Compute x-axis limits, using time norm of profile
        dT = self.end - self.start
        start = self.norm - dT
        end = self.norm + dT

        # Define x-axis limits
        self.xlim = lib.normalizeTimeAxis([start, end], self.norm)

        # Set x-axis limits
        ax.set_xlim(min(ax.get_xlim()[0], self.xlim[0]),
            max(ax.get_xlim()[1], self.xlim[1]))

        # Set y-axis limits
        if self.ylim:
            ax.set_ylim([min(ax.get_ylim()[0], self.ylim[0]),
                max(ax.get_ylim()[1], self.ylim[1])])

        # Return figure and subplot
        return ax