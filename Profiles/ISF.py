#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    ISF

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



class ISF(base.DailyProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(ISF, self).__init__()
        
        # Define report info
        self.report = reporter.PumpReport()
        self.branch = ["ISF"]

        # Read units
        self.units = self.report.get(["Units", "BG"]) + "/U"



class PastISF(ISF, base.PastProfile):
    pass



class FutureISF(ISF, base.FutureProfile):
    pass