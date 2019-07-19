#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    records

    Author:   David Leclerc

    Version:  0.1

    Date:     31.03.2017

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
import errors
import reporter



# Define instances
Logger = logger.Logger("CGM/records.py")



class Record(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize report properties
        self.reportType = None
        self.report = None

        # Initialize record size
        self.size = None

        # Initialize record vectors
        self.t = None
        self.values = None
        self.bytes = None

        # Link with CGM
        self.cgm = cgm



    def find(self, data):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset record vectors
        self.t = []
        self.values = []
        self.bytes = []

        # Compute number of records in data
        n = len(data) / self.size

        # Extract records
        for i in range(n):

            # Extract ith record's bytes
            bytes = data[i * self.size: (i + 1) * self.size]

            # Info
            Logger.debug("Record bytes: " + str(bytes))

            # Store them
            self.bytes.append(bytes)

            # Verify them
            self.verify()

            # Decode them
            self.decode()

        # Store records
        self.store()



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode and compute CRCs
        expectedCRC = lib.unpack(self.bytes[-1][-2:], "<")
        computedCRC = lib.computeCRC16(self.bytes[-1][:-2])

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad record CRC. Expected: " + str(expectedCRC) +
                ". Computed: " + str(computedCRC) + ".")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode local time
        t = (self.cgm.clock.epoch +
             datetime.timedelta(seconds = lib.unpack(self.bytes[-1][4:8], "<")))

        # Store it
        self.t.append(t)



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore if method not implemented
        pass



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore if method not implemented
        pass



class BGRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(BGRecord, self).__init__(cgm)

        # Define record size
        self.size = 13

        # Define dictionary for trends
        self.trends = {1: "90UpUp",
                       2: "90Up",
                       3: "45Up",
                       4: "0",
                       5: "45Down",
                       6: "90Down",
                       7: "90DownDown",
                       8: "None",
                       9: "OutOfRange"}

        # Define dictionary for special values
        self.special = {0: None,
                        1: 'SensorInactive',
                        2: 'MinimalDeviation',
                        3: 'NoAntenna',
                        5: 'SensorInitialization',
                        6: 'DeviationCount',
                        9: 'AbsoluteDeviation',
                        10: 'PowerDeviation',
                        12: 'BadRF'}

        # Define if conversion from mg/dL to mmol/L is needed
        self.convert = True

        # Define report type
        self.reportType = reporter.BGReport



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(BGRecord, self).decode()

        # Decode BG
        BG = lib.unpack(self.bytes[-1][8:10], "<") & 1023

        # Decode trend
        trend = self.trends[self.bytes[-1][10] & 15]

        # Deal with special values
        if BG in self.special:

            # Decode special BG
            BG = self.special[BG]

            # Info
            Logger.info("Special value: " + BG)

        # Deal with normal values
        else:

            # Convert BG units if desired
            if self.convert:

                # Convert them
                BG = round(BG / 18.0, 1)

            # Info
            Logger.info("BG: " + str(BG) + " " + str(trend) + " " +
                        "(" + lib.formatTime(self.t[-1]) + ")")

        # Store them
        self.values.append({"BG": BG, "Trend": trend})



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record dict
        BGs = {}

        # Compute number of decoded records
        n = len(self.t)

        # Filter records
        for i in range(n):

            # Only keep normal (numeric) BG values
            if type(self.values[i]["BG"]) is float:

                # Store them
                BGs[self.t[i]] = self.values[i]["BG"]

            # Print special values
            else:

                # Info
                Logger.info(self.values[i]["BG"] + " (" + str(self.t[i]) + ")")

        # Return them
        return BGs



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding BG records to: " + repr(self.reportType))

        # Add entries
        reporter.setDatedEntries(self.reportType, [], self.filter())



class SensorRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(SensorRecord, self).__init__(cgm)

        # Define record size
        self.size = 15

        # Define possible sensor status
        self.statuses = {1: "Stopped",
                         2: "Expired",
                         3: "ResidualDeviation",
                         4: "CountsDeviation",
                         5: "SecondSession",
                         6: "OffTimeLoss",
                         7: "Started",
                         8: "BadTransmitter",
                         9: "ManufacturingMode"}

        # Define report type
        self.reportType = reporter.HistoryReport



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(SensorRecord, self).decode()

        # Decode sensor status
        status = self.statuses[self.bytes[-1][12]]

        # Store it
        self.values.append(status)

        # Info
        Logger.info("Sensor status: " + str(status) + " " +
                    "(" + lib.formatTime(self.t[-1]) + ")")



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding sensor statuses to: " + repr(self.reportType))

        # Add entries
        reporter.setDatedEntries(self.reportType, ["CGM", "Sensor Statuses"],
            dict(zip(self.t, self.values)))



class CalibrationRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(CalibrationRecord, self).__init__(cgm)

        # Define record size
        self.size = 16

        # Define report type
        self.reportType = reporter.HistoryReport



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(CalibrationRecord, self).decode()

        # Decode BG
        BG = round(lib.unpack(self.bytes[-1][8:10], "<") / 18.0, 1)

        # Store it
        self.values.append(BG)

        # Info
        Logger.info("BG: " + str(BG) + " " + self.cgm.units.value + " " +
                    "(" + lib.formatTime(self.t[-1]) + ")")



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding sensor calibrations to: " + repr(self.reportType))

        # Add entries
        reporter.setDatedEntries(self.reportType, ["CGM", "Calibrations"],
            dict(zip(self.t, self.values)))



class EventRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(EventRecord, self).__init__(cgm)

        # Define record size
        self.size = 20