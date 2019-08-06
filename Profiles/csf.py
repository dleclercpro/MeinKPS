#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    csf

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import reporter
from daily import DailyProfile
from past import PastProfile
from future import FutureProfile



class CSF(DailyProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(CSF, self).__init__()

        # Define report properties
        self.report = reporter.getPumpReport()
        self.branch = ["CSF"]

        # Read units
        units = self.report.get(["Units", "Carbs"])

        # In case of grams
        if units == "g":
            self.units = "g/U"

        # In case of exchanges
        elif units == "exchange":
            self.units = "U/exchange"

        # Bad units
        else:
            raise ValueError("Bad CSF units.")



class PastCSF(CSF, PastProfile):
    pass

class FutureCSF(CSF, FutureProfile):
    pass