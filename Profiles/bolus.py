#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    bolus

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import reporter
from step import StepProfile
from past import PastProfile



class Bolus(PastProfile, StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(Bolus, self).__init__()

        # Define profile zero
        self.zero = 0

        # Define units
        self.units = "U/h"

        # Define bolus delivery rate
        self.rate = 90.0

        # Read theoretical max
        self.max = reporter.REPORTS["pump"].get(["Settings", "Max Bolus"])

        # Define report properties
        self.reportType = reporter.TreatmentsReport
        self.branch = ["Boluses"]



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(Bolus, self).decouple()

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # Compute delivery time
            self.d.append(datetime.timedelta(hours = 1 / self.rate * self.y[i]))

            # Convert bolus to delivery rate
            self.y[i] = self.rate