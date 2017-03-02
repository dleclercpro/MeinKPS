#! /usr/bin/python

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
import os
import sys
import time
import datetime
import numpy as np



# USER LIBRARIES
import lib
import reporter



class Calculator:

    # CALCULATOR CHARACTERISTICS

    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the calculator a reporter
        self.reporter = reporter.Reporter()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """



    def inform(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INFORM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store input about current situation
        TB = [0.5, "U/h", 30]

        # Read user profile
        # Read time interval between BG readings
        self.dt = self.reporter.getEntry(report_name = "profile.json",
                                         entry_type = "Settings",
                                         entry_key = "BG Time Interval")

        # Read BG scale
        self.scale = self.reporter.getEntry(report_name = "profile.json",
                                            entry_type = "Settings",
                                            entry_key = "BG Scale")

        # Read duration of insulin action
        self.DIA = self.reporter.getEntry(report_name = "profile.json",
                                          entry_type = "Settings",
                                          entry_key = "DIA")

        # Read insulin to carbs factors
        self.ICF = self.reporter.getEntry(report_name = "profile.json",
                                          entry_type = "Settings",
                                          entry_key = "ICF")

        # Read insulin sensitivities factors
        self.ISF = self.reporter.getEntry(report_name = "profile.json",
                                          entry_type = "Settings",
                                          entry_key = "ISF")

        # Read maximal allowed BG time-rate
        self.max_dBG_dt = self.reporter.getEntry(report_name = "profile.json",
                                                 entry_type = "Settings",
                                                 entry_key = "BG Maximal Rate")



    def computeIOB(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTEIOB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        IOB = 5



    def computeCOB(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTECOB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        COB = 5



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute time-derivative of BG
        self.dBG_dt = lib.derivate(self.BG, self.dt)
        print len(self.dBG_dt)

        # Compute expected BG based on BG time-rate
        self.expected_BG = 0

        # Reset temporary recommendation
        self.recommendation = 0

        # Compute temporary basal recommendation
        self.recommendation = 0



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    #calculator.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
