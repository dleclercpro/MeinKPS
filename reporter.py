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
# - Scan for corrupted directory/file structure (e.g. should this report be
#   there?)



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
PATH_REPORTS = path.Path("Reports")
PATH_EXPORTS = path.Path("Exports")
LOADING_ATTEMPTS = 2



# CLASSES
class Report(object):

    """
    Report object based on given JSON file.
    """

    # Define report name
    name = None



    def __init__(self, date = None, directory = PATH_REPORTS, json = {}):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Initialize report based on its name, its eventual date, its source
            directory, and its JSON content.
        """

        # Test path
        if not isinstance(directory, path.Path):
            raise TypeError("Need path.")

        # Initialize report attributes
        self.date = date
        self.json = json

        # Create new path object for report
        self.directory = path.Path(directory.path)

        # Dated report
        if date is not None:
            self.directory.expand(lib.formatDate(date))



    def __repr__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            REPR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            String representation of report.
        """

        # Prepare string
        string = "'" + self.name + "'"

        # Add date
        if self.date is not None:
            string += " (" + lib.formatDate(self.date) + ")"

        # Return for printing
        return string



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            String representation of report's content.
        """

        # Return for printing
        return lib.JSONize({
            "Name": self.name,
            "Directory": self.directory.path,
            "Date": self.date,
            "JSON": self.json
        })



    def erase(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ERASE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Erase report's content.
        """

        # Info
        Logger.debug("Erasing report: " + repr(self))

        # Erase JSON
        self.json = {}



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Reset report's content and store it.
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

        # Reset JSON
        self.erase()
        self.store()



    def merge(self, report):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MERGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Merge report's JSON with given JSON.
        """

        # Test report
        if not isinstance(report, Report):
            raise TypeError("Need report to merge.")

        # Info
        Logger.debug("Merging " + repr(self) + " with " + repr(report))

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
        Logger.debug("Loading report: " + repr(self))

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



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Store current JSON to report's JSON file.
        """

        # Info
        Logger.debug("Storing report: " + repr(self))

        # Make sure report exists
        self.directory.touch(self.name)

        # Rewrite report
        with open(self.directory.path + self.name, "w") as f:

            # Dump JSON
            json.dump(self.json, f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)



    def get(self, branch = []):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Get value in report according to given series of keys (aka branch).
        """

        # Test branch
        if isBranchBroken(branch):
            raise errors.BrokenBranch(str(branch))

        # Empty branch: return whole report
        if branch == []:
            return self.json

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



    def add(self, value, branch = [], overwrite = False, touch = False):

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

        # Empty branch: replace the whole report
        if branch == []:

            # Value is dict
            if type(value) is dict:

                # Overwriting allowed
                if overwrite:
                    self.json = value
                    return

                # Otherwise
                else:
                    raise errors.NoOverwritingAdd(self.name, str(branch))

            # Otherwise
            else:
                raise TypeError("Cannot replace report's content with a " +
                                "non-dict object.")

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



    def delete(self, branch = []):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Delete entry from report at the tip of given branch.
        """

        # Test branch
        if isBranchBroken(branch):
            raise errors.BrokenBranch(str(branch))

        # Empty branch: erase whole report
        if branch == []:
            self.json = {}
            return

        # Initialize JSON
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

        # Test branch: no empty branch allowed (cannot increment the root of a
        # report's content)
        if isBranchBroken(branch) or branch == []:
            raise errors.BrokenBranch(str(branch))

        # Try reading value
        n = self.get(branch)

        # Make sure it is a number
        if type(n) is not int:
            raise TypeError("Can only increment integers. Found: " + str(n))

        # Update value
        self.add(n + 1, branch, True)






class BGReport(Report):

    # Define report name
    name = "BG.json"



    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(BGReport, self).__init__(date)



class PumpReport(Report):

    # Define report name
    name = "pump.json"



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(PumpReport, self).__init__()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

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

    # Define report name
    name = "CGM.json"



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(CGMReport, self).__init__()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

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

    # Define report name
    name = "stick.json"



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(StickReport, self).__init__()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

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

    # Define report name
    name = "treatments.json"



    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(TreatmentsReport, self).__init__(date)



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

        # Reset to default
        self.json = {
            "Boluses": {},
            "IOB": {},
            "Net Basals": {}
        }

        # Store it
        self.store()



