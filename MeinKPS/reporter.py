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

        # Set source path to reports
        self.src = os.getcwd() + "/Reports/"
        #self.src = "/home/pi/MeinKPS/MeinKPS/Reports/"

        # Initialize reports
        self.reports = []



    def find(self, path, file = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # On first run
        if n == 1:

            # Convert path to list
            path = self.splitPath(path)

        # Stringify current path
        p = self.mergePath(path[:n])

        # Look for path
        if n < len(path):

            # If it does not exist
            if not os.path.exists(p):

                # Give user info
                print "Making '" + p + "/'..."

                # Make it
                os.makedirs(p)

            # Contine looking
            self.find(path, file, n + 1)

        # Look for file
        elif file is not None:

            # Complete path with filename
            p += file

            # If it does not exist
            if not os.path.exists(p):

                # Give user info
                print "Making '" + p + "'..."

                # Create it
                with open(p, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)



    def scan(self, file, path = None, results = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If path undefined
        if path is None:

            # Define source as path
            path = self.src

        # On first run
        if n == 1:

            # Give user info
            print ("Scanning for '" + str(file) + "' within '" + str(path) +
                   "'...")

            # Initialize results
            results = []

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

            # If directory
            elif os.path.isdir(f):

                # Scan further
                self.scan(file, f, results, n + 1)

        # Go back up
        os.chdir("..")

        # If first level
        if n == 1:

            # Return results
            return results



    def splitPath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SPLITPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Split path
        return [p for p in path.split("/") if p != ""]



    def mergePath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MERGEPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: The first "/" will only work for Linux
        """

        # Merge path
        #return "/" + "/".join(path) + "/"
        return "/".join(path) + "/"



    def datePath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DATEPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize date
        date = []

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



    def showPath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Format path
        return " > ".join(path)



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



    def new(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NEW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Loop on reports
        for report in self.reports:

            # Check if report already exists
            if report.name == name and report.date == date:

                # Give user info
                print ("Report '" + name + "' (" + str(date) + ") already " +
                       "loaded.")

                # Skip
                return False

        # Generate new report
        self.reports.append(Report(name, path, date, json))

        # Success
        return True



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset reports
        self.reports = []



    def load(self, name, dates = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize number of reports to load
        n = 0

        # No dates
        if dates is None:

            # Define path
            p = self.src

            # Generate new report
            if self.new(name, p):

                # Update count
                n += 1

        # Otherwise
        else:

            # Make sure dates are sorted out and only appear once
            # This can deal with both list and dict types
            dates = lib.uniqify(dates)

            # Loop on dates
            for date in dates:

                # Format current date
                d = datetime.datetime.strftime(date, "%Y/%m/%d")

                # Define path
                p = self.src + d + "/"

                # Generate new report
                if self.new(name, p, d):

                    # Update count
                    n += 1

        # Load report(s)
        for i in range(n):

            # Get current new report
            report = self.reports[-(i + 1)]

            # Give user info
            print ("Loading report: '" + report.name + "' (" +
                   str(report.date) + ")")

            # Make sure report exists
            self.find(report.path, name)

            # Open report
            with open(report.path + name, "r") as f:

                # Load JSON
                report.json = json.load(f)



    def unload(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UNLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If date
        if date is not None:

            # Get current date
            d = datetime.datetime.strftime(date, "%Y/%m/%d")

        # Loop on reports
        for i in range(len(self.reports)):

            # Get current report
            report = self.reports[i]

            # If name fits
            if report.name != name:

                # Skip
                continue

            # If dates
            if date is not None and report.date != d:

                # Skip
                continue

            # Give user info
            print ("Unloading report: " + report.name + " (" +
                   str(report.date) + ")")

            # Delete it
            del self.reports[i]

            # Exit
            return

        # Report not found
        sys.exit("Report could not be found, thus not unloaded.")



    def save(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SAVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Rewrite reports
        for report in self.reports:

            # If report was modified
            if report.modified:

                # Give user info
                print ("Updating report: '" + report.name + "' (" +
                       str(report.date) + ")")

                # Rewrite report
                with open(report.path + report.name, "w") as f:

                    # Dump JSON
                    json.dump(report.json, f,
                              indent = 4,
                              separators = (",", ": "),
                              sort_keys = True)

                # Report was updated
                report.modified = False



    def getReport(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETREPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If date
        if date is not None:

            # Get and format date
            date = datetime.datetime.strftime(date, "%Y/%m/%d")

        # Give user info
        print "Getting report: '" + name + "' (" + str(date) + ")"

        # Loop through reports
        for report in self.reports:

            # Check if names match
            if report.name != name:

                # Skip
                continue

            # Check if dates match
            if report.date != date:

                # Skip
                continue

            # Return report
            return report

        # Give user info
        sys.exit("Did not find report.")



    def getSection(self, report, path, make = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETSECTION
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make sure section path is of list type
        if type(path) is not list:

            # Raise error
            raise errors.BadPath

        # Read section depth: if it is equal to 0, the following loop is
        # skipped and the section corresponds to the whole report
        d = len(path)

        # First level section is whole report
        section = report.json

        # Give user info
        print "Getting section: " + self.showPath(path)

        # Loop through whole report to find section
        for i in range(d):

            # Get current path
            p = path[i]

            # Check if section report exists
            if p not in section:

                # Make section if desired
                if make:
                
                    # Give user info
                    print "Section not found. Making it..."

                    # Create it
                    section[p] = {}

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[p]

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



    def getLastEntry(self, section):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETLASTENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Getting last entry."

        # Look if at least one entry exists
        if len(section) > 0:

            # Get latest key
            key = max(section)

            # Get corresponding value
            value = section[key]

            # Give user info
            print "Entry found."

            # Return entry for external access
            return [key, value]

        # Otherwise
        else:

            # Give user info
            print "No entry found."



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



    def add(self, name, path, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If entries are dated
        if type(min(entries)) is datetime.datetime:

            # Initialize date
            date = True

            # Load report(s)
            self.load(name, entries)

        # Otherwise
        else:

            # Initialize date
            date = None

            # Load report
            self.load(name)

            # Get it
            report = self.getReport(name)

            # Get section
            section = self.getSection(report, path, True)

        # Loop through entries
        for key in sorted(entries):

            # Get value
            value = entries[key]

            # If date
            if date is not None:

                # Get date
                d = key.date()

                # Format key
                key = lib.formatTime(key)

                # If date is different than previous one
                if d != date:

                    # Update date
                    date = d

                    # Get report
                    report = self.getReport(name, date)

                    # Get section
                    section = self.getSection(report, path, True)

            # Add entry
            self.addEntry(section, {key: value}, overwrite)

            # Report was modified
            report.modified = True

        # Save reports
        self.save()



    def get(self, name, path, keys):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make sure keys are a list
        if type(keys) is not list:

            # Make single key to list
            keys = [keys]

        # If entries are dated
        if type(min(keys)) is datetime.datetime:

            # Initialize date
            date = True

            # Load report(s)
            self.load(name, keys)

        # Otherwise
        else:

            # Initialize date
            date = None

            # Load report
            self.load(name)

            # Get it
            report = self.getReport(name)

            # Get section
            section = self.getSection(report, path)

        # Initialize values
        values = []

        # Loop through entries
        for key in keys:

            # If date
            if date is not None:

                # Get date
                d = key.date()

                # Format key
                key = lib.formatTime(key)

                # If date is different than previous one
                if d != date:

                    # Update date
                    date = d

                    # Get report
                    report = self.getReport(name, date)

                    # Get section
                    section = self.getSection(report, path)

            # Add value
            values.append(self.getEntry(section, key))

        # If single value
        if len(values) == 1:

            # Return single value
            return values[0]

        # Otherwise
        else:

            # Return values
            return values



    def getRecent(self, name, path = [], n = 2):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETRECENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Scan for all possible report paths
        paths = self.scan(name)

        # If no possible reports found
        if not paths:

            # Exit
            sys.exit("Nothing found for '" + name + "'.")

        # Get n most recent ones
        paths = lib.nMax(paths, n)

        # Initialize dates
        dates = []

        # Loop on paths
        for p in paths:

            # Get date from path
            dates.append(self.datePath(p))

        # Load corresponding reports
        self.load(name, dates)

        # Group all entries in one dict
        entries = {}

        # Loop on all reports
        for date in dates:

            # Get report
            report = self.getReport(name, date)

            # Get section
            section = self.getSection(report, path)

            # Give user info
            print "Merging '" + report.name + "' (" + report.date + ")"

            # Merge entries
            entries = lib.mergeDict(entries, section)

        # Return entries
        return entries



    def increment(self, name, path, key, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get report
        report = self.getReport(name, date)

        # Get section
        section = self.getSection(report, path)

        # Increment entry
        self.addEntry(section, {key: self.getEntry(section, key) + 1}, True)



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

    # Load reports
    reporter.load("pump.json")

    # Get basal profile from pump report
    reporter.get("pump.json", [], "Basal Profile (Standard)")

    # Unload pump report
    reporter.unload("pump.json")

    # Add entries to test report
    #reporter.add("test.json", ["A", "B"], {"C": 0, "D": 1})

    # Get most recent BG
    lib.printJSON(reporter.getRecent("BG.json"))
    lib.printJSON(reporter.getRecent("treatments.json", ["Temporary Basals"]))



# Run this when script is called from terminal
if __name__ == "__main__":
    main()