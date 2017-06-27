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
        self.src = "/home/pi/MeinKPS/MeinKPS/Reports/"

        # Initialize section
        self.section = []



    def load(self, report):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store report's name
        self.name = report

        # Give user info
        print "Loading '" + self.name + "'..."

        # Check if report exists. If not, generate it.
        if not os.path.exists(self.src + self.name):

            # Give user info
            print "'" + self.name + "' does not exist. Creating it..."

            # Creating new empty report
            with open(self.src + self.name, "w") as f:
                json.dump({}, f)

        # Load report
        with open(self.src + self.name, "r") as f:
            self.report = json.load(f)

        # Give user info
        print "'" + self.name + "' loaded."



    def save(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SAVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Updating '" + self.name + "'..."

        # Rewrite report
        with open(self.src + self.name, "w") as f:
            json.dump(self.report,
                      f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)

        # Give user info
        print "'" + self.name + "' updated."



    def delete(self, path, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Print report entries
        print self.report



    def formatPath(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FORMATPATH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Format path
        return " > ".join(["."] + path)



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

                    # Raise error
                    raise errors.NoSection

            # Update section
            self.section = self.section[path[i]]

        # Give user info
        print "Section found."



    def getEntry(self, path, key):

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
        print ("Attempting to find entry: " + self.formatPath(path) + " > " +
               str(key))

        # Look if entry exists
        if key in self.section:

            # Get entry matching the key
            entry = self.section[key]

            # Give user info
            print "Entry found:"

            # Print entry based on type
            if type(entry) is dict:
                lib.printJSON(entry)

            else:
                print entry

            # Return entry for external access
            return entry

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."



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
            print ("Attempting to add entry: " + self.formatPath(path) + " > " +
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

    # Instanciate a reporter for me
    reporter = Reporter()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
