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
import json
import numpy as np



# USER LIBRARIES
import lib



class Reporter:

    # REPORTER CHARACTERISTICS
    VERBOSE = True



    def addEntries(self, report_name, path, keys, entries):

        """
        ========================================================================
        addEntries
        ========================================================================
        """

        # Give user info
        print "Loading report '" + report_name + "'..."

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Read depth of entries
        d = len(path)

        # Read number of entries
        n = len(keys)

        # Get section of report in which to add entry
        section = report[path[0]]

        for i in range(1, d):
            section = section[path[i]]

        # Look if entry is already in report
        for i in range(n):
            if keys[i] in section:

                # Give user info
                print ("Entry already exists: " + str(keys[i]) + ": " +
                       str(entries[i]))

            # If not, write it down
            else:

                # Give user info
                print "New entry: " + str(keys[i]) + ": " + str(entries[i])

                # Add entry to report
                section[keys[i]] = entries[i]

                # Rewrite report
                with open("Reports/" + report_name, "w") as f:
                    json.dump(report,
                              f,
                              indent = 4,
                              separators = (",", ": "),
                              sort_keys = True)

        # Give user info
        print "Report '" + report_name + "' updated."



    def getEntry(self, report_name, path, key):

        """
        ========================================================================
        GETENTRY
        ========================================================================
        """

        # Give user info
        print "Loading report '" + report_name + "'..."

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Read depth of entry
        d = len(path)

        # Get section of report from which to get entry
        section = report[path[0]]

        for i in range(1, d):
            section = section[path[i]]

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



    def deleteEntries(self, report_name, path):

        """
        ========================================================================
        DELETEENTRIES
        ========================================================================
        """

        # Give user info
        print "Loading report '" + report_name + "'..."

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Read depth of entry
        d = len(path)

        # Get section of report in which to add entry
        section = report[path[0]]

        for i in range(1, d):
            section = section[path[i]]

        # Give user info
        print "Deleting entries..."

        # Delete entries
        section.clear()

        # Rewrite report
        with open("Reports/" + report_name, "w") as f:
            json.dump(report,
                      f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)

        # Give user info
        print ("Entries deleted!")



    def getReport(self, report_name):

        """
        ========================================================================
        GETREPORT
        ========================================================================
        """

        # Load report
        with open("Reports/" + report_name, "r") as f:
            report = json.load(f)

        # Give user info
        print "Report '" + report_name + "' loaded."

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



    def addReservoirLevel(self):

        """
        ========================================================================
        ADDRESERVOIRLEVEL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntries("pump.json", ["Reservoir Levels"],
                        [time], [level])



    def addBolus(self, time, bolus):

        """
        ========================================================================
        ADDBOLUS
        ========================================================================
        """

        # Add bolus entry
        self.addEntries("insulin.json", ["Boluses"],
                        [time], [bolus])



    def addTemporaryBasal(self, time, rate, units, duration):

        """
        ========================================================================
        ADDTEMPORARYBASAL
        ========================================================================
        """

        # Add temporary basal entry
        self.addEntries("insulin.json", ["Temporary Basals"],
                        [time], [[rate, units, duration]])



    def saveCarbRatios(self, ratios):

        """
        ========================================================================
        SAVECARBRATIOS
        ========================================================================
        """

        # Delete previous carb ratios
        self.deleteEntries("profile.json", ["Settings", "Carb Ratios"])

        # Read number of ratios
        n = len(ratios)

        # Numpy array conversion
        ratios = np.array(ratios)

        # Add ratio entries
        self.addEntries("profile.json", ["Settings", "Carb Ratios"],
                        ratios[:, 0], ratios[:, 1].astype(float))



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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
