#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    bg

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
import logger
import reporter
import calculator
from dot import DotProfile
from past import PastProfile
from future import FutureProfile



# Define instances
Logger = logger.Logger("Profiles.bg")



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
        self.units = reporter.getPumpReport().get(["Units", "BG"])

        # Define plot y-axis default limits
        # mmol/L
        if self.units == "mmol/L":
            self.ylim = [0, 15]
        
        # mg/dL
        elif self.units == "mg/dL":
            self.ylim = [0, 270]

        # Otherwise
        else:
            raise ValueError("Bad BG units.")



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



    def build(self, past, net, IDC, futureISF, dt, show = False):

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
        Logger.debug("Step size: " + str(self.dt) + " h")

        # Ensure there is one BG recent enough to accurately predict decay
        calculator.countValidBGs(past, 15, 1)

        # Reset previous BG predictions
        self.reset()

        # Define time references
        self.define(net.end, IDC.DIA, dt)

        # Initialize BG
        BG = past.y[-1]

        # Store initial (most recent) BG
        self.y.append(BG)

        # Copy net insulin profile
        net = copy.deepcopy(net)

        # Compute initial IOB
        IOBs = [calculator.computeIOB(net, IDC)]

        # Compute dBG
        for i in range(len(self.t) - 1):

            # Compute start/end of current step
            [t0, t1] = [self.t[i], self.t[i + 1]]

            # Generate time axis associated with ISF changes over current step
            t = [t0]
            t += list(filter(lambda t_: t0 < t_ < t1, futureISF.t))
            t += [t1]

            # Loop on ISF changes
            for j in range(len(t) - 1):

                # Move net insulin profile into the past
                dt = t[j + 1] - t[j]
                net.shift(-dt)

                # Compute new IOB and difference with last one
                IOB = calculator.computeIOB(net, IDC)
                dIOB = IOB - IOBs[-1]
                IOBs += [IOB]

                # Compute dBG for current step and corresponding expected BG
                dBG = futureISF.f(t[j]) * dIOB
                BG += dBG

            # Store BG at end of current step
            self.y += [BG]

        # Derivate
        self.derivate()

        # Show
        if show:
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

        # Generate time axes
        self.t = list(np.linspace(0, DIA, int(DIA / dt) + 1))
        self.T = [start + datetime.timedelta(hours = h) for h in self.t]

        # Finish defining
        super(FutureBG, self).define(start, end)