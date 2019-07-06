#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    reporter

    Author:   David Leclerc

    Version:  0.1

    Date:     30.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TO-DO'S
# - Disconnect Pi safely (do not break JSON files)
# - When adding an entry with the overwrite argument, only said entry can be
#   overwritten and not the whole section (see BG Targets)?



# LIBRARIES
import json
import datetime



# USER LIBRARIES
import lib
import path
import logger
import errors



# Instanciate logger
Logger = logger.Logger("reporter.py", level = "DEBUG")



# CONSTANTS
SRC = path.Path("Reports")
LOADING_ATTEMPTS = 2



# CLASSES
class Reporter:

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define source path
        self.src = path.Path("Reports")

        # Define export path
        self.export = path.Path("Reports/Export")



    def getDates(self, name):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETDATES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Get corresponding date objects for each dated report.
        """

        # Scan for all possible report directories
        directories = self.src.scan(name)

        # Convert paths to dates
        if directories:
            return [path.toDate(d) for d in directories]

        # Info
        Logger.debug("No dated report found for '" + name + "'.")



    def getReport(self, name, date = None, directory = None, touch = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETREPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Get report object.
        """

        # Default directory
        if directory is None:

            # Define source
            directory = self.src

        # Given date
        if date is not None:

            # Add date to path
            directory.expand(lib.formatDate(date))

        # If report can be generated in case it doesn't exist yet
        if touch:

            # Touch it
            directory.touch(name)

        # Generate new report
        report = Report(name, directory, date)

        # Load its JSON
        report.load()

        # Return it
        return report



    def getSection(self, report, branch, make = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETSECTION
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read section depth
        d = len(branch)

        # First level section is whole report
        section = report.json

        # Info
        Logger.debug("Getting section: " + " > ".join(["."] + branch))

        # Loop through whole report to find section
        for i in range(d):

            # Get current branch
            b = branch[i]

            # Check if section report exists
            if b not in section:

                # Make section if desired
                if make:
                
                    # Info
                    Logger.debug("Section not found. Making it...")

                    # Create it
                    section[b] = {}

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[b]

        # Info
        Logger.debug("Section found.")

        # Show section
        Logger.debug(lib.JSONize(section))

        # Return section
        return section



    def getEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Getting entry: " + str(key))

        # Look if entry exists
        if key in section:

            # Get corresponding value
            value = section[key]

            # Info
            Logger.debug("Entry found.")

            # Show value
            Logger.debug(lib.JSONize(value))

            # Return it for external access
            return value

        # Otherwise
        else:

            # Info
            Logger.debug("No matching entry found.")

            # Return nothing
            return None



    def addEntry(self, section, entry, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding entry:")

        # Show entry
        Logger.debug(lib.JSONize(entry))

        # Destructure entry
        key, value = entry.items()[0]

        # Look if entry is already in report
        if key in section and not overwrite:

            # Info
            Logger.debug("Entry already exists.")

            # Entry was not modified
            return False

        # If not, write it down
        else:

            # Add entry to report
            section[key] = value

            # If overwritten
            if overwrite:

                # Info
                Logger.debug("Entry overwritten.")

            # Otherwise
            else:

                # Info
                Logger.debug("Entry added.")

            # Entry was modified
            return True



    def deleteEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETEENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Deleting entry: " + str(key))

        # If it does, delete it
        if key in section:

            # Delete entry
            del section[key]

            # Info
            Logger.debug("Entry deleted.")

        else:

            # Info
            Logger.debug("No such entry.")



    def add(self, name, branch, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # No entries
        if len(entries) == 0:

            # Info
            Logger.debug("No entries to add.")

            # Exit
            return

        # Get first value
        zero = min(entries)

        # If entries are dated
        if type(zero) is datetime.datetime:

            # Initialize date
            date = zero.date()

        # Otherwise
        else:

            # Initialize date
            date = None

        # Load report
        report = self.getReport(name, date)

        # Get section
        section = self.getSection(report, branch, True)

        # Loop through entries
        for key in sorted(entries):

            # Get value
            value = entries[key]

            # If date
            if date is not None:

                # If date is different than previous one
                if key.date() != date:

                    # Update date
                    date = key.date()

                    # Store last loaded report
                    report.store()

                    # Load new report
                    report = self.getReport(name, date)

                    # Get section
                    section = self.getSection(report, branch, True)

                # Format key
                key = lib.formatTime(key)

            # Add entry
            self.addEntry(section, {key: value}, overwrite)

        # Store report
        report.store()



    def get(self, name, branch, key = None, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report
        report = self.getReport(name, date, None, False)

        # Get section
        section = self.getSection(report, branch)

        # If key was provided
        if key is not None:

            # If key is a date
            if date is not None:

                # Format key
                key = lib.formatTime(key)

            # Get corresponding value
            entry = self.getEntry(section, key)

            # Return it
            return entry

        # Otherwise
        else:

            # Return section
            return section



    def getRecent(self, now, name, branch, n = 2, strict = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETRECENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current date
        today = now.date()

        # If search is strict
        if strict:

            # Compute oldest day to look for
            oldest = today - datetime.timedelta(days = n - 1)

        # Get dates of existing corresponding reports and exclude future ones
        dates = [d for d in self.getDates(name) if d <= today]

        # Initialize dict for merged entries
        entries = {}

        # Initialize number of reports merged
        N = 0

        # Loop on dates, starting with the latest one
        for date in sorted(dates, reverse = True):

            # Check if enough recent reports were fetched
            if N == n or strict and date < oldest:

                # Quit
                break

            # Try getting section
            try:

                # Load report
                report = self.getReport(name, date, None, False)

                # Get section
                section = self.getSection(report, branch)

                # If section not empty
                if section:

                    # Merge entries
                    entries = lib.mergeDicts(entries, section)

                    # Update number of reports merged
                    N += 1

            # In case of failure
            except:

                # Ignore
                pass

        # Return entries
        return entries



    def increment(self, name, branch, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try reading value
        n = self.get(name, branch, key)

        # If non-existent
        if n is None:

            # Set to zero
            n = 0

        # Update value
        self.add(name, branch, {key: n + 1}, True)






class Report(object):

    """
    Report object based on given JSON file.
    """

    def __init__(self, name = None, date = None, directory = SRC, json = {}):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize report attributes
        self.name = name
        self.directory = directory
        self.date = date
        self.json = json



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Reset report's JSON.
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset JSON
        self.json = {}
        self.store()



    def merge(self, json):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MERGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Merge report's JSON with given JSON.
        """

        # Info
        Logger.debug("Updating report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Update JSON
        self.json = lib.mergeDicts(self.json, json)



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Load content of report's JSON file.
        """

        # Info
        Logger.debug("Loading report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Loading
        for i in range(LOADING_ATTEMPTS):

            # Info
            Logger.debug("Loading attempt: " + str(i + 1) + "/" +
                                               str(LOADING_ATTEMPTS))

            # Try opening report
            try:

                # Open report
                with open(self.directory.path + self.name, "r") as f:

                    # Load JSON
                    self.json = json.load(f)

                # Success
                Logger.debug("Report loaded.")
                return

            # In case of error
            except:

                # Reset report
                self.reset()
                self.store()



    def store(self, directory = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Store current JSON to report's JSON file.
        """

        # Info
        Logger.debug("Storing report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # If no directory given
        if directory is None:
            directory = self.directory

        # Make sure report exists
        directory.touch(self.name)

        # Rewrite report
        with open(directory.path + self.name, "w") as f:

            # Dump JSON
            json.dump(self.json, f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show report
        Logger.debug(lib.JSONize({"Name": self.name,
                                  "Directory": self.directory.path,
                                  "Date": self.date,
                                  "JSON": self.json}))



    def get(self, branch):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Get value in report according to given series of keys (aka branch).
        """

        # Test branch
        if isBranchBroken(branch):
            raise errors.BrokenBranch(str(branch))

        # Initialize json
        json = self.json

        # Dive in JSON according to branch
        for key in branch:

            # Key exists
            if key in json:

                # Last key of branch (actual key of entry)
                if key == branch[-1]:
                    return json[key]

                # Key leads to another dict: dive deeper
                elif type(json[key]) is dict:
                    json = json[key]

        # Branch is invalid
        raise errors.InvalidBranch(self.name, str(branch))



    def add(self, branch, value, overwrite = False, touch = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Add entry to report at the tip of given branch. Touch will allow
            to create parts of the branch that could eventually be missing,
            while overwrite allows to wipe and rewrite preexisting entries/
            branches.
        """

        # Test branch
        if isBranchBroken(branch):
            raise errors.BrokenBranch(str(branch))

        # Overwrite is stronger than touch (if overwriting allowed, creating new
        # parts of report should be also allowed)
        if overwrite:
            touch = True

        # Initialize JSON
        json = self.json

        # Dive in JSON according to branch
        for key in branch:

            # Last key of branch (actual key of entry)
            if key == branch[-1]:
                
                # Key does not exist or can be overwritten
                if not key in json or overwrite:
                    json[key] = value
                    return

                # Otherwise
                else:
                    raise errors.NoOverwritingAdd(self.name, str(branch))

            # Otherwise
            else:
                
                # Key is missing
                if not key in json:

                    # Can touch it
                    if touch:
                        json[key] = {}

                    # Otherwise
                    else:
                        raise errors.NoTouchingAdd(self.name, str(branch))

                # Key exists, but doesn't lead to a dict
                if type(json[key]) is not dict:

                    # However, overwriting is allowed
                    if overwrite:
                        json[key] = {}

                    # Otherwise
                    else:
                        raise errors.NoOverwritingAdd(self.name, str(branch))

                # Dive deeper in JSON
                json = json[key]

        # Branch is invalid
        raise errors.InvalidBranch(self.name, str(branch))



    def delete(self, branch):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Delete entry from report at the tip of given branch.
        """

        # Test branch
        if isBranchBroken(branch):
            raise errors.BrokenBranch(str(branch))

        # Initialize json
        json = self.json

        # Dive in JSON according to branch
        for key in branch:

            # Key exists
            if key in json:

                # Last key of branch (actual key of entry)
                if key == branch[-1]:
                    del json[key]
                    return

                # Key leads to another dict: dive deeper
                elif type(json[key]) is dict:
                    json = json[key]

        # Branch is invalid
        raise errors.InvalidBranch(self.name, str(branch))



    def increment(self, branch):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Increment the tip of the branch by one.
        """

        # Try reading value
        n = self.get(branch)

        # Make sure it is a number
        if not type(n) is int:
            raise TypeError("Can only increment integers. Found: " + str(n))

        # Update value
        self.add(branch, n + 1, True)






class BGReport(Report):

    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(BGReport, self).__init__("BG.json", date)



class PumpReport(Report):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(PumpReport, self).__init__("pump.json")



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset to default
        self.json = {
            "BG Targets": {},
            "Basal Profile (A)": {},
            "Basal Profile (B)": {},
            "Basal Profile (Standard)": {},
            "CSF": {},
            "ISF": {},
            "Power": "1970.01.01 - 00:00:00",
            "Properties": {
                "Firmware": "",
                "Model": 0
            },
            "Settings": {
                "DIA": 0,
                "Max Basal": 0,
                "Max Bolus": 0
            },
            "Units": {
                "BG": "mmol/L",
                "Carbs": "g",
                "TB": "U/h"
            }
        }

        # Store it
        self.store()



class CGMReport(Report):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(CGMReport, self).__init__("CGM.json")



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset to default
        self.json = {
            "Clock Mode": "24h",
            "Language": "English",
            "Transmitter ID": "",
            "Units": "mmol/L"
        }

        # Store it
        self.store()



class StickReport(Report):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(StickReport, self).__init__("stick.json")



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset to default
        self.json = {
            "Frequency": [
                    917.5,
                    "1970.01.01 - 00:00:00"
                ]
        }

        # Store it
        self.store()



class TreatmentsReport(Report):

    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(TreatmentsReport, self).__init__("treatments.json", date)



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset to default
        self.json = {
            "Boluses": {},
            "IOB": {},
            "Net Basals": {}
        }

        # Store it
        self.store()



class HistoryReport(Report):

    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(HistoryReport, self).__init__("history.json", date)



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset to default
        self.json = {
            "CGM": {
                "Battery Levels": {},
                "Calibrations": {},
                "Sensor Statuses": {}
            },
            "Pump": {
                "Battery Levels": {},
                "Reservoir Levels": {}
            }
        }

        # Store it
        self.store()



# FUNCTIONS
def isBranchBroken(branch):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ISBRANCHBROKEN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        A branch is a list of keys, which lead to a value in a dict. It should
        never be empty, and all its values should be strings.
    """

    return len(branch) == 0 or not all([type(b) is str for b in branch])



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now() - datetime.timedelta(days = 0)

    # Get pump report
    pumpReport = PumpReport()
    pumpReport.load()
    pumpReport.get(["Settings", "Max Bolus"])
    pumpReport.add(["Settings", "Max Bolus", "Test"], 0, True)
    pumpReport.increment(["Settings", "Max Bolus", "Test"])
    pumpReport.show()
    #pumpReport.delete(["Settings", "Max Bolus", "Test"])
    #pumpReport.show()
    pumpReport.add(["Settings", "Max Bolus"], 35.0, True)
    pumpReport.show()

    # Get basal profile from pump report
    #reporter.get("pump.json", [], "Basal Profile (Standard)")

    # Get BGs of today
    #reporter.get("BG.json", [], None, now)

    # Get most recent data
    #json = reporter.getRecent(now, "BG.json", [], 3, True)

    # Print data
    #print lib.JSONize(json)

    # Increment loop
    #reporter.increment("loop.json", ["Status"], "N")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()