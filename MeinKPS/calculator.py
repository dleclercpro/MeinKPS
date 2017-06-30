#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    calculator

    Author:   David Leclerc

    Version:  0.1

    Date:     27.05.2016

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
import reporter
from Profiles import *



# Instanciate a reporter
Reporter = reporter.Reporter()



class Calculator(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize DIA
        self.DIA = None

        # Initialize IDC
        self.IDC = None

        # Give calculator a basal profile
        self.basal = basal.BasalProfile("Standard")

        # Give calculator a TB profile
        self.TB = TB.TBProfile()

        # Give calculator a bolus profile
        self.bolus = bolus.BolusProfile()

        # Give calculator a net profile
        self.net = suspend.SuspendProfile()

        # Give calculator an IOB profile
        self.IOB = IOB.FutureIOBProfile(IOB.PastIOBProfile())

        # Give calculator a COB profile
        self.COB = COB.COBProfile()

        # Give calculator an ISF profile
        self.ISF = ISF.ISFProfile()

        # Give calculator a CSF profile
        self.CSF = CSF.CSFProfile()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets.BGTargets()

        # Give calculator a BG profile
        self.BG = BG.FutureBGProfile(BG.PastBGProfile())

        # Initialize pump's max values
        self.max = {"Basal": None,
                    "Bolus": None}



    def run(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load components
        self.load()

        # Prepare components
        self.prepare(now)

        # Recommend TB and return it
        return self.recommend()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump report
        Reporter.load("pump.json")

        # Read DIA
        self.DIA = Reporter.getEntry(["Settings"], "DIA")

        # Give user info
        print "DIA: " + str(self.DIA) + " h"

        # Read max basal
        self.max["Basal"] = Reporter.getEntry(["Settings"], "Max Basal")

        # Give user info
        print "Max basal: " + str(self.max["Basal"]) + " U/h"

        # Read max bolus
        self.max["Bolus"] = Reporter.getEntry(["Settings"], "Max Bolus")

        # Give user info
        print "Max bolus: " + str(self.max["Bolus"]) + " U"



    def prepare(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute past start of insulin action
        past = now - datetime.timedelta(hours = self.DIA)

        # Compute future end of insulin action
        future = now + datetime.timedelta(hours = self.DIA)

        # Define IDC
        self.IDC = IDC.WalshIDC(self.DIA)

        # Build basal profile
        self.basal.build(past, now)

        # Build TB profile
        self.TB.build(past, now, self.basal)

        # Build bolus profile
        self.bolus.build(past, now)

        # Build net profile using suspend times
        self.net.build(past, now, self.TB.subtract(self.basal).add(self.bolus))

        # Build past IOB profile
        self.IOB.past.build(past, now)

        # Build future IOB profile
        self.IOB.build(self.net, self.IDC)

        # Build COB profile
        #self.COB.build(past, now)

        # Build ISF profile (over the next DIA)
        self.ISF.build(now, future)

        # Build CSF profile (over the next DIA)
        #self.CSF.build(now, future)

        # Build BG targets profile (over the next DIA)
        self.BGTargets.build(now, future)

        # Build past BG profile
        self.BG.past.build(past, now)

        # Build future BG profile
        self.BG.build(self.IOB, self.ISF)



    def recommend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECOMMEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recommend a bolus based on latest BG and future target average, taking
        into account ISF step curve over the next DIA hours (assuming natural
        decay of insulin).
        """

        # Give user info
        print "Recommending treatment..."

        # Compute eventual BG after complete IOB decay
        naiveBG = self.BG.expect(self.IDC.DIA, self.IOB)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        [deltaBG, BGI, expectedBGI] = self.BG.analyze(self.IOB, self.ISF)

        # Update eventual BG
        eventualBG = naiveBG + deltaBG

        # Compute BG target
        target = np.mean(self.BGTargets.y[-1])

        # Compute BG difference with average target
        dBG = target - eventualBG

        # Compute necessary dose
        dose = self.BG.dose(dBG, self.ISF, self.IDC)

        # Give user info
        print "BG target: " + str(target) + " " + self.BG.u
        print "Current BG: " + str(self.BG.past.y[-1]) + " " + self.BG.u
        print "Current ISF: " + str(self.ISF.y[0]) + " " + self.BG.u + "/U"
        print "Naive eventual BG: " + str(round(naiveBG, 1)) + " " + self.BG.u
        print "Eventual BG: " + str(round(eventualBG, 1)) + " " + self.BG.u
        print "dBG: " + str(round(dBG, 1)) + " " + self.BG.u
        print "Recommended dose: " + str(round(dose, 1)) + " U"

        # Define time to enact equivalent of dose (m)
        T = 0.5

        # Give user info
        print "Enactment time: " + str(T) + " h"

        # Find required basal difference to enact over given time (round to
        # pump's precision)
        dTB = round(dose / T, 2)

        # Compute TB to enact 
        TB = self.basal.y[-1] + dTB

        # Give user info
        print "Current basal: " + str(self.basal.y[-1]) + " U/h"
        print "Required basal difference: " + str(dTB) + " U/h"
        print "Temporary basal to enact: " + str(TB) + " U/h"

        # Convert enactment time to minutes
        T *= 60

        # Define computed TB recommendation
        R = [TB, "U/h", T]

        # If less insulin is needed
        if dose < 0:

            # Define minimal basal allowed (U/h)
            minTB = 0

            # Is required TB allowed?
            if TB < minTB:

                # Give user info
                print ("External action required: negative basal required. " +
                       "Eat something!")

                # Stop insulin delivery
                R = [minTB, "U/h", T]

        # If more insulin is needed
        elif dose > 0:

            # Find maximal basal allowed (U/h)
            maxTB = min(self.max["Basal"],
                        3 * self.basal.max,
                        4 * self.basal.y[0])

            # Give user info
            print "Theoretical max basal: " + str(self.max["Basal"]) + " U/h"
            print "3x max daily basal: " + str(3 * self.basal.max) + " U/h"
            print "4x current basal: " + str(4 * self.basal.y[0]) + " U/h"
            print "Max basal selected: " + str(maxTB) + " U/h"

            # Is required TB allowed?
            if TB > maxTB:

                # Give user info
                print ("External action required: maximal basal exceeded. " +
                       "Enact dose manually!")

                # Max out TB
                R = [maxTB, "U/h", T]

        # No modification to insulin dosage necessary
        else:

            # Give user info
            print ("No modification to insulin dosage necessary.")

            # No TB recommendation
            R = None

        # Look for conflictual info
        if (np.sign(BGI) == -1 and eventualBG > max(self.BGTargets.y[-1]) or
            np.sign(BGI) == 1 and eventualBG < min(self.BGTargets.y[-1])):

            # Give user info
            print ("Conflictual information: BG decreasing/rising although " +
                   "expected to land higher/lower than target range.")

            # No TB recommendation
            R = None

        # Give user info
        print ("Recommended TB: " + str(R[0]) + " " + R[1] + " (" + str(R[2]) +
               " m)")

        # Return recommendation
        return R



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a calculator
    calculator = Calculator()

    # Get current time
    now = datetime.datetime.now()

    # Run calculator
    calculator.run(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()