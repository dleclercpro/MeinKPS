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

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PATH
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Normalized path object with 2 components (string and list) which always
        points to a directory.
    """

    def __init__(self, path = SRC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare path
        self.path = self.prepare(path)

        # Normalize it
        self.normalize()



    def prepare(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Prepare path: check its type and replace backslashes.
        """

        # Wrong path type
        if not type(path) is str:
            raise TypeError("String path expected. Got: " + type(path))

        # Replace backslashes
        return path.replace("\\", "/")



    def normalize(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NORMALIZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Normalize path to an absolute path.
        """

        # Normalized path
        self.path = os.path.abspath(self.path) + os.sep



    def expand(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPAND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Expand path with another path.
        """

        # Prepare path
        path = self.prepare(path)

        # Only relative paths allowed
        if os.path.isabs(path):
            raise TypeError("Path expansion only possible with relative " +
                            "paths: " + path)

        # Join paths into one
        self.path = os.path.join(self.path, path)

        # Normalize it
        self.normalize()



    def touch(self, filename = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TOUCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Generate directories and (JSON) file corresponding to path.
        """

        # Get string from path
        path = self.path

        # If directories do not exist
        if not os.path.isdir(path):

            # Info
            # print "Making path '" + path + "'..."

            # Make it
            os.makedirs(path, 0o777)

        # Look for file
        if filename is not None:

            # Get file extension
            ext = os.path.splitext(filename)[1]

            # Only JSON works
            if ext != ".json":

                # Error
                raise TypeError("Only allowed to touch JSON files: " + ext)

            # Complete path with filename
            path += filename

            # If it does not exist
            if not os.path.isfile(path):

                # Info
                # print "Making file '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)

                # Give permissions
                os.chmod(path, 0o777)



    def delete(self, path = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Recursively delete path.
        """

        # Top level scan
        if n == 1:

            # Get string from path
            path = self.path

            # No path
            if not os.path.isdir(path):
                return

        # Otherwise
        else:

            # Create new path
            path = Path(path).path

        # Get all child files/directories within path
        children = [path + p for p in os.listdir(path)]

        # Loop on them
        for p in children:

            # If file and name fits
            if os.path.isfile(p):

                # Info
                # print "Deleting file '" + os.path.basename(p) + "'..."

                # Remove it
                os.remove(p)

            # If directory
            elif os.path.isdir(p):

                # Delete further
                self.delete(p, n + 1)

        # Delete directory
        os.rmdir(path)



    def scan(self, filename, path = None, results = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Scan for a specific file recursively within a directory and return
            paths to directories, which contain said file.
        """

        # Top level scan
        if n == 1:

            # Get string from path
            path = self.path

            # Initialize results
            results = []

            # No path
            if not os.path.isdir(path):
                return []

        # Otherwise
        else:

            # Create new path
            path = Path(path).path

        # Info
        # print "Scanning for '" + str(filename) + "' in '" + str(path) + "'..."

        # Get all child files/directories within path
        children = [path + p for p in os.listdir(path)]

        # Loop on them
        for p in children:

            # If file and name fits
            if os.path.isfile(p) and os.path.basename(p) == filename:
                results.append(Path(os.path.dirname(p)))

            # If directory
            elif os.path.isdir(p):
                self.scan(filename, p, results, n + 1)

        # End of top level scan
        if n == 1:

            # Return results
            return results



# FUNCTIONS
def getDate(path):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETDATE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Get date from 3 parent directories.
    """

    # Initialize date
    date = []

    # Get string path
    path = os.path.dirname(path.path)

    # Loop 3 directories up to get corresponding date
    for i in range(3):

        # Split path
        path, dirname = os.path.split(path)

        # Add date component
        date.append(int(dirname))

    # Reverse date to get format YYYY.MM.DD
    date.reverse()

    # Return datetime object
    return datetime.date(*date)



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
        return datetime.datetime.strftime(date, "%Y/%m/%d")

    # Raise error
    raise NotImplementedError("Incorrect date object type: " + type(date))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Create path
    _path = Path()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()