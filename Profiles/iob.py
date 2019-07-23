#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    iob

    Author:   David Leclerc

    Version:  0.2

    Date:     03.10.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import numpy as np
import datetime
import copy



# USER LIBRARIES
import logger
import reporter
import calculator
from dot import DotProfile
from past import PastProfile
from future import FutureProfile



# Define instances
Logger = logger.Logger("Profiles.iob")



class IOB(DotProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(IOB, self).__init__()

        # Define units
        self.units = "U"

        # Define report properties
        self.reportType = reporter.TreatmentsReport
        self.branch = ["IOB"]



class PastIOB(IOB, PastProfile):
    pass



class FutureIOB(IOB, FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureIOB, self).__init__()

        # Initialize step size
        self.dt = None
        self.dT = None



    def build(self, dt, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Build prediction profile of IOB decay.
        """

        # Info
        Logger.debug("Building 'FutureIOB'...")

        # Reset components
        self.reset()

        # Define time references
        self.define(net.end, IDC.DIA, dt)

        # Copy net insulin profile
        net = copy.deepcopy(net)

        # Compute IOB decay
        for _ in self.t:

            # Compute new IOB and store it
            self.y.append(calculator.computeIOB(net, IDC))

            # Move net insulin profile into the past
            for i in range(len(net.t)):

                # Update time axes
                net.t[i] -= self.dt

        # Derivate
        self.derivate()

        # Store current IOB
        self.store()

        # Show
        self.show()



    def define(self, start, DIA, dt):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define time references for prediction of IOB decay.
        """

        # Compute end of profile
        end = start + datetime.timedelta(hours = DIA)

        # Define step size
        self.dt = dt
        self.dT = datetime.timedelta(hours = dt)

        # Generate normalized time axis
        self.t = np.linspace(0, DIA, int(DIA / dt) + 1)

        # Generate datetime time axis
        self.T = [start + datetime.timedelta(hours = h) for h in self.t]

        # Finish defining
        super(FutureIOB, self).define(start, end)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: only stores current IOB for later displaying purposes.
        """

        # Info
        Logger.debug("Adding current IOB to: " + repr(self.reportType))

        # Add entry
        reporter.setDatedEntries(self.reportType, self.branch,
            { self.T[0]: round(self.y[0], 2) })