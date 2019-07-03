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



# CLASSES
class Path:

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PATH
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Normalized path object with 2 components (string and list) which always
        points to a directory.
    """

    def __init__(self, path = "./"):

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
            Create corresponding absolute array/string path pair.
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
            Expand path with another path.
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



    def touch(self, filename = None, mode = "JSON"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TOUCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Generate directories and (JSON) file corresponding to path.
        """

        # Only JSON works
        if mode != "JSON":

            # Error
            raise TypeError("Only allowed to touch JSON files: " + mode)

        # Get string from path
        path = self.string

        # If directories do not exist
        if not os.path.exists(path):

            # Info
            # print "Making path '" + path + "'..."

            # Make it
            os.makedirs(path, 0777)

        # Look for file
        if filename is not None:

            # Complete path with filename
            path += filename

            # If it does not exist
            if not os.path.exists(path):

                # Info
                # print "Making file '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)

                # Give permissions
                os.chmod(path, 0777)



    def delete(self, filename = None, path = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Recursively delete path or given file.
        """

        # Top level scan
        if n == 1:

            # Get string from path
            path = self.string

            # No path
            if not os.path.exists(path):
                return

        # Get all child files/directories within path
        children = map(lambda p: path + p, os.listdir(path))

        # Loop on them
        for p in children:

            # If file and name fits
            if os.path.isfile(p) and (filename is None or
                                      filename is not None and
                                      os.path.basename(p) == filename):

                # Give user info
                # print "Deleting file '" + os.path.basename(p) + "'..."

                # Remove it
                os.remove(p)

            # If directory
            elif os.path.isdir(p):

                # Delete further
                self.delete(filename, p + os.sep, n + 1)

        # Not deleting a specific file
        if filename is None:

            # Give user info
            # print "Deleting directory '" + str(path) + "'..."

            # Delete directory
            os.rmdir(path)



    def scan(self, filename, path = None, results = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Scan for a specific file recursively within a directory.
        """

        # Top level scan
        if n == 1:

            # Get string from path
            path = self.string

            # Initialize results
            results = []

            # No path
            if not os.path.exists(path):
                return []

        # Give user info
        # print "Scanning for '" + str(filename) + "' in '" + str(path) + "'..."

        # Get all child files/directories within path
        children = map(lambda p: path + p, os.listdir(path))

        # Loop on them
        for p in children:

            # If file and name fits
            if os.path.isfile(p) and os.path.basename(p) == filename:
                results.append(os.path.dirname(p))

            # If directory
            elif os.path.isdir(p):
                self.scan(filename, p + os.sep, results, n + 1)

        # End of top level scan
        if n == 1:

            # Return results
            return results



# FUNCTIONS
def isString(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ISSTRING
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Make sure the inputted path is a string.
    """
    
    return type(path) is str



def isList(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ISLIST
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Make sure the inputted path is a list of strings.
    """
    
    return type(path) is list and all(map(lambda p: type(p) is str, path))



def split(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        SPLIT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Split string path into array of directories and possibly a file as
        its last element.
    """

    return [p for p in path.split(os.sep) if p != ""]



def merge(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MERGE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Merge an array of directories and possibly a file into a string
        path.
    """

    return os.path.join(*path)



def getDate(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETDATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Get date from 3 parent directories.
    """

    return datetime.date(*[int(d) for d in path.list[-3:]])



def formatDate(date):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FORMATDATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Using a date object, format and return it as follows: YYYY/MM/DD/
    """
    
    # If datetime object
    if type(date) is datetime.datetime or type(date) is datetime.date:

        # Format date
        return datetime.datetime.strftime(date,
            os.path.join("%Y", "%m", "%d", ""))

    # Raise error
    raise NotImplementedError("Incorrect date object type: " + type(date))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Create empty path
    path = Path()
    print "Created path: " + path.string

    # Create new path
    path = Path("Test")
    print "Created path: " + path.string

    # Expand path
    path.expand("1/2")
    print "Expanded path to: " + path.string

    # Expand path
    path.expand(["3", "4"])
    print "Expanded path to: " + path.string

    # Search for file
    print path.scan("test.json")

    # Create, and find
    path.touch("test.json")
    print path.scan("test.json")

    # Scan from top and delete
    path = Path("./Test")
    print path.scan("test.json")
    path.delete()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()