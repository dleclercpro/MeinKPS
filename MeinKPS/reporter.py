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

        # Initialize name
        self.name = None

        # Initialize dates
        self.dates = []

        # Initialize paths
        self.paths = []

        # Initialize reports
        self.reports = {}

        # Initialize section
        self.section = []



    def find(self, path, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # On first run
        if n == 1:

            # Convert path to list
            path = path.split("/")

            # Remove empty entries
            path = [p for p in path if p != ""]

        # Stringify current path
        p = "/".join(path[:n])

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
                    json.dump({}, f)



    def load(self, name, dates = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store report's name
        self.name = name

        # No dates
        if dates is None:

            # Define path
            self.paths.append(self.src)

        # Otherwise
        else:

            # Loop on dates
            for i in range(len(dates)):

                # Format current date
                d = datetime.datetime.strftime(dates[i], "%Y/%m/%d")

                # Store it
                self.dates.append(d)

                # Define path
                self.paths.append(self.src + d + "/")

        # Load report(s)
        for i in range(len(self.paths)):

            # Get current path to file
            p = self.paths[i] + name

            # Give user info
            print "Loading '" + p + "'..."

            # Make sure report exists
            self.find(p)

            # Open report
            with open(p, "r") as f:

                # Load JSON
                self.reports[p] = json.load(f)

        # Show reports
        self.show()



    def save(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SAVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Rewrite reports
        for p in self.reports:

            # Give user info
            print "Updating '" + p + "'..."

            # Rewrite report
            with open(p, "w") as f:
                json.dump(self.reports[p], f,
                          indent = 4,
                          separators = (",", ": "),
                          sort_keys = True)



    def show(self, report = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define default report to show
        if report is None:

            # Last report
            report = self.reports

        # Print report entries
        print json.dumps(report, indent = 2,
                                 separators = (",", ": "),
                                 sort_keys = True)



    def showPath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Format path
        return " > ".join(["."] + path)



    def delete(self, path, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report section
        self.getSection(path)

        # Give user info
        print ("Attempting to delete entry: " + self.showPath(path) + " > " +
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



    def getSection(self, path, create = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETSECTION
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make sure section path is of list type!
        if type(path) is not list:

            # Raise error
            raise errors.BadPath

        # First level section is whole report
        self.section = self.report

        # Read section depth: if it is equal to 0, the following loop is
        # skipped and the section corresponds to the whole report
        d = len(path)

        # Give user info
        print "Attempting to find section: " + self.showPath(path)

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

                    # Raise error
                    raise errors.NoSection

            # Update section
            self.section = self.section[path[i]]

        # Give user info
        print "Section found."



    def getEntry(self, path, key = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report section
        self.getSection(path)

        # If no key
        if key is None:

            # Return section
            return self.section

        # Give user info
        print ("Attempting to find entry: " + self.showPath(path) + " > " +
               str(key))

        # Look if entry exists
        if key in self.section:

            # Get entry matching the key
            entry = self.section[key]

            # Give user info
            print "Entry found:"

            # If entry is a dict
            if type(entry) is dict:
                self.show(entry)

            # Otherwise
            else:
                print entry

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."



    def getLastEntry(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETLASTENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report section
        self.getSection(path)

        # Give user info
        print ("Attempting to find last entry in: " + self.showPath(path))

        # Look if at least one entry exists
        if len(self.section) > 0:

            # Get latest entry time
            t = max(self.section)

            # Get corresponding entry
            entry = self.section[t]

            # Give user info
            print "Entry found:"

            # Give user info
            print str(entry) + " (" + str(t) + ")" 

            # Return entry for external access
            return [t, entry]

        # Otherwise
        else:

            # Give user info
            print "No entry found."



    def addEntries(self, path, keys, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRIES
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report section
        self.getSection(path, True)

        # Make sure input is of list type
        if type(keys) is not list:
            keys = [keys]
            entries = [entries]

        # Compute number of entries
        n = len(keys)

        # Add entries
        for i in range(n):

            # Give user info
            print ("Attempting to add entry: " + self.showPath(path) + " > " +
                   str(keys[i]) + " > " + json.dumps(entries[i]))

            # Look if entry is already in report
            if keys[i] in self.section and not overwrite:

                # Give user info
                print "Entry already exists."

            # If not, write it down
            else:

                # Add entry to report
                self.section[keys[i]] = entries[i]

                # If overwritten
                if overwrite:

                    # Give user info
                    print "Entry overwritten."

                # Otherwise
                else:

                    # Give user info
                    print "Entry added."

        # Rewrite report
        self.save()



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
    #reporter.find("/2017/07/05/BG.json")
    reporter.load("BG.json", [now, now - datetime.timedelta(days = 1)])



# Run this when script is called from terminal
if __name__ == "__main__":
    main()