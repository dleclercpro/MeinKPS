#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    past

    Author:   David Leclerc

    Version:  0.2

    Date:     31.08.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import lib
import logger
import path
import reporter
from .profile import Profile



# Define instances
Logger = logger.Logger("Profiles/past.py")



class PastProfile(Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initializing
        super(PastProfile, self).__init__()

        # Initialize report properties (past profiles use dated reports)
        self.reportType = None
        self.branch = []



    def define(self, start, end):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define profile time references.
        """

        # Start defining
        super(PastProfile, self).define(start, end)

        # Define norm
        self.norm = end

        # Compute time difference
        dT = end - start

        # Define plot x-axis default limits
        self.xlim = [lib.normalizeTime(t, end) for t in
            [end - dT, end + dT]]



    def load(self, strict = False, src = path.REPORTS):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Load profile components from specified dated report(s).

            'strict' defines whether data should strictly be loaded within
            given time range or try and find the latest available.
        """

        # Info
        Logger.debug("Loading data for: " + repr(self))

        # Load data
        self.data = reporter.getDatedEntries(self.reportType, self.days,
            self.branch, strict, src)

        # Info
        Logger.debug("Loaded " + str(len(self.data)) + " data point(s).")



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()