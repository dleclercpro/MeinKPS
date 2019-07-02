#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    path

    Author:   David Leclerc

    Version:  0.2

    Date:     02.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a module that defines a Path object able to deal with
              directory/file management.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import json
import datetime



# CONSTANTS
SRC = os.getcwd() + os.sep



# CLASSES
class Path:

    def __init__(self, path = SRC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize path components
        self.string = None
        self.list = None

        # String
        if isString(path):
            self.string = path

        # List
        elif isList(path):
            self.list = path

        # Error
        else:
            raise TypeError("Incorrect path type: " + path)

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

        # List
        if self.list is not None:
            self.string = merge(self.list)

        # Normalize both path types
        self.string = os.path.abspath(self.string) + os.sep
        self.list = split(self.string)



    def expand(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPAND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # String
        if isString(path):
            pass

        # List
        elif isList(path):
            path = merge(path)

        # Error
        else:
            raise TypeError("Incorrect path type: " + path)

        # Only relative paths allowed
        if os.path.isabs(path):
            raise TypeError("Path expansion only possible with relative " +
                            "paths: " + path)

        # Join paths
        self.string = os.path.join(self.string, path)
        self.list = None
        
        # Normalize
        self.normalize()



    def date(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize date
        date = []

        # Get initial path
        path = self.string

        # Loop 3 directories up to get corresponding date
        for i in range(3):

            # Split path
            path = os.path.split(path)

            # Add date component
            date.append(int(path))

        # Reverse date to get format YYYY.MM.DD
        date.reverse()

        # Return datetime object
        return datetime.date(*date)



    def touch(self, filename = None, n = 1, mode = "JSON"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TOUCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Only JSON works
        if mode != "JSON":

            # Error
            raise TypeError("Only allowed to touch JSON files: " + mode)

        # Get current path
        path = Path(self.list[:n]).string

        # Look for path
        if n <= self.depth:

            # If it does not exist
            if not os.path.exists(path):

                # Info
                print "Making path '" + path + "'..."

                # Make it
                os.makedirs(path)

            # Contine looking
            self.touch(filename, n + 1, mode)

        # Look for file
        elif file is not None:

            # Complete path with filename
            path += filename

            # If it does not exist
            if not os.path.exists(path):

                # Info
                print "Making file '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)

                # Give permissions
                os.chmod(path, 0777)



    def scan(self, filename, path = "", results = [], n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Top level scan
        if n == 1:

            # Read source path
            path = self.string

        # Give user info
        # print ("Scanning for '" + str(filename) + "' within '" + str(path) +
        #        "'...")

        # Get all files from path
        files = os.listdir(path)

        # Get inside path
        os.chdir(path)

        # Upload files
        for f in files:

            # If file and name fits
            if os.path.isfile(f) and f == filename:

                # Store path
                results.append(os.getcwd())

            # If directory and a digit (because a date)
            elif os.path.isdir(f) and f.isdigit():

                # Scan further
                self.scan(filename, f, results, n + 1)

        # Go back up
        os.chdir("..")

        # End of top level scan
        if n == 1:

            # Return results
            return results



# FUNCTIONS
def split(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        SPLIT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    if not isString(path):
        raise TypeError("Incorrect path type (string needed): " + path)

    return [p for p in path.split(os.sep) if p != ""]



def merge(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MERGE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Note: first slash only works for Linux.
    """

    if not isList(path):
        raise TypeError("Incorrect path type (list needed): " + path)

    # return os.sep + os.path.join(*path)
    return os.path.join(*path)



def formatDate(date):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FORMATDATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Using a date object, format and return it as follows: YYYY/MM/DD/
    """
    
    # If datetime object
    if type(date) is datetime.datetime or type(date) is datetime.date:

        # Format date
        return datetime.datetime.strftime(date,
            os.path.join("%Y", "%m", "%d", ""))

    # Raise error
    raise NotImplementedError("Incorrect date object type: " + type(date))



def isString(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ISSTRING
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Make sure the inputted path is a string.
    """
    
    return type(path) is str



def isList(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ISLIST
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Make sure the inputted path is a list of strings.
    """
    
    return type(path) is list and all(map(lambda p: type(p) is str, path))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Create new path
    path = Path("./Test")
    print "Created path: " + path.string

    # Expand path
    path.expand("1/2/3")
    print "Expanded path to: " + path.string

    # Expand path
    path.expand(["4", "5", "6"])
    print "Expanded path to: " + path.string



# Run this when script is called from terminal
if __name__ == "__main__":
    main()