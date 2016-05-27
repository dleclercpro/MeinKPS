#! /usr/bin/python



"""
================================================================================
Title:    basal
Author:   David Leclerc
Version:  0.1
Date:     27.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: ...
Notes:    ...
================================================================================
"""



# LIBRARIES
import os
import sys
import time
import datetime
import numpy as np



# USER LIBRARIES
import lib
import stick
import pump



# DEFINITIONS
LOGS_ADDRESS = "./stickLogs.txt"
NOW          = datetime.datetime.now()



class Calculator:

    # BASAL CALCULATOR CHARACTERISTICS
    TALKATIVE        = True
    BG_TIME_INTERVAL = 5
    BG_MAX_RATE      = 0
    BG_MMOL_L_SCALE = {"Extreme Low"  : 1.5,
                       "Huge Low"     : 2.0,
                       "Big Low"      : 2.5,
                       "Low"          : 3.0,
                       "Little Low"   : 3.5,
                       "Tiny Low"     : 3.8,
                       "Target Low"   : 4.0,
                       "Target High"  : 7.0,
                       "Tiny High"    : 8.0,
                       "Little High"  : 10.0,
                       "High"         : 12.0,
                       "Big High"     : 15.0,
                       "Huge High"    : 18.0,
                       "Extreme High" : 20.0}
    BG_MG_DL_SCALE = {i : int(18 * BG_MMOL_L_SCALE[i]) for i in BG_MMOL_L_SCALE}



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        """



    def inform(self, t, BG, TBR, IOB, IS, CB):

        """
        ========================================================================
        INFORM
        ========================================================================
        """

        # Store input
        self.t = t                      # Times
        self.BG = BG                    # Blood glucose values
        self.TBR = TBR                  # Temporary basal rates
        self.IOB = IOB                  # Insulin on board
        self.IS = IS                    # Insulin sensitivities (based on time)
        self.CB = CB                    # Carbs taken



    def run(self):

        """
        ========================================================================
        RUN
        ========================================================================
        """

        # Compute time-derivative of BG
        self.dBG_dt = lib.derivate(self.BG, self.BG_TIME_INTERVAL)

        # Compute expected BG based on dBG/dt
        self.expected_BG = 0

        # Reset TBR recommendation
        self.TBR_recommendation = 0

        # Compute TBR recommendation
        self.TBR_recommendation = 0



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a basal calculator for me
    calculator = Calculator()

    # Start calculator
    calculator.start()

    # Inform calculator
    calculator.inform()

    # Run calculator
    calculator.run()

    # Stop calculator
    calculator.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
