#! /usr/bin/python



"""
================================================================================
Title:    reporter
Author:   David Leclerc
Version:  0.1
Date:     30.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: ...
Notes:    ...
================================================================================
"""

# TODO
# - Create report and/or categories if non-existent



# LIBRARIES
import os
import sys
import time
import datetime as datetime
import numpy as np
import json



class Reporter:

    # REPORTER CHARACTERISTICS
    TALKATIVE = True



    def addEntry(self):

        """
        ========================================================================
        ADDENTRY
        ========================================================================
        """



    def printEntries(self):

        """
        ========================================================================
        PRINTENTRIES
        ========================================================================
        """

        # Load reports
        with open("Reports/insulin.json", "r") as f:
            insulin_report = json.load(f)

        # Print report entries
        print insulin_report



    def addReservoirLevelEntry(self):

        """
        ========================================================================
        ADDRESERVOIRLEVELENTRY
        ========================================================================
        """

        # Load reports
        with open("Reports/pump.json", "r") as f:
            insulin_report = json.load(f)

        # ...
        for i in range(4):
            time.sleep(1)

            now = datetime.datetime.now()
            now_str = datetime.datetime.strftime(now, "%Y.%m.%d - %H:%M:%S")

            level = i * 4.5

            insulin_report["Reservoir Levels"][now_str] = level

        # Save to file
        with open("Reports/pump.json", "w") as f:
            json.dump(insulin_report, f,
                      indent = 4, separators = (",", ": "), sort_keys = True)



    def addBolusEntry(self):

        """
        ========================================================================
        ADDBOLUSENTRY
        ========================================================================
        """

        # Load reports
        with open("Reports/insulin.json", "r") as f:
            insulin_report = json.load(f)

        # ...
        for i in range(4):
            time.sleep(1)

            now = datetime.datetime.now()
            now_str = datetime.datetime.strftime(now, "%Y.%m.%d - %H:%M:%S")

            bolus = i * 5.0

            insulin_report["Boluses"][now_str] = bolus

        # Save to file
        with open("Reports/insulin.json", "w") as f:
            json.dump(insulin_report, f,
                      indent = 4, separators = (",", ": "), sort_keys = True)



    def addTemporaryBasalEntry(self):

        """
        ========================================================================
        ADDTEMPORARYBASALENTRY
        ========================================================================
        """

        # Load reports
        with open("Reports/insulin.json", "r") as f:
            insulin_report = json.load(f)

        # ...
        for i in range(4):
            time.sleep(1)

            now = datetime.datetime.now()
            now_str = datetime.datetime.strftime(now, "%Y.%m.%d - %H:%M:%S")

            rate = i * 1.5
            units = "U/h"
            duration = i * 30

            insulin_report["Temporary Basals"][now_str] = [rate,
                                                           units,
                                                           duration]

        # Save to file
        with open("Reports/insulin.json", "w") as f:
            json.dump(insulin_report, f,
                      indent = 4, separators = (",", ": "), sort_keys = True)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a reporter for me
    reporter = Reporter()

    # Add entries to reports
    reporter.addReservoirLevelEntry()
    reporter.addBolusEntry()
    reporter.addTemporaryBasalEntry()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
