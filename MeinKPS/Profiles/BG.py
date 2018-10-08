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
import numpy as np
import datetime



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

        # Define plot y-axis default limits (mmol/L)
        self.ylim = [0, 15]

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



    def build(self, past, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Use predicted IOB decay curve and ISF to predict where BG will land
            after insulin activity is over, assuming a natural decay.

            FIXME: when predicting dBG and ISF changes, dBG != ISF0 * dIOB
        """

        # Give user info
        Logger.debug("Decaying BG...")

        # Make sure there is one BG that's max 15 minutes old to ensure
        # accurate predicted BG decay
        Calculator.countValidBGs(past, 1, 15)

        # Reset previous BG predictions
        self.reset()

        # Define time references using IOB decay prediction
        self.define(IOB)

        # Read latest BG and corresponding time
        BG = past.y[-1]

        # Add it to prediction
        self.y.append(BG)

        # Give user info
        Logger.debug("Step size: " + str(self.dt) + " h")
        Logger.debug("Initial BG: " + str(BG) + " " + self.units + " " +
                     "(" + lib.formatTime(past.T[-1]) + ")")

        # Get number of IOB predicted points
        n = len(IOB.T)

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n - 1):

            # Compute ISF
            isf = ISF.f(self.T[i])

            # Compute IOB change
            dIOB = IOB.y[i + 1] - IOB.y[i]

            # Compute BG change
            dBG = isf * dIOB

            # Update BG
            BG += dBG

            # Store current BG
            self.y.append(BG)

            # Give user info
            Logger.debug("ISF: " + str(isf) + " " + ISF.units)
            Logger.debug("dIOB: " + str(round(dIOB, 1)) + " " + IOB.units)
            Logger.debug("dBG: " + str(round(dBG, 1)) + " " + self.units)
            Logger.debug("BG: " + str(round(BG, 1)) + " " + self.units)

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Show
        self.show()



    def define(self, IOB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEFINE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Define time references for prediction of BG decay using the one for
            IOB.
        """

        # Copy step size
        self.dt = IOB.dt
        self.dT = IOB.dT

        # Copy normalized time axis
        self.t = IOB.t

        # Copy datetime time axis
        self.T = IOB.T

        # Finish defining
        super(FutureBG, self).define(IOB.start, IOB.end)






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