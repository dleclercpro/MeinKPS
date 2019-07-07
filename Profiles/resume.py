#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    resume

    Author:   David Leclerc

    Version:  0.1

    Date:     27.07.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import base



class Resume(base.PastProfile, base.StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(Resume, self).__init__()

        # Initialize zero (no data found: assume pump is not suspended)
        self.zero = 1

        # Define units
        self.units = "U/h"

        # Load latest data available
        self.strict = False

        # Define report info
        self.report = "treatments.json"
        self.branch = ["Suspend/Resume"]



    def fill(self, filler):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Change resume times to None before filling with net insulin profile.
        """

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # If resume
            if self.y[i] == 1:

                # Fill later
                self.y[i] = None

        # Fill
        super(Resume, self).fill(filler)