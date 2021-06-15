#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    daily

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



# USER LIBRARIES
import lib
import logger
from step import StepProfile



# Define instances
Logger = logger.Logger("Profiles.daily")



class DailyProfile(StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initializing
        super(DailyProfile, self).__init__()

        # Initialize report properties
        self.report = None
        self.branch = []



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Loading data for: " + repr(self))

        # Load data
        data = self.report.get(self.branch)

        # No data
        if not data:
            Logger.debug("No data found for: " + repr(self))

        # Found data
        else:
            Logger.debug("Loaded " + str(len(data)) + " data entries.")
            
            # Decouple and map it
            self.decouple(data)
            self.map()



    def map(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MAP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Repeat daily entries over the days covered by profile.
        """

        # Map each time and value to profile's whole set of days
        mappedEntries = [(datetime.datetime.combine(date, T), y)
            for (T, y) in zip(self.T, self.y) for date in self.dates]

        # Sort entries in chronological order and store them
        [self.T, self.y] = lib.unzip(sorted(mappedEntries))