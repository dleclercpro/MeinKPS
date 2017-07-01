#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    uploader

    Author:   David Leclerc

    Version:  0.1

    Date:     01.07.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that uploads all reports to a server.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import ftplib



# USER LIBRARIES
import reporter



# Instanciate a reporter
Reporter = reporter.Reporter()



def upload(ftp, path, ext = None):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        UPLOAD
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get all files from path
    files = os.listdir(path)

    # Get inside path
    os.chdir(path)

    # Upload files
    for f in files:

        # If file
        if os.path.isfile(f):

            # Verify extension
            if "." + ext != os.path.splitext(f)[1]:

                # Skip file
                continue

            # Give user info
            print "Uploading: '" + f + "'"

            # Open file
            F = open(f, "r")

            # Upload file
            ftp.storlines("STOR " + f, F)

            # Close file
            F.close()

        # If directory
        elif os.path.isdir(f):

            # If directory does not exist
            if f not in ftp.nlst():

                # Give user info
                print "Making directory: '" + f + "'"

                # Make directory
                ftp.mkd(f)

            # Move in directory
            ftp.cwd(f)

            # Upload files in directory
            upload(ftp, f, ext)

    # Get back to original directory on server
    ftp.cwd("..")

    # Locally as well
    os.chdir("..")



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Load FTP infos
    Reporter.load("FTP.json")

    # Instanciate an FTP object
    ftp = ftplib.FTP(Reporter.getEntry([], "Host"),
                     Reporter.getEntry([], "User"),
                     Reporter.getEntry([], "Password"))

    # Move to directory
    ftp.cwd(Reporter.getEntry([], "Path"))

    # Define file paths
    path =  os.getcwd() + "/Reports/"

    # Upload files within path
    upload(ftp, path, "json")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
