#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    BG

    Author:   David Leclerc

    Version:  0.2

    Date:     09.10.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import copy
import datetime
import numpy as np



# USER LIBRARIES
from .. import logger
from .. import reporter
from .. import calculator
from dot import DotProfile
from past import PastProfile
from future import FutureProfile



# Define instances
Logger = logger.Logger("Profiles/BG.py")



class BG(DotProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BG, self).__init__()

        # Read units
        self.units = reporter.REPORTS["pump"].get(["Units", "BG"])

        # Define plot y-axis default limits
        self.ylim = [0, 15] if self.units == "mmol/L" else [0, 270]



class PastBG(BG, PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastBG, self).__init__()

        # Define report properties
        self.reportType = reporter.BGReport
        self.branch = []



class FutureBG(BG, FutureProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureBG, self).__init__()

        # Initialize step size
        self.dt = None
        self.dT = None



    def build(self, dt, net, IDC, futureISF, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Predict natural IOB decay and compute resulting BG variation at the
            same time, using ISF profile and IDC. The formula used to compute it
            is given by:

                dBG = SUM_t' ISF(t') * dIOB(t')

            where t' represents the value of a given time step, dIOB(t') the
            drop in active insuline (IOB) during that time, and ISF(t') the
            corresponding insulin sensitivity factor. The variation in BG after
            the end of insulin activity is given by dBG.
        """

        # Info
        Logger.debug("Building 'FutureBG'...")

        # Ensure there is one BG recent enough to accurately predict decay
        calculator.countValidBGs(past, 15, 1)

        # Initialize BG
        BG = past.y[-1]

        # Info
        Logger.debug("Step size: " + str(self.dt) + " h")
        Logger.debug("Initial BG: " + str(BG) + " " + self.units)

        # Reset previous BG predictions
        self.reset()

        # Define time references
        self.define(net.end, IDC.DIA, dt)

        # Store initial (most recent) BG
        self.y.append(BG)

        # Copy net insulin profile
        net = copy.deepcopy(net)

        # Compute initial IOB
        IOB0 = calculator.computeIOB(net, IDC)

        # Read number of steps in prediction
        n = len(self.t) - 1

        # Read number of entries in net insulin profile
        m = len(net.t)

        # Read number of entries in ISF profile
        l = len(futureISF.t)

        # Compute dBG
        for i in range(n):

            # Compute start/end of current step
            t0 = self.t[i]
            t1 = self.t[i + 1]

            # Initialize time axis associated with ISF changes
            t = []

            # Define start time
            t.append(t0)

            # Fill it with ISF change times
            for j in range(l):

                # Change contained within current step
                if t0 < futureISF.t[j] < t1:

                    # Add it
                    t.append(futureISF.t[j])

            # Define end time
            t.append(t1)

            # Loop on ISF changes
            for j in range(len(t) - 1):

                # Define step
                dt = t[j + 1] - t[j]

                # Move net insulin profile into the past
                for k in range(m):

                    # Update normalized time axis
                    net.t[k] -= dt

                # Compute new IOB
                IOB = calculator.computeIOB(net, IDC)

                # Compute dIOB
                dIOB = IOB - IOB0

                # Update IOB
                IOB0 = IOB

                # Compute dBG for current step
                dBG = futureISF.f(t[j]) * dIOB

                # Compute expected BG
                BG += dBG

            # Store BG at end of current step
            self.y.append(BG)

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Show
        self.show()



    def define(self, start, DIA, dt):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define time references for prediction of BG decay.
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
        super(FutureBG, self).define(start, end)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a BG profile
    pastBG = PastBG()
    futureBG = FutureBG()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()