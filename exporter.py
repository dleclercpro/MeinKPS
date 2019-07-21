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
from Profiles import (bolus, basal, tb, net, bg, targets, isf, csf, iob, cob,
    idc, resume, suspend)



# Define instances
Logger = logger.Logger("exporter.py")



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
            "net": None,
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

        # Define dates
        today = self.now.date()
        yesterday = today - datetime.timedelta(days = 1)
        then = self.now - datetime.timedelta(hours = 24)

        # Build net insulin profile for last 24 hours
        _net = net.Net()
        _net.build(then, self.now,
            suspend.Suspend(), resume.Resume(), basal.Basal(), tb.TB())

        # Format and store its data
        self.data["net"] = dict(zip(
            [lib.formatTime(T) for T in _net.T],
            [round(y, 2) for y in _net.y]))

        # Get pump data
        self.data["pump"] = reporter.REPORTS["pump"].get()

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

        # Get recent sensor statuses
        self.data["statuses"] = reporter.getDatedEntries(
            reporter.HistoryReport,
            [yesterday, today],
            ["CGM", "Sensor Statuses"])

        # Get recent calibrations
        self.data["calibrations"] = reporter.getDatedEntries(
            reporter.HistoryReport,
            [yesterday, today],
            ["CGM", "Calibrations"])



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
            reporter.path.EXPORTS,
            self.data["bgs"])

        # Fill treatments report
        self.reports["treatments"] = reporter.Report("treatments.json",
            reporter.path.EXPORTS, {
                "Net Basals": self.data["net"],
                "Boluses": self.data["boluses"],
                "IOB": self.data["iobs"]
            })

        # Fill history report
        self.reports["history"] = reporter.Report("history.json",
            reporter.path.EXPORTS,
            lib.mergeDicts(self.data["history"], {
                "CGM": {
                    "Sensor Statuses": self.data["statuses"],
                    "Calibrations": self.data["calibrations"]
                }
            }))

        # Fill pump report
        self.reports["pump"] = reporter.Report("pump.json",
            reporter.path.EXPORTS,
            self.data["pump"])



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