#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    BG

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
import copy
import datetime
import numpy as np



# USER LIBRARIES
import lib
import logger
import errors
import reporter
import calculator
import base



# Define instances
Logger = logger.Logger("Profiles/BG.py")
Reporter = reporter.Reporter()
Calculator = calculator.Calculator()



class BG(base.DotProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BG, self).__init__()

        # Read units
        self.units = Reporter.get("pump.json", ["Units"], "BG")

        # Define plot y-axis default limits
        if self.units == "mmol/L":

            # mmol/L
            self.ylim = [0, 15]

        elif self.units == "mg/dL":

            # mg/dL
            self.ylim = [0, 270]

        # Define report info
        self.report = "BG.json"



class PastBG(BG, base.PastProfile):
    pass



class FutureBG(BG, base.FutureProfile):

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



    def build(self, dt, net, IDC, ISF, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Predict natural IOB decay and compute resulting dBG at the same
            time, using ISF.
        """

        # Give user info
        Logger.debug("Decaying BG...")

        # Ensure there is one BG recent enough to accurately predict decay
        Calculator.countValidBGs(past, 1, 15)

        # Initialize BG
        BG = past.y[-1]

        # Give user info
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
        IOB0 = Calculator.computeIOB(net, IDC)

        # Read number of steps in prediction
        n = len(self.t) - 1

        # Read number of entries in net insulin profile
        m = len(net.t)

        # Read number of entries in ISF profile
        l = len(ISF.t)

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
                if t0 < ISF.t[j] < t1:

                    # Add it
                    t.append(ISF.t[j])

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
                IOB = Calculator.computeIOB(net, IDC)

                # Compute dIOB
                dIOB = IOB - IOB0

                # Update IOB
                IOB0 = IOB

                # Compute dBG for current step
                dBG = ISF.f(t[j]) * dIOB

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









    def project(self, dt):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PROJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BG projection based on expected duration dt (h) of current BG trend
        """

        # Give user info
        Logger.info("Projection time: " + str(dt) + " h")

        # Read latest BG
        BG = self.past.y[-1]

        # Compute derivative to use when predicting future BG
        dBGdt = self.past.impact()

        # Predict future BG
        BG += dBGdt * dt

        # Return BG projection based on dBG/dt
        return BG


    def expect(self, dt, IOB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BG expectation after a certain time dt (h) based on IOB decay
        """

        # Give user info
        Logger.info("Expectation time: " + str(dt) + " h")

        # Get number of steps corresponding to expected BG
        n = dt / IOB.dt - 1

        # Check if expectation fits with previously computed BGs
        if int(n) != n or n < 0:

            # Exit
            raise errors.BadBGTime()

        # Return expected BG
        return self.y[int(n)]



    def analyze(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ANALYZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Analyze and compute BG-related values.
        """

        # Give user info
        Logger.debug("Analyzing BG...")

        # Define prediction time (h)
        dt = 0.5

        # Compute projected BG based on latest CGM readings
        projectedBG = self.project(dt)

        # Compute BG variation due to IOB decay
        expectedBG = self.expect(dt, IOB)

        # Read BGI
        BGI = self.past.impact()

        # Compute BGI (dBG/dt) based on IOB decay
        expectedBGI = IOB.dydt[0] * ISF.y[0]

        # Compute deviation between BGs
        deltaBG = projectedBG - expectedBG

        # Compute deviation between BGIs
        deltaBGI = BGI - expectedBGI

        # Give user info (about BG)
        Logger.info("Expected BG: " + str(round(expectedBG, 1)) + " " +
                    self.units)
        Logger.info("Projected BG: " + str(round(projectedBG, 1)) + " " +
                    self.units)
        Logger.info("BG deviation: " + str(round(deltaBG, 1)) + " " +
                    self.units)

        # Give user info (about BGI)
        Logger.info("Expected BGI: " + str(round(expectedBGI, 1)) + " " +
                    self.units + "/h")
        Logger.info("BGI: " + str(round(BGI, 1)) + " " +
                    self.units + "/h")
        Logger.info("BGI deviation: " + str(round(deltaBGI, 1)) + " " +
                    self.units + "/h")

        # Give user info
        Logger.debug("End of BG analysis.")

        # Return computations
        return [deltaBG, BGI, expectedBGI]



    def dose(self, dBG, ISF, IDC):

        # FIXME

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Compute bolus to bring back BG to target using ISF and IDC.
        """

        # Initialize conversion factor between dose and BG difference to target
        f = 0

        # Get number of ISF steps
        n = len(ISF.t) - 1

        # Compute factor
        for i in range(n):

            # Compute step limits
            a = ISF.t[i] - IDC.DIA
            b = ISF.t[i + 1] - IDC.DIA

            # Update factor with current step
            f += ISF.y[i] * (IDC.f(a) - IDC.f(b))

        # Compute bolus
        bolus = dBG / f

        # Return bolus
        return bolus



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a BG profile
    BG = FutureBG()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()