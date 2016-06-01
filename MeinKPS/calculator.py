#! /usr/bin/python



"""
================================================================================
Title:    calculator

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
import reporter



class Calculator:

    # BASAL CALCULATOR CHARACTERISTICS
    TALKATIVE = True



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Give the calculator a reporter
        self.reporter = reporter.Reporter()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        """



    def inform(self, t, BG, TB, IOB, COB):

        """
        ========================================================================
        INFORM
        ========================================================================
        """

        # Store given input about current situation
        self.t = t
        self.BG = BG
        self.TB = TB
        self.IOB = IOB
        self.COB = COB

        # Read user profile
        # Read time interval between BG readings
        self.dt = self.reporter.getEntry(report_name = "profile",
                                         entry_type = "Settings",
                                         entry_key = "BG Time Interval")

        # Read BG scale
        self.scale = self.reporter.getEntry(report_name = "profile",
                                            entry_type = "Settings",
                                            entry_key = "BG Scale")

        # Read duration of insulin action
        self.DIA = self.reporter.getEntry(report_name = "profile",
                                          entry_type = "Settings",
                                          entry_key = "DIA")

        # Read insulin to carbs factors
        self.ICF = self.reporter.getEntry(report_name = "profile",
                                          entry_type = "Settings",
                                          entry_key = "ICF")

        # Read insulin sensitivities factors
        self.ISF = self.reporter.getEntry(report_name = "profile",
                                          entry_type = "Settings",
                                          entry_key = "ISF")

        # Read maximal allowed BG time-rate
        self.max_dBG_dt = self.reporter.getEntry(report_name = "profile",
                                                 entry_type = "Settings",
                                                 entry_key = "BG Maximal Rate")



    def run(self):

        """
        ========================================================================
        RUN
        ========================================================================
        """

        # Compute time-derivative of BG
        self.dBG_dt = lib.derivate(self.BG, self.dt)

        # Compute expected BG based on BG time-rate
        self.expected_BG = 0

        # Reset temporary recommendation
        self.recommendation = 0

        # Compute temporary basal recommendation
        self.recommendation = 0



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
    calculator.inform(t = [0, 1, 2, 3],
                      BG = [5.0, 6.0, 7.0, 8.0],
                      TB = [0.5, "U/h", 30],
                      IOB = 5.5,
                      COB = 0)

    # Run calculator
    #calculator.run()

    # Stop calculator
    #calculator.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
