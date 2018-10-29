#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    exporter

    Author:   David Leclerc

    Version:  0.1

    Date:     07.04.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import logger
import reporter
from Profiles import *



# Define instances
Logger = logger.Logger("exporter.py")
Reporter = reporter.Reporter()



# CLASSES
class Exporter(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.now = None

        # Initialize reports
        self.reports = {"BG": reporter.Report("BG.json"),
                        "history": reporter.Report("history.json"),
                        "treatments": reporter.Report("treatments.json"),
                        "pump": reporter.Report("pump.json")}

        # Initialize net profile
        self.net = net.Net()

        # Initialize recent BGs
        self.BGs = None

        # Initialize recent boluses
        self.boluses = None

        # Initialize recent IOBs
        self.IOBs = None

        # Initialize recent history
        self.history = None

        # Initialize recent sensor statuses
        self.statuses = None

        # Initialize recent sensor calibrations
        self.calibrations = None

        # Initialize pump data
        self.pump = None



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Reading recent data...")

        # Get recent BGs
        self.BGs = Reporter.getRecent(self.now, "BG.json", [])

        # Get recent boluses
        self.boluses = Reporter.getRecent(self.now, "treatments.json",
                                          ["Boluses"])

        # Get recent IOBs
        self.IOBs = Reporter.getRecent(self.now, "treatments.json", ["IOB"])

        # Get recent history
        self.history = Reporter.getRecent(self.now, "history.json", [], 1)

        # Get recent sensor statuses
        self.statuses = Reporter.getRecent(self.now, "history.json",
                                           ["CGM", "Sensor Statuses"])

        # Get recent calibrations
        self.calibrations = Reporter.getRecent(self.now, "history.json",
                                               ["CGM", "Calibrations"])

        # Get pump data
        self.pump = Reporter.get("pump.json", [])



    def fill(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Building recent data structures...")

        # Fill BG report
        self.reports["BG"].update(self.BGs)

        # Fill treatments report
        self.reports["treatments"].update({"Net Basals": self.net,
                                           "Boluses": self.boluses,
                                           "IOB": self.IOBs})

        # Fill history report
        self.reports["history"].update(lib.mergeDicts(self.history, {"CGM": {
            "Sensor Statuses": self.statuses,
            "Calibrations": self.calibrations}}))

        # Fill pump report
        self.reports["pump"].update(self.pump)



    def run(self, now, hours = 24):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store current time
        self.now = now

        # Compute past time
        past = now - datetime.timedelta(hours = hours)

        # Build it for last 24 hours
        self.net.build(past, self.now, suspend.Suspend(), resume.Resume(),
                                       basal.Basal(), TB.TB())

        # Format net profile
        self.net = dict(zip([lib.formatTime(T) for T in self.net.T],
                            [round(y, 2) for y in self.net.y]))

        # Get data
        self.get()

        # Fill reports
        self.fill()

        # Store reports to exports directory
        for report in self.reports.values():

            # Do it
            report.store(Reporter.exp.str)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Initialize exporter
    exporter = Exporter()

    # Run it
    exporter.run(now)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()