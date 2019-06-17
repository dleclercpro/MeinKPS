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
Logger = logger.Logger("reporter.py")



# CLASSES
class Reporter:

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define source path
        self.src = path.Path(path.SRC + "Reports")

        # Define export path
        self.exp = path.Path(self.src.str + "Export")



    def getDates(self, name):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETDATES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize dates
        dates = []

        # Scan for all possible report directories
        directories = self.src.scan(name)

        # If no possible reports found
        if not directories:

            # Give user info
            Logger.debug("No dated report found for '" + name + "'.")

        # Otherwise
        else:

            # Convert paths to dates
            dates = [path.Path(d).date() for d in directories]

        # Return dates
        return dates



    def getReport(self, name, date = None, directory = None, touch = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETREPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Default directory
        if directory is None:

            # Define source
            directory = self.src.str

        # Otherwise
        if date is not None:

            # Format date
            date = path.formatDate(date)

            # Update path to report
            directory = path.Path(directory + date).str

        # If report can be generated in case it doesn't exist yet
        if touch:

            # Touch it
            path.Path(directory).touch(name)

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

        # Give user info
        Logger.debug("Getting section: " + " > ".join(["."] + branch))

        # Loop through whole report to find section
        for i in range(d):

            # Get current branch
            b = branch[i]

            # Check if section report exists
            if b not in section:

                # Make section if desired
                if make:
                
                    # Give user info
                    Logger.debug("Section not found. Making it...")

                    # Create it
                    section[b] = {}

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[b]

        # Give user info
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

        # Give user info
        Logger.debug("Getting entry: " + str(key))

        # Look if entry exists
        if key in section:

            # Get corresponding value
            value = section[key]

            # Give user info
            Logger.debug("Entry found.")

            # Show value
            Logger.debug(lib.JSONize(value))

            # Return it for external access
            return value

        # Otherwise
        else:

            # Give user info
            Logger.debug("No matching entry found.")

            # Return nothing
            return None



    def addEntry(self, section, entry, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Adding entry:")

        # Show entry
        Logger.debug(lib.JSONize(entry))

        # Destructure entry
        key, value = entry.items()[0]

        # Look if entry is already in report
        if key in section and not overwrite:

            # Give user info
            Logger.debug("Entry already exists.")

            # Entry was not modified
            return False

        # If not, write it down
        else:

            # Add entry to report
            section[key] = value

            # If overwritten
            if overwrite:

                # Give user info
                Logger.debug("Entry overwritten.")

            # Otherwise
            else:

                # Give user info
                Logger.debug("Entry added.")

            # Entry was modified
            return True



    def deleteEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETEENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Deleting entry: " + str(key))

        # If it does, delete it
        if key in section:

            # Delete entry
            del section[key]

            # Give user info
            Logger.debug("Entry deleted.")

        else:

            # Give user info
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



class Report:

    def __init__(self, name = None, directory = None, date = None, json = {}):

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
        """

        # Give user info
        Logger.debug("Resetting report: '" + self.name + "' (" +
                     str(self.date) + ")")

        # Reset JSON
        self.json = {}



    def erase(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ERASE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Erasing report: '" + self.name + "' (" + str(self.date) +
                     ")")

        # Reset JSON
        self.reset()

        # Store it
        self.store()



    def update(self, json):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Updating report: '" + self.name + "' (" + str(self.date) +
                     ")")

        # Update JSON
        self.json = lib.mergeDicts(self.json, json)



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Loading report: '" + self.name + "' (" + str(self.date) +
                     ")")

        # Try opening report
        try:

            # Open report
            with open(self.directory + self.name, "r") as f:

                # Load JSON
                self.json = json.load(f)

        # In case of error
        except:

            # No report
            # FIXME: just reset report to empty JSON object
            self.erase()
            #raise errors.NoReport(self.name, self.date)

        # Give user info
        Logger.debug("Report loaded.")



    def store(self, directory = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing report: '" + self.name + "' (" + str(self.date) +
                     ")")

        # If no directory given
        if directory is None:

            # Use stored directory
            directory = self.directory

        # Make sure report exists
        path.Path(directory).touch(self.name)

        # Rewrite report
        with open(directory + self.name, "w") as f:

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
                                  "Directory": self.directory,
                                  "Date": self.date,
                                  "JSON": self.json}))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now() - datetime.timedelta(days = 0)

    # Instanciate a reporter for me
    reporter = Reporter()

    # Get basal profile from pump report
    #reporter.get("pump.json", [], "Basal Profile (Standard)")

    # Get BGs of today
    #reporter.get("BG.json", [], None, now)

    # Get most recent data
    json = reporter.getRecent(now, "BG.json", [], 3, True)

    # Print data
    print lib.JSONize(json)

    # Increment loop
    #reporter.increment("loop.json", ["Status"], "N")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()