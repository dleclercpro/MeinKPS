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
import idc
from Profiles import net, bg, targets, isf, csf, iob, cob



# Define instances
Logger = logger.Logger("exporter")



# CONSTANTS
MAX_SENSOR_AGE = 10 # days
N_MONTH_DAYS   = 30 # days



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
            "pump": None,
            "errors": None,
        }

        # Initialize data
        self.data = {
            "bgs": None,
            "pump": None,
            "net": None,
            "boluses": None,
            "iobs": None,
            "history": None,
            "statuses": None,
            "calibrations": None,
            "errors": None,
        }



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Reading recent data...")

        # Define dates
        today = self.now.date()
        yesterday = today - datetime.timedelta(days = 1)
        then = self.now - datetime.timedelta(hours = 24)

        # Build net insulin profile for last 24 hours
        _net = net.Net()
        _net.build(then, self.now, False)

        # Format and store its data
        self.data["net"] = dict(zip(
            [lib.formatTime(T) for T in _net.T],
            [round(y, 2) for y in _net.y]))

        # Get pump data
        self.data["pump"] = reporter.getPumpReport().get()

        # Get recent BGs
        self.data["bgs"] = reporter.getDatedEntries(
            reporter.BGReport,
            [yesterday, today],
            [])

        # Get recent boluses
        self.data["boluses"] = reporter.getDatedEntries(
            reporter.TreatmentsReport,
            [yesterday, today],
            ["Boluses"])

        # Get recent IOBs
        self.data["iobs"] = reporter.getDatedEntries(
            reporter.TreatmentsReport,
            [yesterday, today],
            ["IOB"])

        # Get recent history
        self.data["history"] = reporter.getDatedEntries(
            reporter.HistoryReport,
            [yesterday, today],
            [])

        # Get recent sensor statuses (last session)
        # With n = 1, only today's history report would be considered, thus + 1
        self.data["statuses"] = reporter.getRecentDatedEntries(
            reporter.HistoryReport,
            self.now,
            ["CGM", "Sensor Statuses"],
            MAX_SENSOR_AGE + 1)

        # Get recent calibrations
        self.data["calibrations"] = reporter.getDatedEntries(
            reporter.HistoryReport,
            [yesterday, today],
            ["CGM", "Calibrations"])

        # Get recent errors
        self.data["errors"] = reporter.getDatedEntries(
            reporter.ErrorsReport,
            [today],
            [])



    def fill(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Filling recent data structures...")

        # Fill separate BG report
        self.reports["bgs"] = reporter.Report("BG.json",
            reporter.path.EXPORTS,
            self.data["bgs"])

        # Fill separate treatments report
        self.reports["treatments"] = reporter.Report("treatments.json",
            reporter.path.EXPORTS, {
                "Net Basals": self.data["net"],
                "Boluses": self.data["boluses"],
                "IOB": self.data["iobs"]
            })

        # Fill separate history report
        self.reports["history"] = reporter.Report("history.json",
            reporter.path.EXPORTS,
            lib.mergeDicts(self.data["history"], {
                "CGM": {
                    "Sensor Statuses": self.data["statuses"],
                    "Calibrations": self.data["calibrations"]
                }
            }))

        # Fill separate pump report
        self.reports["pump"] = reporter.Report("pump.json",
            reporter.path.EXPORTS,
            self.data["pump"])
        
        # Fill separate errors report
        self.reports["errors"] = reporter.Report("errors.json",
            reporter.path.EXPORTS,
            self.data["errors"])



    def run(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store current time
        self.now = now

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