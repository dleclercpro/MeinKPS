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
import os
import datetime
import logging
import logging.handlers



# USER LIBRARIES
import lib



# CONSTANTS
SRC = os.path.dirname(os.path.realpath(__file__)) + os.sep + "Reports" + os.sep



# FUNCTIONS
def get(name, level = logging.DEBUG):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GET
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get logger
    logger = logging.getLogger(name)

    # Set its level
    logger.setLevel(level)

    # Define logging format
    fmt = "[%(asctime)s] [%(levelname)8s] --- %(message)s"

    # Define formatter
    formatter = logging.Formatter(fmt = fmt, datefmt = "%H:%M:%S")

    # Define timed rotating handler
    handler = logging.handlers.TimedRotatingFileHandler(getPath(), "midnight")

    # Set formatter
    handler.setFormatter(formatter)

    # Add rotating handler
    logger.addHandler(handler)

    # Return it
    return logger



def getPath():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        GETPATH
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Define path
    path = (SRC + "{0:04}".format(now.year) + os.sep +
                  "{0:02}".format(now.month) + os.sep +
                  "{0:02}".format(now.day) + os.sep +
                  "loop.log")

    # Return it
    return path



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate loggers
    logger1 = get("1")
    logger2 = get("2")

    # Try logger 1 out
    logger1.debug("Test 1 - DEBUG")
    logger1.info("Test 1 - INFO")
    logger1.warning("Test 1 - WARNING")
    logger1.error("Test 1 - ERROR")
    logger1.critical("Test 1 - CRITICAL")
    
    # Try logger 2 out
    logger2.debug("Test 2 - DEBUG")
    logger2.info("Test 2 - INFO")
    logger2.warning("Test 2 - WARNING")
    logger2.error("Test 2 - ERROR")
    logger2.critical("Test 2 - CRITICAL")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()