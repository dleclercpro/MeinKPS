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
import reporter



# Define instances
Logger = logger.Logger("CGM/records.py")
Reporter = reporter.Reporter()



class Record(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record's report
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

            # Give user info
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

            # Raise error
            raise errors.BadCGMRecordCRC(expectedCRC, computedCRC)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode local time
        t = (datetime.timedelta(seconds =
                                lib.unpack(self.bytes[-1][4:8], "<")) +
                                self.cgm.clock.epoch)

        # Store it
        self.t.append(t)

        # Give user info
        Logger.info("Time: " + str(t))



    def filter(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FILTER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



class BGRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

        # Define record's report
        self.report = "BG.json"

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



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Decode BG
        BG = lib.unpack(self.bytes[-1][8:10], "<") & 1023

        # Decode trend
        trend = self.trends[self.bytes[-1][10] & 15]

        # Deal with special values
        if BG in self.special:

            # Decode special BG
            BG = self.special[BG]

            # Give user info
            Logger.info("Special value: " + BG)

        # Deal with normal values
        else:

            # Convert BG units if desired
            if self.convert:
                BG = round(BG / 18.0, 1)

            # Give user info
            Logger.info("BG: " + str(BG) + " " + str(trend))

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

                # Give user info
                Logger.info(self.values[i]["BG"] + " (" + str(self.t[i]) + ")")

        # Return them
        return BGs



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Adding BG records to report: '" + self.report + "'...")

        # Add entries
        Reporter.add(self.report, [], self.filter())



class SensorRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

        # Define record's report
        self.report = "history.json"

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



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Decode sensor status
        status = self.statuses[self.bytes[-1][12]]

        # Store it
        self.values.append(status)

        # Give user info
        Logger.info("Sensor status: " + str(status))



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Adding sensor statuses to report: '" + self.report +
                     "'...")

        # Add entries
        Reporter.add(self.report, ["CGM", "Sensor Statuses"],
                     dict(zip(self.t, self.values)))



class CalibrationRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

        # Define record's report
        self.report = "history.json"

        # Define record size
        self.size = 16



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Decode BG
        BG = round(lib.unpack(self.bytes[-1][8:10], "<") / 18.0, 1)

        # Store it
        self.values.append(BG)

        # Give user info
        Logger.info("BG: " + str(BG) + " " + self.cgm.units.value)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Adding sensor calibrations to report: '" + self.report +
                     "'...")

        # Add entries
        Reporter.add(self.report, ["CGM", "Calibrations"],
                     dict(zip(self.t, self.values)))



class EventRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

        # Define record size
        self.size = 20



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()
