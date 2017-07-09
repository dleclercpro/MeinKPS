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
        return "/" + "/".join(path)



    def showPath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Format path
        return " > ".join(["."] + path)



    def new(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NEW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Loop on reports
        for i in range(len(self.reports)):

            # Get current report
            report = self.reports[i]

            # Check if report already exists
            if report["Name"] == name and report["Date"] == date:

                # Exit
                sys.exit("Report '" + name + "' (" + str(date) + ") already " +
                         "exists.")

        # Generate new report
        self.reports.append({"Name": name,
                             "Path": path,
                             "Date": date,
                             "JSON": json})



    def find(self, path, n = 1):

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

        # If destination directory not yet attained
        if n < len(path):

            # If it does not exist
            if not os.path.exists(p):

                # Give user info
                print "Making '" + p + "'/..."

                # Make it
                os.makedirs(p)

            # Contine looking
            self.find(path, n + 1)

        # Otherwise, time to look for file
        else:

            # If it does not exist
            if not os.path.exists(p):

                # Give user info
                print "Making '" + p + "'..."

                # Create it
                with open(p, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)



    def load(self, name, dates = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # No dates
        if dates is None:

            # Define number of reports to load
            n = 1

            # Define path
            p = self.src

            # Generate new report
            self.new(name, p)

        # Otherwise
        else:

            # Make sure dates appear only once
            dates = list(set(dates))

            # Define number of reports to load
            n = len(dates)

            # Loop on dates
            for i in range(n):

                # Format current date
                d = datetime.datetime.strftime(dates[i], "%Y/%m/%d")

                # Define path
                p = self.src + d + "/"

                # Generate new report
                self.new(name, p, d)

        # Load report(s)
        for i in range(n):

            # Get current new report
            report = self.reports[-(i + 1)]

            # Get current path to file
            p = report["Path"] + name

            # Give user info
            print ("Loading: '" + report["Name"] + "' (" + str(report["Date"]) +
                   ")")

            # Make sure report exists
            self.find(p)

            # Open report
            with open(p, "r") as f:

                # Load JSON
                report["JSON"] = json.load(f)

        # Show reports
        lib.printJSON(self.reports)



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
            if report["Name"] != name:

                # Skip
                continue

            # If dates
            if date is not None and report["Date"] != d:

                # Skip
                continue

            # Give user info
            print ("Unloading: " + report["Name"] + " (" + str(report["Date"]) +
                   ")")

            # Delete it
            del self.reports[i]

            # Show reports
            lib.printJSON(self.reports)

            # Exit
            return

        # Report not found
        sys.exit("Report could not be found, thus not unloaded.")



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset reports
        self.reports = []



    def save(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SAVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Rewrite reports
        for i in range(len(self.reports)):

            # Get current report
            report = self.reports[i]

            # If report has date
            if report["Date"] is not None:

                # Give user info
                print ("Updating: '" + report["Name"] + "' (" + report["Date"] +
                       ")")

            # Otherwise
            else:

                # Give user info
                print "Updating: '" + report["Name"] + "'"

            # Rewrite report
            with open(report["Path"] + report["Name"], "w") as f:

                # Dump JSON
                json.dump(report["JSON"], f,
                          indent = 4,
                          separators = (",", ": "),
                          sort_keys = True)



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
        print "Looking for report: '" + name + "' (" + str(date) + ")"

        # Loop through reports
        for report in self.reports:

            # Check if names match
            if report["Name"] != name:

                # Skip
                continue

            # Check if dates match
            if report["Date"] != date:

                # Skip
                continue

            # Give user info
            print "Found report:"

            # Show report
            lib.printJSON(report)

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
        section = report["JSON"]

        # Give user info
        print "Attempting to find section: " + self.showPath(path)

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

                    # Show section
                    lib.printJSON({p: section[p]})

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[p]

        # Give user info
        print "Found section:"

        # Print section
        lib.printJSON(section)

        # Return section
        return section



    def addEntry(self, section, entry, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Attempting to add entry:"

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

            # Show section
            lib.printJSON(section)



    def addEntries(self, name, path, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRIES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If entries are dated
        if type(min(entries)) is datetime.datetime:

            # Initialize date
            date = True

        # Otherwise
        else:

            # Initialize date
            date = None

            # Get corresponding report
            report = self.getReport(name)

            # Get corresponding section
            section = self.getSection(report, path, True)

        # Loop through entries
        for key in sorted(entries):

            # Get value
            value = entries[key]

            # If date
            if date is not None:

                # Get date
                d = key.date()

                # Format time
                key = lib.formatTime(key)

                # If date is different than previous one
                if d != date:

                    # Update date
                    date = d

                    # Get corresponding report
                    report = self.getReport(name, date)

                    # Get corresponding section
                    section = self.getSection(report, path, True)

            # Add entry
            self.addEntry(section, {key: value}, overwrite)











    def deleteEntry(self, report, path, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETEENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load section
        section = self.getSection(report, path)

        # Give user info
        print ("Attempting to delete entry: " + self.showPath(path) + " > " +
               str(key))

        # If it does, delete it
        if key in section:

            # Delete entry
            del section[key]

            # Give user info
            print "Entry deleted."

            # Rewrite report
            self.save()

        else:

            # Give user info
            print "No such entry: no need to delete."



    def getEntry(self, report, path, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print ("Attempting to find entry: " + self.showPath(path) + " > " +
               str(key))

        # Load section
        section = self.getSection(report, path)

        # Look if entry exists
        if key in section:

            # Get entry matching the key
            entry = section[key]

            # Give user info
            print "Entry found: " + str(entry)

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."



    def getLastEntry(self, report, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETLASTENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load section
        section = self.getSection(report, path)

        # Give user info
        print "Attempting to find last entry in: " + self.showPath(path)

        # Look if at least one entry exists
        if len(section) > 0:

            # Get latest entry time
            t = max(section)

            # Get corresponding entry
            entry = section[t]

            # Give user info
            print "Entry found: " + str(entry) + " (" + str(t) + ")" 

            # Return entry for external access
            return [t, entry]

        # Otherwise
        else:

            # Give user info
            print "No entry found."






    def increment(self, path, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Increment entry
        self.addEntries(path, key, self.getEntry(path, key) + 1, True)



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

    # Test
    reporter.load("profile.json")
    reporter.load("BG.json", [now, now - datetime.timedelta(days = 1)])
    reporter.unload("profile.json")
    #report = reporter.getReport("BG.json", now)
    #section = reporter.getSection(report, ["A", "B"])
    #reporter.addEntry(section, {"D": 1})
    #reporter.addEntries("profile.json", ["A", "B"], {"C": 0, "D": 1})
    #reporter.addEntries("BG.json", ["A", "B"], {now: 0, now - datetime.timedelta(days = 1): 1})



# Run this when script is called from terminal
if __name__ == "__main__":
    main()