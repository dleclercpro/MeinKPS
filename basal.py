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
import profile



# DEFINITIONS
LOGS_ADDRESS = "./stickLogs.txt"
NOW          = datetime.datetime.now()



class Calculator:

    # BASAL CALCULATOR CHARACTERISTICS
    TALKATIVE        = True



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



    def inform(self, t, BG, TBR, IOB, COB):

        """
        ========================================================================
        INFORM
        ========================================================================
        """

        # Store input
        self.t = t                              # Times of BG readings
        self.dt = profile.BG_TIME_INTERVAL      # See user profile
        self.BG = BG                            # Blood glucose readings
        self.BG_scale = profile.BG_SCALE        # See user profile
        self.dBG_dt_max = profile.BG_MAX_RATE   # See user profile
        self.TBR = TBR                          # Temporary basal rates
        self.IOB = IOB                          # Insulin on board
        self.IC = profile.IC                    # See user profile
        self.ISF = profile.ISF                  # See user profile
        self.DIA = profile.DIA                  # See user profile
        self.COB = COB                          # Carbs on board



    def run(self):

        """
        ========================================================================
        RUN
        ========================================================================
        """

        # Compute time-derivative of BG
        self.dBG_dt = lib.derivate(self.BG, self.BG_TIME_INTERVAL)

        # Compute expected BG based on BG time-rate
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