class HistoryReport(Report):

    # Define report name
    name = "history.json"



    def __init__(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(HistoryReport, self).__init__(date)



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

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



class LoopReport(Report):

    # Define report name
    name = "loop.json"



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(LoopReport, self).__init__()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Resetting report: " + repr(self))

        # Reset to default
        self.json = {
            "CGM": {
                "BG": 0,
                "Battery": 0,
                "Calibration": 0,
                "Clock": 0,
                "Firmware": 0,
                "Language": 0,
                "Sensor": 0,
                "Start": 0,
                "Stop": 0,
                "Transmitter": 0,
                "Units": 0
            },
            "Pump": {
                "BG Targets": 0,
                "Basal": 0,
                "Battery": 0,
                "CSF": 0,
                "History": 0,
                "ISF": 0,
                "Model": 0,
                "Reservoir": 0,
                "Settings": 0,
                "Start": 0,
                "Stop": 0,
                "TB": 0,
                "Time": 0
            },
            "Status": {
                "Duration": 0,
                "Export": 0,
                "N": 0,
                "Time": "1970.01.01 - 00:00:00",
                "Upload": 0
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
        A branch is a list of keys, which lead to a value in a dict. All its
        values should be strings.
    """

    return type(branch) is not list or not all([type(b) is str for b in branch])



def getReportDates(reportType, src = PATH_REPORTS):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETREPORTDATES
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Get corresponding date objects for a dated report.
    """

    # Test report
    if not issubclass(reportType, Report):
        raise TypeError("Report class needed.")

    # Scan for reports with same name within given source directory
    directories = src.scan(reportType.name)

    # Convert paths to dates
    if directories:
        return [path.toDate(d) for d in directories]

    # Info
    Logger.debug("No dated report found for '" + reportType.name + "'.")



def getRecent(now, reportType, branch, n = 2, strict = False):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETRECENT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Get the "n" most recent report parts, according to the tip of the given
        branch (this can be the whole report if the branch is an empty list).
                
        If "strict" is true, "n" defines the number of days from today the
        function will try looking back for content. Otherwise, it will try to
        find "n" reports, no matter how old they are.
    """

    # Test report
    if not issubclass(reportType, Report):
        raise TypeError("Report class needed.")

    # Get current date
    today = now.date()
    
    # Initialize oldest possible date
    oldest = datetime.date(1970, 1, 1)

    # Strict search: look up to "n" days before
    if strict:
        oldest = today - datetime.timedelta(days = n - 1)

    # Get dates of reports
    dates = [d for d in getReportDates(reportType) if oldest <= d <= today]
    nDates = len(dates)

    # Not enough reports
    if nDates < n:
        Logger.warning("Could not gather " + str(n) + " most recent reports. " +
                       "Found: " + str(nDates))

        # Update number of reports
        n = nDates

    # Initialize dict for merged JSON
    json = {}

    # Loop on found dates, starting with the latest one
    for date in sorted(dates, reverse = True)[-n:]:

        # Initialize and load report
        report = reportType(date)
        report.load()

        # Merge entries
        json = lib.mergeDicts(json, report.get(branch))

    # Return entries
    return json



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now() - datetime.timedelta(days = 0)

    # Get reports
    reports = {
        "bg": BGReport(now),
        "stick": StickReport(),
        "pump": PumpReport(),
        "cgm": CGMReport(),
        "treatments": TreatmentsReport(now),
        "history": HistoryReport(now),
        "loop": LoopReport(),
    }

    # Load them
    for name in reports:
        reports[name].load()

    reports["pump"].get(["Settings", "Max Bolus"])
    reports["pump"].add(0, ["Settings", "Max Bolus", "Test"], True)
    reports["pump"].increment(["Settings", "Max Bolus", "Test"])
    print reports["pump"]
    reports["pump"].delete(["Settings", "Max Bolus", "Test"])
    print reports["pump"]
    reports["pump"].add(35.0, ["Settings", "Max Bolus"], True)
    print reports["pump"]

    print getReportDates(BGReport)
    print lib.JSONize(getRecent(now, BGReport, [], 4))

    # Get basal profile from pump report
    print reports["pump"].get(["Basal Profile (Standard)"])

    # Get BGs of today
    print lib.JSONize(reports["bg"].get())

    # Get most recent data
    print lib.JSONize(getRecent(now, BGReport, [], 3))

    # Increment loop
    print reports["loop"]
    reports["loop"].increment(["Status", "N"])
    reports["loop"].store()
    print reports["loop"]



# Run this when script is called from terminal
if __name__ == "__main__":
    main()