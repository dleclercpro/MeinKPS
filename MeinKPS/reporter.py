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

# LIBRARIES
import datetime
import json
import os.path
import sys



# USER LIBRARIES
import lib



class Reporter:

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Set source path to reports
        self.source = "/home/pi/MeinKPS/MeinKPS/Reports/"

        # Initialize looked up sections
        self.section = [] # Should not be equal to last one!
        self.lastSection = None



    def load(self, report):

        """
        ========================================================================
        LOAD
        ========================================================================
        """

        # Store report's name
        self.name = report

        # Give user info
        print "Loading '" + self.name + "'..."

        # Check if report exists. If not, generate it.
        if not os.path.exists(self.source + self.name):

            # Give user info
            print "'" + self.name + "' does not exist. Creating it..."

            # Creating new empty report
            with open(self.source + self.name, "w") as f:
                json.dump({}, f)

        # Load report
        with open(self.source + self.name, "r") as f:
            self.report = json.load(f)

        # Give user info
        print "'" + self.name + "' loaded."



    def save(self):

        """
        ========================================================================
        SAVE
        ========================================================================
        """

        # Give user info
        print "Updating '" + self.name + "'..."

        # Rewrite report
        with open(self.source + self.name, "w") as f:
            json.dump(self.report,
                      f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)

        # Give user info
        print "'" + self.name + "' updated."



    def delete(self, path, key):

        """
        ========================================================================
        DELETE
        ========================================================================
        """

        # Load report section
        self.getSection(path)

        # Give user info
        print ("Attempting to delete entry: " + self.formatPath(path) + " > " +
               str(key))

        # If it does, delete it
        if key in self.section:

            # Delete entry
            del self.section[key]

            # Give user info
            print ("Entry deleted.")

            # Rewrite report
            self.save()

        else:

            # Give user info
            print ("No such entry: no need to delete.")



    def show(self):

        """
        ========================================================================
        SHOW
        ========================================================================
        """

        # Print report entries
        print self.report



    def formatPath(self, path):

        """
        ========================================================================
        FORMATPATH
        ========================================================================
        """

        # Format path
        return " > ".join(["."] + path)



    def getSection(self, path, create = False):

        """
        ========================================================================
        GETSECTION
        ========================================================================
        """

        # Make sure section path is of list type!
        if type(path) is not list:

            # Give user output
            sys.exit("Make sure to input paths as lists, otherwise finding " +
                     "corresponding section won't work. Exiting...")

        # First level section is whole report
        self.section = self.report

        # Read section depth: if it is equal to 0, the following loop is
        # skipped and the section corresponds to the whole report
        d = len(path)

        # Give user info
        print "Attempting to find section: " + self.formatPath(path)

        # Loop through whole report to find section
        for i in range(d):

            # Check if section report exists
            if path[i] not in self.section:

                # Create report if desired
                if create:
                
                    # Give user info
                    print "Section not found. Creating it..."

                    # Create missing report section
                    self.section[path[i]] = {}

                else:

                    # Give user info
                    sys.exit("No matching section found. Exiting...")

            # Update section
            self.section = self.section[path[i]]

        # Give user info
        print "Section found."



    def getEntry(self, path, key):

        """
        ========================================================================
        GETENTRY
        ========================================================================
        """

        # Load report section
        self.getSection(path)

        # Give user info
        print ("Attempting to find entry: " + self.formatPath(path) + " > " +
               str(key))

        # Look if entry exists
        if key in self.section:

            # Get entry matching the key
            entry = self.section[key]

            # Give user info
            print "Entry found: " + json.dumps(entry)

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."



    def addEntry(self, path, key, entry):

        """
        ========================================================================
        ADDENTRY
        ========================================================================
        """

        # FIXME
        # Look if trying to add entry in an already found section
        #if self.section != self.lastSection:

        # Load report section
        self.getSection(path, True)

        # Give user info
        print ("Attempting to add entry: " + self.formatPath(path) + " > " +
               str(key) + " > " + json.dumps(entry))

        # Look if entry is already in report
        if key in self.section:

            # Give user info
            print "Entry already exists."

        # If not, write it down
        else:

            # Add entry to report
            self.section[key] = entry

            # Give user info
            print "Entry added."

            # Rewrite report
            self.save()

        # Store last section in which entries were added
        self.lastSection = self.section



    def addBatteryLevel(self, t, level):

        """
        ========================================================================
        ADDBATTERYLEVEL
        ========================================================================
        """

        # Give user info
        print "Adding battery level to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Add entry
        self.addEntry(["Battery Levels"], t, level)



    def addReservoirLevel(self, t, level):

        """
        ========================================================================
        ADDRESERVOIRLEVEL
        ========================================================================
        """

        # Give user info
        print "Adding reservoir level to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Add entry
        self.addEntry(["Reservoir Levels"], t, level)



    def addBoluses(self, t, boluses):

        """
        ========================================================================
        ADDBOLUSES
        ========================================================================
        """

        # Give user info
        print "Adding boluses to report: 'treatments.json'..."

        # Load report
        self.load("treatments.json")

        # Read number of entries to add
        n = len(boluses)

        # Add entries
        for i in range(n):
            self.addEntry(["Boluses"], t[i], boluses[i])



    def addCarbs(self, t, carbs):

        """
        ========================================================================
        ADDCARBS
        ========================================================================
        """

        # Give user info
        print "Adding carbs to report: 'treatments.json'..."

        # Load report
        self.load("treatments.json")

        # Read number of entries to add
        n = len(carbs)

        # Add entries
        for i in range(n):
            self.addEntry(["Carbs"], t[i], carbs[i])



    def addTBR(self, t, rate, units, duration):

        """
        ========================================================================
        ADDTBR
        ========================================================================
        """

        # Give user info
        print "Adding TBR to report: 'treatments.json'..."

        # Load report
        self.load("treatments.json")

        # Add entry
        self.addEntry(["Temporary Basals"], t, [rate, units, duration])



    def storePowerTime(self, t):

        """
        ========================================================================
        STOREPOWERTIME
        ========================================================================
        """

        # Give user info
        print "Adding pump radio's last power up to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Remove old entry
        self.delete([], "Power")

        # Add entry
        self.addEntry([], "Power", t)



    def storeModel(self, model):

        """
        ========================================================================
        STOREMODEL
        ========================================================================
        """

        # Give user info
        print "Adding pump model to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Remove old entry
        self.delete([], "Model")

        # Add entry
        self.addEntry([], "Model", model)



    def storeFirmware(self, firmware):

        """
        ========================================================================
        STOREFIRMWARE
        ========================================================================
        """

        # Give user info
        print "Adding pump firmware to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Remove old entry
        self.delete([], "Firmware")

        # Add entry
        self.addEntry([], "Firmware", firmware)



    def storeSettings(self, settings):

        """
        ========================================================================
        STORESETTINGS
        ========================================================================
        """

        # Give user info
        print "Adding pump settings to report: 'profile.json'..."

        # Load report
        self.load("profile.json")

        # Remove old entry
        self.delete([], "Settings")

        # Add entry
        self.addEntry([], "Settings", settings)



    def storeISF(self, t, factors, units):

        """
        ========================================================================
        STOREISF
        ========================================================================
        """

        # Give user info
        print "Adding ISF to report: 'profile.json'..."

        # Load report
        self.load("profile.json")

        # Define path
        path = ["ISF (" + units + ")"]

        # Remove old entries
        self.delete([], path[0])

        # Read number of entries to add (if 0, no entries will be added)
        n = len(factors)

        # Add entries
        for i in range(n):
            self.addEntry(path, t[i], factors[i])



    def storeCSF(self, t, factors, units):

        """
        ========================================================================
        STORECSF
        ========================================================================
        """

        # Give user info
        print "Adding CSF to report: 'profile.json'..."

        # Load report
        self.load("profile.json")

        # Define path
        path = ["CSF (" + units + ")"]

        # Remove old entries
        self.delete([], path[0])

        # Read number of entries to add (if 0, no entries will be added)
        n = len(factors)

        # Add entries
        for i in range(n):
            self.addEntry(path, t[i], factors[i])



    def storeBGTargets(self, t, targets, units):

        """
        ========================================================================
        STOREBGTargets
        ========================================================================
        """

        # Give user info
        print "Adding BG targets to report: 'profile.json'..."

        # Load report
        self.load("profile.json")

        # Define path
        path = ["BG Targets (" + units + ")"]

        # Remove old entries
        self.delete([], path[0])

        # Read number of entries to add (if 0, no entries will be added)
        n = len(targets)

        # Add entries
        for i in range(n):
            self.addEntry(path, t[i], targets[i])



    def storeBGU(self, BGU):

        """
        ========================================================================
        STOREBGU
        ========================================================================
        """

        # Give user info
        print "Adding pump BG units to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Remove old entry
        self.delete([], "BG Units")

        # Add entry
        self.addEntry([], "BG Units", BGU)



    def storeCU(self, CU):

        """
        ========================================================================
        STORECU
        ========================================================================
        """

        # Give user info
        print "Adding pump carb units to report: 'pump.json'..."

        # Load report
        self.load("pump.json")

        # Remove old entry
        self.delete([], "Carb Units")

        # Add entry
        self.addEntry([], "Carb Units", CU)



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
