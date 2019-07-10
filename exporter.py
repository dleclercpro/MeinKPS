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
from Profiles import (base, bolus, basal, TB, net, BG, BGTargets, ISF, CSF,
                      IOB, COB, IDC, resume, suspend)



# Define instances
Logger = logger.Logger("exporter.py", "DEBUG")



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
        self.reports = {
            "bgs": None,
            "history": None,
            "treatments": None,
            "pump": None
        }

        # Initialize data
        self.data = {
            "bgs": None,
            "pump": None,
            "net": net.Net(),
            "boluses": None,
            "iobs": None,
            "history": None,
            "statuses": None,
            "calibrations": None
        }



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Reading recent data...")

        # Get recent BGs
        self.data["bgs"] = reporter.getRecent(reporter.BGReport,
            self.now, [], 2)

        # Get pump data
        self.data["pump"] = reporter.PumpReport().get([])

        # Get recent boluses
        self.data["boluses"] = reporter.getRecent(reporter.TreatmentsReport,
            self.now, ["Boluses"], 2)

        # Get recent IOBs
        self.data["iobs"] = reporter.getRecent(reporter.TreatmentsReport,
            self.now, ["IOB"], 2)

        # Get recent history
        self.data["history"] = reporter.getRecent(reporter.HistoryReport,
            self.now, [], 2)

        # Get recent sensor statuses
        self.data["statuses"] = reporter.getRecent(reporter.HistoryReport,
            self.now, ["CGM", "Sensor Statuses"], 2)

        # Get recent calibrations
        self.data["calibrations"] = reporter.getRecent(reporter.HistoryReport,
            self.now, ["CGM", "Calibrations"], 2)



    def fill(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Filling recent data structures...")

        # Fill BG report
        self.reports["bgs"] = reporter.Report("BG.json",
            reporter.PATH_EXPORTS,
            self.data["bgs"])

        # Fill treatments report
        self.reports["treatments"] = reporter.Report("treatments.json",
            reporter.PATH_EXPORTS, {
                "Net Basals": self.data["net"],
                "Boluses": self.data["boluses"],
                "IOB": self.data["iobs"]
            })

        # Fill history report
        self.reports["history"] = reporter.Report("history.json",
            reporter.PATH_EXPORTS,
            lib.mergeDicts(self.data["history"], {
                "CGM": {
                    "Sensor Statuses": self.data["statuses"],
                    "Calibrations": self.data["calibrations"]
                }
            }))

        # Fill pump report
        self.reports["pump"] = reporter.Report("pump.json",
            reporter.PATH_EXPORTS,
            self.data["pump"])



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
        self.data["net"].build(past, self.now,
            suspend.Suspend(), resume.Resume(), basal.Basal(), TB.TB())

        # Format net profile
        self.net = dict(zip([lib.formatTime(T) for T in self.data["net"].T],
                            [round(y, 2) for y in self.data["net"].y]))

        # Get report data
        self.get()

        # Fill reports
        self.fill()

        # Store reports to exports directory
        for report in self.reports.values():
            report.store()



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