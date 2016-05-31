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



# TERMINOLOGY
# - BG: Blood glucose [mmol/l]
# - TB: Temporary basal (rate) [U/h]
# - ICF: Insulin to carbs factors [U/(15g)]
# - ISF: Insulin sensitivity factors [(mmol/l)/U]
# - DIA: Duration of insulin action [h]
# - IOB: Insulin on board [U]
# - COB: Carbs on board [g]
# - BG Maximal Rate: Maximal allowed BG rate [(mmol/l)/h]
# - BG Time Interval: Time interval between two BG readings [m]



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



    def addEntry(self, report_name, entry_type, entry_key, entry):

        """
        ========================================================================
        ADDENTRY
        ========================================================================
        """

        # Load report
        with open("Reports/" + report_name + ".json", "r") as f:
            report = json.load(f)

        # Look if entry is not already in report
        if entry_key in report[entry_type]:

            # Give user info
            print ("Entry already exists in '" + report_name + ".json':" +
                   str(entry_type) + ", " + str(entry_key) + ", " + str(entry))

        # If not, write it down
        else:

            # Give user info
            print ("New entry for '" + report_name + ".json':" +
                   str(entry_type) + ", " + str(entry_key) + ", " + str(entry))

            # Add entry to report
            report[entry_type][entry_key] = entry

            # Rewrite report
            with open("Reports/" + report_name + ".json", "w") as f:
                json.dump(report, f,
                          indent = 4,
                          separators = (",", ": "),
                          sort_keys = True)



    def getEntry(self, report_name, entry_type, entry_key):

        """
        ========================================================================
        GETENTRY
        ========================================================================
        """

        # Load report
        with open("Reports/" + report_name + ".json", "r") as f:
            report = json.load(f)

        # Look if entry exists
        if entry_key in report[entry_type]:

            # Get entry matching the key
            entry = report[entry_type][entry_key]

            # Give user info
            print ("Entry found in '" + report_name + ".json': " +
                   str(entry_type) + ", " + str(entry_key) + ", " + str(entry))

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print ("No matching entry found in '" + report_name + ".json': " +
                   str(entry_type) + ", " + str(entry_key) + ", ?")



    def printEntries(self, report):

        """
        ========================================================================
        PRINTENTRIES
        ========================================================================
        """

        # Load report
        with open("Reports/" + report + ".json", "r") as f:
            report = json.load(f)

        # Print report entries
        print report



    def addReservoirLevel(self):

        """
        ========================================================================
        ADDRESERVOIRLEVEL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntry("pump", "Reservoir Levels",
                      time, level)



    def addBolus(self, time, bolus):

        """
        ========================================================================
        ADDBOLUS
        ========================================================================
        """

        # Add bolus entry
        self.addEntry("insulin", "Boluses",
                      time, bolus)



    def addTemporaryBasal(self, time, rate, units, duration):

        """
        ========================================================================
        ADDTEMPORARYBASAL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntry("insulin", "Temporary Basals",
                      time, [rate, units, duration])



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a reporter for me
    reporter = Reporter()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
