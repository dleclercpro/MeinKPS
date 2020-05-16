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
import pysftp



# USER LIBRARIES
import logger
import errors
import path
import reporter



# Define instances
Logger = logger.Logger("uploader")



# CLASSES
class Uploader(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        self.report = reporter.getSFTPReport()



    def upload(self, sftp, path, ext = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UPLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

                # Info
                Logger.debug("Uploading: '" + os.getcwd() + "/" + f + "'")

                # Upload file
                sftp.put(f, preserve_mtime = True)

            # If directory
            elif os.path.isdir(f):

                # If directory does not exist
                if f not in sftp.listdir():

                    # Info
                    Logger.debug("Making directory: '" + f + "'")

                    # Make directory
                    sftp.mkdir(f)

                # Move in directory
                sftp.cwd(f)

                # Upload files in directory
                self.upload(sftp, f, ext)

        # Get back to original directory on server
        sftp.cwd("..")

        # Locally as well
        os.chdir("..")



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Test if report is empty before proceding
        if not self.report.isValid():
            raise errors.InvalidSFTPReport

        # Disable host key checking (FIXME)
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        # Instanciate an FTP object
        sftp = pysftp.Connection(
            host = self.report.get(["Host"]),
            username = self.report.get(["Username"]),
            private_key = path.REPORTS.path + self.report.get(["Key"]),
            cnopts = cnopts)

        # Move to directory
        sftp.cwd(self.report.get(["Path"]))

        # Upload files
        self.upload(sftp, path.EXPORTS.path, "json")

        # Close SFTP connection
        sftp.close()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define uploader
    uploader = Uploader()

    # Run it
    uploader.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()