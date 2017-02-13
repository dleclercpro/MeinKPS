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
# X Create report and/or categories if non-existent
# X Overwrite option instead of deleting section completely



# TERMINOLOGY
# - BGs: Blood glucose [mmol/l]
# - TB: Temporary basal (rate) [U/h]
# - ICF: Insulin to carbs factors [U/(15g)]
# - ISF: Insulin sensitivity factors [(mmol/l)/U]
# - DIA: Duration of insulin action [h]
# - IOB: Insulin on board [U]
# - COB: Carbs on board [g]
# - BGs Maximal Rate: Maximal allowed BGs rate [(mmol/l)/h]
# - BGs Time Interval: Time interval between two BGs readings [m]



# LIBRARIES
import json
import numpy as np
import os.path
import datetime



# USER LIBRARIES
import lib



# CONSTANTS
dirReports = "/home/pi/MeinKPS/MeinKPS/Reports/"



class Reporter:

    # REPORTER CHARACTERISTICS



    def getReport(self, reportName):

        """
        ========================================================================
        GETREPORT
        ========================================================================
        """

        # Give user info
        print "Loading report '" + reportName + "'..."

        # Check for report existence
        self.verifyReport(reportName)

        # Load report
        with open(dirReports + reportName, "r") as f:
            report = json.load(f)

        # Give user info
        print "Report loaded."

        # Return entry for external access
        return report



    def printReport(self, reportName):

        """
        ========================================================================
        PRINTREPORT
        ========================================================================
        """

        # Load report
        with open(dirReports + reportName, "r") as f:
            report = json.load(f)

        # Print report entries
        print report



    def verifyReport(self, reportName):

        """
        ========================================================================
        VERIFYREPORT
        ========================================================================
        """

        # Check for report existence
        if not os.path.exists(dirReports + reportName):

            # Give user info
            print "Report '" + reportName + "' does not exist. Creating it..."

            # Creating new empty report
            with open(dirReports + reportName, "w") as f:
                json.dump({}, f)



    def verifySection(self, report, path, create):

        """
        ========================================================================
        VERIFYSECTION
        ========================================================================
        """

        # Check if section report exists. If not, then create it
        section = report

        # Read section depth
        d = len(path)

        for i in range(0, d):
            if path[i] not in section:

                # Create report if desired
                if create:
                
                    # Give user info
                    print ("Report section '" + path[i] + "' does not exist. " +
                           "Creating it...")

                    # Create missing report section
                    section[path[i]] = {}

                else:

                    # Give user info
                    print "No matching report section found for: " + str(path)

                    # Exit
                    return

            # Actualize section
            section = section[path[i]]

        # Give out section
        return section



    def deleteSection(self, reportName, path):

        """
        ========================================================================
        DELETESECTION
        ========================================================================
        """

        # Load report
        report = self.getReport(reportName)

        # Get section of report in which to add entry
        section = report

        # Check if section exists at all
        section = self.verifySection(report, path, False)

        # Give user info
        print "Attempting to delete section: " + str(path)

        # If it does, delete it
        if section:

            # Load report parent section of the one that has to be deleted
            parent = self.verifySection(report, path[0:-1], False)

            # Delete last section in path
            del parent[path[-1]]

            # Rewrite report
            with open(dirReports + reportName, "w") as f:
                json.dump(report,
                          f,
                          indent = 4,
                          separators = (",", ": "),
                          sort_keys = True)

            # Give user info
            print ("Section deleted!")

        else:

            # Give user info
            print ("No such section: no need to delete!")



    def getEntry(self, reportName, path, key):

        """
        ========================================================================
        GETENTRY
        ========================================================================
        """

        # Load report
        report = self.getReport(reportName)

        # Load report section
        section = self.verifySection(report, path, False)

        # Look if entry exists
        if key in section:

            # Get entry matching the key
            entry = section[key]

            # Give user info
            print "Entry found: " + str(key) + ": " + str(entry)

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."



    def addEntries(self, reportName, path, keys, entries, overwrite = False):

        """
        ========================================================================
        addEntries
        ========================================================================
        """

        # Load report
        report = self.getReport(reportName)

        # Make sure keys and entries are of array type
        if type(keys) is not list:
            keys = [keys]
            entries = [entries]

        # Read number of entries
        n = len(keys)

        # Load report section
        section = self.verifySection(report, path, True)

        # If desired, clear report section
        if overwrite:

            # Give user info
            print "Overwriting option chosen: removing entries..."

            # If section to write only consists in a single entry, only delete
            # said entry and not the whole section!
            if n == 1:
                del section[keys[0]]

            else:
                section.clear()

        # Initialize variable to keep track of report modifications
        modified = False

        # Look if entry is already in report
        for i in range(n):
            if keys[i] in section:

                # Give user info
                print ("Entry already exists: " + str(keys[i]) + " - " +
                       str(section[keys[i]]))

            # If not, write it down
            else:

                # Give user info
                print "New entry: " + str(keys[i]) + " - " + str(entries[i])

                # Add entry to report
                section[keys[i]] = entries[i]

                # Update modifications variable
                modified = True

        # Does report need to be updated?
        if modified:

            # Rewrite report
            with open(dirReports + reportName, "w") as f:
                json.dump(report,
                          f,
                          indent = 4,
                          separators = (",", ": "),
                          sort_keys = True)

            # Give user info
            print "Report '" + reportName + "' was updated."



    def addReservoirLevel(self, t, level):

        """
        ========================================================================
        ADDRESERVOIRLEVEL
        ========================================================================
        """

        # Add reservoir levels (only keep one digit in case of rounding errors)
        self.addEntries("pump.json", ["Reservoir Levels"], t, round(level, 1))



    def addBoluses(self, t, boluses):

        """
        ========================================================================
        ADDBOLUSES
        ========================================================================
        """

        # Give user info
        print "Storing boluses to report: 'insulin.json'..."

        # Add boluses
        self.addEntries("insulin.json", ["Boluses"], t, boluses)



    def addTemporaryBasal(self, t, rate, units, duration):

        """
        ========================================================================
        ADDTEMPORARYBASAL
        ========================================================================
        """

        # Add temporary basal entries
        self.addEntries("insulin.json", ["Temporary Basals"],
                                         t, [rate, units, duration])



    def storeSettings(self, settings):

        """
        ========================================================================
        STORESETTINGS
        ========================================================================
        """

        # Write down max bolus
        self.addEntries("profile.json", ["Settings"], "Max Bolus",
                        settings["Max Bolus"], True)

        # Write down max basal
        self.addEntries("profile.json", ["Settings"], "Max Basal",
                        settings["Max Basal"], True)



    def storeInsulinSensitivityFactors(self, t, factors, units):

        """
        ========================================================================
        STOREINSULINSENSITIVITYFACTORS
        ========================================================================
        """

        # Read number of factors
        n = len(factors)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "ISF (" + units + ")"],
                                         t, factors, True)



    def storeCarbSensitivityFactors(self, t, factors, units):

        """
        ========================================================================
        STORECARBSENSITIVITYFACTORS
        ========================================================================
        """

        # Read number of factors
        n = len(factors)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "CSF (" + units + ")"],
                                         t, factors, True)



    def storeBloodGlucoseTargets(self, t, targets, units):

        """
        ========================================================================
        STOREBLOODGLUCOSETARGETS
        ========================================================================
        """

        # Read number of factors
        n = len(targets)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "BGs Targets (" +
                                         units + ")"], t, targets, True)



    def storePowerTime(self):

        """
        ========================================================================
        STOREPOWERTIME
        ========================================================================
        """

        # Get current time
        now = datetime.datetime.now()

        # Convert time to string
        now = lib.getTime(now)

        # Write down (and overwrite if necessary) last power up time
        self.addEntries("pump.json", [], "Power Up", now, True)






    def readLastBolus(self):

        """
        ========================================================================
        READLASTBOLUS
        ========================================================================
        """

        # Load insulin report
        report = self.getReport("insulin.json")

        # Get number of entries
        n = len(report["Boluses"])

        # Initialize bolus vectors
        boluses = [None] * n
        times = [None] * n

        # Initialize looping variable
        i = 0

        # Read bolus report
        for key in report["Boluses"]:

            # Extend bolus vectors
            boluses[i] = report["Boluses"][key]
            times[i] = lib.getTime(key)

            # Update looping variable
            i += 1

        # Convert bolus vectors to numpy arrays
        boluses = np.array(boluses)
        times = np.array(times)

        # Get sorted index of bolus vectors according to growing time order
        indices = np.argsort(times)

        # Sort bolus vectors
        boluses = boluses[indices]
        times = times[indices]

        # Reconvert bolus time to a string
        for i in range(n):

            # Convert datetime object
            times[i] = lib.getTime(times[i])

        # Store last bolus
        self.lastBolus = boluses[-1]
        self.lastBolusTime = times[-1]

        # Give user info
        print ("Last bolus: " + str(self.lastBolus) + "U (" +
               self.lastBolusTime + ")")



    def readLastBG(self):

        """
        ========================================================================
        READLASTBG
        ========================================================================
        """

        # Load BGs report
        report = self.getReport("BGs.json")

        # Get number of entries
        n = len(report)

        # Initialize BGs vectors
        BGs = [None] * n
        BGTimes = [None] * n

        # Initialize looping variable
        i = 0

        # Read BGs report
        for key in report:

            # Extend BGs vectors
            BGs[i] = report[key]
            BGTimes[i] = lib.getTime(key)

            # Update looping variable
            i += 1

        # Convert BGs vectors to numpy arrays
        BGs = np.array(BGs)
        BGTimes = np.array(BGTimes)

        # Get sorted index of BGs vectors according to growing time order
        indices = np.argsort(BGTimes)

        # Sort BGs vectors
        BGs = BGs[indices]
        BGTimes = BGTimes[indices]

        # Reconvert BGs time to a string
        for i in range(n):

            # Convert datetime object
            BGTimes[i] = lib.getTime(BGTimes[i])

        # Store last BGs
        self.lastBGs = BGs[-1]
        self.lastBGTimes = BGTimes[-1]

        # Give user info
        print ("Last BGs: " + str(self.lastBGs) + " mmol/l (" +
               self.lastBGTimes + ")")



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a reporter for me
    reporter = Reporter()

    # Read last bolus
    #reporter.readLastBolus()

    # Read last BGs
    #reporter.readLastBGs()

    # Add reservoir level
    #reporter.addReservoirLevel("05.02.2017 - 23:42:05", 195)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
