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

# LIBRARIES
import json
import datetime
import os
import sys



# USER LIBRARIES
import lib
import errors



class Reporter:

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define source path
        self.src = Path(os.path.dirname(os.path.realpath(__file__)) + os.sep +
                        "Reports")

        # Define export path
        self.exp = Path(self.src.str + "Recent")

        # Initialize reports
        self.reports = []



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset reports
        self.reports = []



    def new(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NEW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify if report already exists
        try:

            # Try getting report (without loading it!)
            self.getReport(name, date, False)

            # Give user info
            print "Report '" + name + "' (" + str(date) + ") already loaded."

            # Skip
            return False

        # If it fails, then store it
        except errors.NoReport:

            # Generate new report
            self.reports.append(Report(name, path, date, json))

            # Success
            return True



    def load(self, name, dates = None, path = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize number of reports to load
        n = 0

        # No path
        if path is None:

            # Define source
            path = self.src.str

        # No dates
        if dates is None:

            # Generate new report
            if self.new(name, path):

                # Update count
                n += 1

        # Otherwise
        else:

            # Make sure dates are given in list form
            if type(dates) is not list:

                # Convert type
                dates = [dates]

            # Format dates
            dates = [lib.formatDate(d) for d in dates]

            # Make sure dates are sorted out and only appear once
            # This can deal with both list and dict types
            dates = lib.uniqify(dates)

            # Loop on dates
            for d in dates:

                # Generate new report
                if self.new(name, path + d + os.sep, d):

                    # Update count
                    n += 1

        # Load report(s)
        for i in range(n):

            # Get current new report
            report = self.reports[-(i + 1)]

            # Load its JSON
            report.load()



    def unload(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UNLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify if report already exists
        try:

            # Try loading report
            report, i = self.getReport(name, date)

            # Give user info
            print ("Unloading report: " + report.name + " (" +
                   str(report.date) + ")")

            # Delete it using its index
            del self.reports[i]

            # Give user info
            print "Report unloaded."

        # If it fails, then store it
        except errors.NoReport as e:

            # Show error message
            print e.message



    def erase(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ERASE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get report
        report = self.getReport(name, date)[0]

        # Erase report
        report.erase()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Rewrite reports
        for report in self.reports:

            # If report was modified
            if report.modified:

                # Store it
                report.store()



    def export(self, name, json):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Generate temporary report
        report = Report(name, self.exp.str, None, json)

        # Store it
        report.store()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Loop on reports
        for report in self.reports:

            # Show report
            report.show()



    def getDates(self, name):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETDATES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Scan for all possible report paths
        paths = self.src.scan(name)

        # If no possible reports found
        if not paths:

            # Exit
            sys.exit("No dated report found for '" + name + "'.")

        # Initialize dates
        dates = []

        # Loop on paths
        for p in paths:

            # Get date from path
            dates.append(Path(p).date())

        # Return dates
        return dates



    def getReport(self, name, date = None, load = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETREPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If loading necessary
        if load:

            # Give user info
            print ("Getting report: '" + name + "' (" + lib.formatDate(date) +
                   ")")

            # Load report
            self.load(name, date)

        # If date
        if date is not None:

            # If date given as datetime object, format it
            if (type(date) is datetime.datetime or
                type(date) is datetime.date):

                # Get and format date
                date = lib.formatDate(date)

        # Count loaded reports
        n = len(self.reports)

        # Loop through reports
        for i in range(n):

            # Get current report
            report = self.reports[i]

            # Check if names match
            if report.name != name:

                # Skip
                continue

            # Check if dates match
            if report.date != date:

                # Skip
                continue

            # Give user info
            print "Report found."

            # Return report and corresponding index
            return (report, i)

        # Raise error
        raise errors.NoReport(name, date)



    def getSection(self, report, branch, make = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETSECTION
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make sure section branch is of list type
        if type(branch) is not list:

            # Raise error
            raise errors.BadPath

        # Read section depth: if it is equal to 0, the following loop is
        # skipped and the section corresponds to the whole report
        d = len(branch)

        # First level section is whole report
        section = report.json

        # Give user info
        print "Getting section: " + " > ".join(["."] + branch)

        # Loop through whole report to find section
        for i in range(d):

            # Get current branch
            b = branch[i]

            # Check if section report exists
            if b not in section:

                # Make section if desired
                if make:
                
                    # Give user info
                    print "Section not found. Making it..."

                    # Create it
                    section[b] = {}

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[b]

        # Give user info
        print "Section found."

        # Return section
        return section



    def getEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Getting entry: " + str(key)

        # Look if entry exists
        if key in section:

            # Get corresponding value
            value = section[key]

            # Give user info
            print "Entry found."

            # Return entry for external access
            return value

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."

            # Return nothing
            return None



    def addEntry(self, section, entry, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding entry:"

        # Show entry
        lib.printJSON(entry)

        # Decouple entry
        (key, value) = entry.items()[0]

        # Look if entry is already in report
        if key in section and not overwrite:

            # Give user info
            print "Entry already exists."

            # Entry was not modified
            return False

        # If not, write it down
        else:

            # Add entry to report
            section[key] = value

            # If overwritten
            if overwrite:

                # Give user info
                print "Entry overwritten."

            # Otherwise
            else:

                # Give user info
                print "Entry added."

            # Entry was modified
            return True



    def deleteEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETEENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Deleting entry: " + str(key)

        # If it does, delete it
        if key in section:

            # Delete entry
            del section[key]

            # Give user info
            print "Entry deleted."

        else:

            # Give user info
            print "No such entry."



    def increment(self, name, branch, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get value
        n = self.get(name, branch, key)

        # Update value
        self.add(name, branch, {key: n + 1}, True)



    def add(self, name, branch, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get first value
        first = min(entries)

        # If entries are dated
        if type(first) is datetime.datetime:

            # Initialize date
            date = first

        # Otherwise
        else:

            # Initialize date
            date = None

        # Get it
        report = self.getReport(name, date)[0]

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

                    # Get report
                    report = self.getReport(name, date)[0]

                    # Get section
                    section = self.getSection(report, branch, True)

                # Format key
                key = lib.formatTime(key)

            # Add entry
            if self.addEntry(section, {key: value}, overwrite):

                # If report was modified
                report.modified = True

        # Store modified reports
        self.store()



    def get(self, name, branch, key = None, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If key is dated
        if type(key) is datetime.datetime:

            # Get date
            date = key.date()

        # Get it
        report = self.getReport(name, date)[0]

        # Get section
        section = self.getSection(report, branch)

        # If key was provided
        if key is not None:

            # Format key
            key = lib.formatTime(key)

            # Return corresponding value
            return self.getEntry(section, key)

        # Otherwise
        else:

            # Return section
            return section



    def getRecent(self, name, branch, n = 2):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETRECENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get dates of existing corresponding reports
        dates = self.getDates(name)

        # Initialize dict for merged entries
        entries = {}

        # Initialize number of reports merged
        N = 0

        # Loop on dates, starting with the latest one
        for date in sorted(dates, reverse = True):

            # Check if enough recent reports were fetched
            if N == n:

                # Quit
                break

            # Get report
            report = self.getReport(name, date)[0]

            # Try getting section
            try:

                # Get section
                section = self.getSection(report, branch)

                # If section not empty
                if section:

                    # Give user info
                    print "Merging '" + report.name + "' (" + report.date + ")"

                    # Merge entries
                    entries = lib.mergeDict(entries, section)

                    # Update number of reports merged
                    N += 1

            # In case of failure
            except Exception as e:

                # Show error message
                print e.message

        # Give user info
        print "Merged entries for " + str(N) + " most recent report(s):"

        # Show entries
        lib.printJSON(entries)

        # Return entries
        return entries



class Report:

    def __init__(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize report attributes
        self.name = name
        self.path = path
        self.date = date
        self.json = json
        self.modified = False



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Resetting report: '" + self.name + "' (" + str(self.date) + ")"

        # Reset JSON
        self.json = {}



    def update(self, json):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Updating report: '" + self.name + "' (" + str(self.date) + ")"

        # Update JSON
        self.json = json

        # Store it
        self.store()



    def erase(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ERASE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Erasing report: '" + self.name + "' (" + str(self.date) + ")"

        # Reset JSON
        self.reset()

        # Store it
        self.store()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Loading report: '" + self.name + "' (" + str(self.date) + ")"

        # Make sure report exists
        Path(self.path).touch(self.name)

        # Open report
        with open(self.path + self.name, "r") as f:

            # Load JSON
            self.json = json.load(f)

        # Give user info
        print "Report loaded."



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing report: '" + self.name + "' (" + str(self.date) + ")"

        # Make sure report exists
        Path(self.path).touch(self.name)

        # Rewrite report
        with open(self.path + self.name, "w") as f:

            # Dump JSON
            json.dump(self.json, f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)

        # Reset modified boolean
        self.modified = False



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show report
        lib.printJSON({"Name": self.name,
                       "Path": self.path,
                       "Date": self.date,
                       "JSON": self.json,
                       "Modified": self.modified})



class Path:

    def __init__(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize string
        self.str = None

        # Initialize list
        self.list = None

        # If input is string
        if type(path) is str:

            # Store it
            self.str = path

        # If it is list
        elif type(path) is list:

            # Store it
            self.list = path

        # Normalize path
        self.norm()

        # Compute path depth
        self.depth = len(self.list)



    def norm(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If list given
        if self.list is not None:

            # Merge it
            self.str = self.merge()

        # Normalize string
        self.str = os.path.abspath(self.str) + os.sep

        # Split it
        self.list = self.split()



    def split(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SPLIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Split path
        return [p for p in self.str.split(os.sep) if p != ""]



    def merge(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MERGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: The first slash might only work for Linux.
        """

        # Merge path
        return os.sep + os.sep.join(self.list)



    def date(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize date
        date = []

        # Get path and remove last slash
        path = os.path.split(self.str)[0]

        # Loop 3 directories up to get corresponding date
        for i in range(3):

            # Split path
            path, file = os.path.split(path)

            # Add date component
            date.append(int(file))

        # Reverse date
        date.reverse()

        # Return datetime object
        return datetime.datetime(*date)



    def touch(self, file = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TOUCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current path
        path = Path(self.list[:n])

        # Stringify it
        path = path.str

        # Look for path
        if n <= self.depth:

            # Show current path
            #print path

            # If it does not exist
            if not os.path.exists(path):

                # Give user info
                print "Making path '" + path + "'..."

                # Make it
                os.makedirs(path)

            # Contine looking
            self.touch(file, n + 1)

        # Look for file
        elif file is not None:

            # Complete path with filename
            path += file

            # If it does not exist
            if not os.path.exists(path):

                # Give user info
                print "Making file '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)

                # Give permissions
                os.chmod(path, 0775)



    def scan(self, file, path = None, results = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # On first run
        if n == 1:

            # Initialize results
            results = []

            # Read source path
            path = self.str

            # Give user info
            print ("Scanning for '" + str(file) + "' within '" + str(path) +
                   "'...")

        # Get all files from path
        files = os.listdir(path)

        # Get inside path
        os.chdir(path)

        # Upload files
        for f in files:

            # If file
            if os.path.isfile(f):

                # Check if filename fits
                if f == file:

                    # Store path
                    results.append(os.getcwd())

            # If directory and a digit (because a date)
            elif os.path.isdir(f) and f.isdigit():

                # Scan further
                self.scan(file, f, results, n + 1)

        # Go back up
        os.chdir("..")

        # If first level
        if n == 1:

            # Return results
            return results



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Instanciate a reporter for me
    reporter = Reporter()

    # Get basal profile from pump report
    lib.printJSON(reporter.get("pump.json", [], "Basal Profile (Standard)"))

    # Get BGs of today
    #lib.printJSON(reporter.get("BG.json", [], None, now))

    # Unload pump report
    #reporter.unload("pump.json")

    # Add entries to test report
    #reporter.add("test.json", ["D", "A"], {now: 0})

    # Erase entries from test report
    #reporter.erase("test.json", now)

    # Get most recent BG
    reporter.getRecent("BG.json", [], 3)
    reporter.getRecent("treatments.json", ["Temporary Basals"])

    # Increment loop
    #reporter.increment("loop.json", ["Status"], "N")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()