#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    IOB

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
import lib
import logger
import reporter
import calculator
import base



# Define instances
Logger = logger.Logger("Profiles/IOB.py")
Reporter = reporter.Reporter()
Calculator = calculator.Calculator()



class IOB(base.DotProfile):

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

        # Define report info
        self.report = "treatments.json"
        self.branch = ["IOB"]



class PastIOB(IOB, base.PastProfile):
    pass



class FutureIOB(IOB, base.FutureProfile):

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



    def build(self, net, IDC, dt = 5.0 / 60.0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Build prediction profile of IOB decay.
        """

        # Give user info
        Logger.debug("Predicting IOB...")

        # Reset components
        self.reset()

        # Define time references
        self.define(net.end, dt, IDC.DIA)

        # Copy net insulin profile
        net = copy.copy(net)

        # Get number of prediction dots in IOB profile
        n = len(self.t)

        # Get number of entries in net insulin profile
        m = len(net.t)

        # Compute initial IOB and store it
        self.y.append(Calculator.computeIOB(net, IDC))

        # Compute IOB decay (initial dot already done)
        for i in range(n - 1):

            # Move net insulin profile into the past
            for j in range(m):

                # Update time axes
                net.T[j] -= self.dT
                net.t[j] -= self.dt

            # Compute new IOB and store it
            self.y.append(Calculator.computeIOB(net, IDC))

        # Derivate
        self.derivate()

        # Store current IOB
        self.store()

        # Show
        self.show()



    def define(self, start, dt, DIA):

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

        # Give user info
        Logger.debug("Adding current IOB to report: '" + self.report + "'...")

        # Add entry
        Reporter.add(self.report, self.branch, {self.T[0]: round(self.y[0], 2)})