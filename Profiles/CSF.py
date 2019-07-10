#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    CSF

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
import base



class CSF(base.DailyProfile, base.FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(CSF, self).__init__()

        # Define report info
        self.report = reporter.PumpReport()
        self.branch = ["CSF"]

        # Read units
        units = self.report.get(["Units", "Carbs"])

        # In case of grams
        if units == "g":

            # Adapt units
            self.units = "g/U"

        # In case of exchanges
        elif units == "exchange":

            # Adapt units
            self.units = "U/exchange"