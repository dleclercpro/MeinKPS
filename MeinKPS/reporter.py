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
# - Overwrite option instead of deleting section completely



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
import json
import numpy as np
import os.path
import datetime



# USER LIBRARIES
import lib



class Reporter:

    # REPORTER CHARACTERISTICS
    VERBOSE = True



    def getReport(self, report_name):

        """
        ========================================================================
        GETREPORT
        ========================================================================
        """

        # Give user info
        print "Loading report '" + report_name + "'..."

        # Check for report existence
        self.verifyReport(report_name)

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Give user info
        print "Report loaded."

        # Return entry for external access
        return report



    def printReport(self, report_name):

        """
        ========================================================================
        PRINTREPORT
        ========================================================================
        """

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Print report entries
        print report



    def verifyReport(self, report_name):

        """
        ========================================================================
        VERIFYREPORT
        ========================================================================
        """

        # Check for report existence
        if not os.path.exists("Reports/" + report_name):

            # Give user info
            print "Report '" + report_name + "' does not exist. Creating it..."

            # Creating new empty report
            with open("Reports/" + report_name, "w") as f:
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



    def deleteSection(self, report_name, path):

        """
        ========================================================================
        DELETESECTION
        ========================================================================
        """

        # Load report
        report = self.getReport(report_name)

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
            with open("Reports/" + report_name, "w") as f:
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



    def getEntry(self, report_name, path, key):

        """
        ========================================================================
        GETENTRY
        ========================================================================
        """

        # Load report
        report = self.getReport(report_name)

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



    def addEntries(self, report_name, path, keys, entries, overwrite = False):

        """
        ========================================================================
        addEntries
        ========================================================================
        """

        # Load report
        report = self.getReport(report_name)

        # Make sure keys and entries are of array type
        if type(keys) is not list:
            keys = [keys]
            entries = [entries]

        # Read number of entries
        n = len(keys)

        # Load report section
        section = self.verifySection(report, path, True)

        # If overwrite option was selected, clear report section
        if overwrite:

            # Give user info
            print ("Overwrite option was selected: clearing " +
                   "report section...")

            # If section is on first level, do not delete whole report!
            if len(path) == 0:
                for i in range(n):
                    del section[keys[i]]

            else:
                section.clear()

        # Initialize variable to keep track of report modifications
        modified = False

        # Look if entry is already in report
        for i in range(n):
            if keys[i] in section:

                # Give user info
                print ("Entry already exists: " + str(keys[i]) + " - " +
                       str(entries[i]))

            # If not, write it down
            else:
                if i == 0:

                    # Give user info
                    print ("Writing down following entries under " +
                           str(path) + ":")

                # Give user info
                print str(keys[i]) + " - " + str(entries[i])

                # Add entry to report
                section[keys[i]] = entries[i]

                # Rewrite report
                with open("Reports/" + report_name, "w") as f:
                    json.dump(report,
                              f,
                              indent = 4,
                              separators = (",", ": "),
                              sort_keys = True)

                # Update modifications variable
                modified = True

        # If report was modified, tell user
        if modified:
            # Give user info
            print "Report '" + report_name + "' was updated."



    def addReservoirLevel(self, t, level):

        """
        ========================================================================
        ADDRESERVOIRLEVEL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntries("pump.json", ["Reservoir Levels"], t, level)



    def addBoluses(self, t, boluses):

        """
        ========================================================================
        ADDBOLUSES
        ========================================================================
        """

        # Give user info
        print "Storing boluses to report: 'insulin.json'..."

        # Add bolus entry
        self.addEntries("insulin.json", ["Boluses"], t, boluses)



    def addTemporaryBasal(self, t, rate, units, duration):

        """
        ========================================================================
        ADDTEMPORARYBASAL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntries("insulin.json", ["Temporary Basals"],
                                         t, [rate, units, duration])



    def saveInsulinSensitivityFactors(self, t, factors, units):

        """
        ========================================================================
        SAVEINSULINSENSITIVITYFACTORS
        ========================================================================
        """

        # Read number of factors
        n = len(factors)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "ISF (" + units + ")"],
                                         t, factors, True)



    def saveCarbSensitivityFactors(self, t, factors, units):

        """
        ========================================================================
        SAVECARBSENSITIVITYFACTORS
        ========================================================================
        """

        # Read number of factors
        n = len(factors)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "CSF (" + units + ")"],
                                         t, factors, True)



    def saveBloodGlucoseTargets(self, t, targets, units):

        """
        ========================================================================
        SAVEBLOODGLUCOSETARGETS
        ========================================================================
        """

        # Read number of factors
        n = len(targets)

        # Write down (and overwrite if necessary) factor entries into report
        self.addEntries("profile.json", ["Settings", "BG Targets (" +
                                         units + ")"], t, targets, True)



    def savePowerTime(self):

        """
        ========================================================================
        SAVEPOWERTIME
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
        boluses_t = [None] * n

        # Initialize looping variable
        i = 0

        # Read bolus report
        for entry_key in report["Boluses"]:

            # Extend bolus vectors
            boluses[i] = report["Boluses"][entry_key]
            boluses_t[i] = lib.getTime(entry_key)

            # Update looping variable
            i += 1

        # Convert bolus vectors to numpy arrays
        boluses = np.array(boluses)
        boluses_t = np.array(boluses_t)

        # Get sorted index of bolus vectors according to growing time order
        indices = np.argsort(boluses_t)

        # Sort bolus vectors
        boluses = boluses[indices]
        boluses_t = boluses_t[indices]

        # Reconvert bolus time to a string
        for i in range(n):

            # Convert datetime object
            boluses_t[i] = lib.getTime(boluses_t[i])

        # Store last bolus
        self.last_bolus = boluses[-1]
        self.last_bolus_t = boluses_t[-1]

        # Give user info
        print "Last bolus: " + str(self.last_bolus) + "U (" + \
              self.last_bolus_t + ")"



    def readLastBG(self):

        """
        ========================================================================
        READLASTBG
        ========================================================================
        """

        # Load BG report
        report = self.getReport("BG.json")

        # Get number of entries
        n = len(report)

        # Initialize BG vectors
        BG = [None] * n
        BG_t = [None] * n

        # Initialize looping variable
        i = 0

        # Read BG report
        for entry_key in report:

            # Extend BG vectors
            BG[i] = report[entry_key]
            BG_t[i] = lib.getTime(entry_key)

            # Update looping variable
            i += 1

        # Convert BG vectors to numpy arrays
        BG = np.array(BG)
        BG_t = np.array(BG_t)

        # Get sorted index of BG vectors according to growing time order
        indices = np.argsort(BG_t)

        # Sort BG vectors
        BG = BG[indices]
        BG_t = BG_t[indices]

        # Reconvert BG time to a string
        for i in range(n):

            # Convert datetime object
            BG_t[i] = lib.getTime(BG_t[i])

        # Store last BG
        self.last_BG = BG[-1]
        self.last_BG_t = BG_t[-1]

        # Give user info
        print "Last BG: " + str(self.last_BG) + " mmol/l (" + \
              self.last_BG_t + ")"



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

    # Read last BG
    #reporter.readLastBG()

    # Add reservoir level
    #reporter.addReservoirLevel("05.02.2017 - 23:42:05", 195)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
