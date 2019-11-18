#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    databases

    Author:   David Leclerc

    Version:  0.1

    Date:     31.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import lib
import logger
import crc
import commands
import records



# Instanciate logger
Logger = logger.Logger("CGM.databases")



class Database(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize database code
        self.code = None

        # Initialize database record
        self.record = None

        # Initialize XML boolean
        self.xml = False

        # Initialize database range
        self.range = None

        # Initialize database page
        self.page = None

        # Initialize database data
        self.data = None

        # Define response head size
        self.headSize = 28

        # Define empty range response
        self.emptyRange = [lib.unpack([255] * 4, "<")] * 2

        # Define command(s)
        self.commands = {"ReadDatabaseRange": commands.ReadDatabaseRange(cgm),
                         "ReadDatabase": commands.ReadDatabase(cgm)}

        # Link with CGM
        self.cgm = cgm



    def measure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MEASURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset database range
        self.range = []

        # Link to database range command
        command = self.commands["ReadDatabaseRange"]

        # Tell command which database to read from
        command.database = self.code

        # Read range
        command.execute()

        # Decode it
        self.range.append(lib.unpack(command.response["Payload"][0:4], "<"))
        self.range.append(lib.unpack(command.response["Payload"][4:8], "<"))

        # Deal with empty database
        if self.range == self.emptyRange:
            Logger.warning("Database empty.")
            return False

        else:
            Logger.debug("Database range: " + str(self.range))
            return True



    def parse(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset database page
        self.page = {"Header": None, "Data": None}

        # Get page header
        self.page["Header"] = bytes[:self.headSize]

        # Parse data, in case record is defined (discard empty bytes)
        if self.record is not None:

            # Get number of records in current page
            n = bytes[4]
            Logger.debug("There are " + str(n) + " records in this page.")

            # Get page data
            self.page["Data"] = bytes[self.headSize:
                                      self.headSize + n * self.record.size]

        else:

            # Get page data
            self.page["Data"] = bytes[self.headSize:]
        
        # Extend data
        self.data.extend(self.page["Data"])



    def read(self, n = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset database data
        self.data = []

        # Read database range and read database if not empty
        if self.measure():

            # Get ends of database range
            start = self.range[0]
            end = self.range[1]

            # Compute eventual new lower limit of database range
            if n is not None and start < end - n:

                # Assign new limit
                start = end - n

            # Link to read database command
            command = self.commands["ReadDatabase"]

            # Tell command which database to read from
            command.database = self.code

            # Read database
            for i in range(start, end + 1):

                # Info
                Logger.debug("Reading database page " + str(i) + "/" +
                             str(end) + "...")

                # Tell command which page to read
                command.page = i

                # Read page
                command.execute()

                # Parse page
                self.parse(command.response["Payload"])

                # Verify page
                self.verify()

            # Extract defined records from data
            if self.record is not None:

                # Find them
                Logger.debug("Trying to find records in: " + str(self.data))
                self.record.find(self.data)



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get and compute header CRCs
        expectedCRC = lib.unpack(self.page["Header"][-2:], "<")
        computedCRC = crc.compute(self.page["Header"][:-2])

        # CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad header CRC. Expected: " + str(expectedCRC) +
                ". Computed: " + str(computedCRC) + ".")



class BGDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(BGDatabase, self).__init__(cgm)

        # Define database code
        self.code = 4

        # Link with record
        self.record = records.BGRecord(cgm)



class SensorDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(SensorDatabase, self).__init__(cgm)

        # Define database code
        self.code = 7

        # Link with record
        self.record = records.SensorRecord(cgm)



class ReceiverDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(ReceiverDatabase, self).__init__(cgm)

        # Define database code
        self.code = 8

        # Link with record
        self.record = records.ReceiverRecord(cgm)



class CalibrationDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(CalibrationDatabase, self).__init__(cgm)

        # Define database code
        self.code = 10

        # Link with record
        self.record = records.CalibrationRecord(cgm)



class EventsDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(EventsDatabase, self).__init__(cgm)

        # Define database code
        self.code = 11

        # Link with record
        self.record = records.EventRecord(cgm)



class SettingsDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(SettingsDatabase, self).__init__(cgm)

        # Define database code
        self.code = 12

        # Link with record
        self.record = records.SettingsRecord(cgm)



class ManufactureDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(ManufactureDatabase, self).__init__(cgm)

        # Define database code
        self.code = 0

        # Link with record
        self.record = records.ManufactureRecord(cgm)



class FirmwareDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FirmwareDatabase, self).__init__(cgm)

        # Define database code
        self.code = 1

        # Link with record
        self.record = records.FirmwareRecord(cgm)



class PCDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PCDatabase, self).__init__(cgm)

        # Define database code
        self.code = 2

        # Link with record
        self.record = records.PCRecord(cgm)