#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    path

    Author:   David Leclerc

    Version:  0.1

    Date:     15.04.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a module that defines a Path object able to deal with
    		  directory/file management.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os



# CONSTANTS
SRC = os.path.dirname(os.path.realpath(__file__)) + os.sep



# CLASSES
class Path:

    def __init__(self, path = SRC):

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
        self.normalize()

        # Compute path depth
        self.depth = len(self.list)



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
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
            Note: first slash only works for Linux.
        """

        # Merge path
        return os.sep + os.sep.join(self.list)



    def toDate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TODATE
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

        # Reverse date to get format YYYY.MM.DD
        date.reverse()

        # Return datetime object
        return datetime.date(*date)



    def fromDate(self, date):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FROMDATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

	    # If datetime object
	    if type(date) is datetime.datetime or type(date) is datetime.date:

	        # Format date
	        date = datetime.datetime.strftime(date, "%Y" + os.sep +
	                                                "%m" + os.sep +
	                                                "%d" + os.sep)

	    # Otherwise
	    else:

	        # Raise error
	        raise NotImplementedError

	    # Return formatted date
	    return date



    def touch(self, file = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TOUCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current path
        path = Path(self.list[:n]).str

        # Look for path
        if n <= self.depth:

            # Show current path
            #print path

            # If it does not exist
            if not os.path.exists(path):

                # Info
                #print "Making path '" + path + "'..."

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

                # Info
                #print "Making file '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)

                # Give permissions
                os.chmod(path, 0777)



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
            #print ("Scanning for '" + str(file) + "' within '" + str(path) +
            #	    "'...")

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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()