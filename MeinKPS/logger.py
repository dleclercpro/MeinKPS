#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    logger

    Author:   David Leclerc

    Version:  0.1

    Date:     13.04.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that generates a logging instance.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import reporter



# CONSTANTS
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]



# CLASSES
class Logger(object):

    def __init__(self, name, level = "INFO"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store logger name
        self.name = name

        # Get level index
        self.level = LEVELS.index(level)

        # Define logging format
        self.format = "[{:%H:%M:%S}] [{:>17}] [{:>8}] --- {}"

        # Define source path
        self.src = reporter.Path(reporter.SRC)

        # Define report
        self.report = "loop.log"



    def log(self, level, msg, show = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Does level allow logging?
        if LEVELS.index(level) >= self.level:

            # Get current time
            now = datetime.datetime.now()

            # Format message
            msg = self.format.format(now, self.name, level, msg)

            # Define path to log
            path = reporter.Path(self.src.str + lib.formatDate(now))

            # Touch it
            path.touch()

            # Log message
            with open(path.str + self.report, "a") as f:

                # Do it and add new line
                f.write(msg + "\n")

            # Print it to terminal?
            if show:

                # Do it
                print msg



    def debug(self, msg):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEBUG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log message
        self.log("DEBUG", msg)



    def info(self, msg):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INFO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log message
        self.log("INFO", msg)



    def warning(self, msg):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WARNING
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log message
        self.log("WARNING", msg)



    def ERROR(self, msg):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ERROR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log message
        self.log("ERROR", msg)



    def critical(self, msg):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CRITICAL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Log message
        self.log("CRITICAL", msg)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Instanciate logger
    logger = Logger(__name__)

    # Write
    logger.info("Test")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()