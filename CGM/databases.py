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
import reporter
import crc
import commands
import records



# Instanciate logger
Logger = logger.Logger("CGM.databases")



# Constants
DATABASE_HEAD_SIZE = 28
EMPTY_PAGE_RANGE = [lib.unpack([255] * 4, "<")] * 2



class Database(object):

    # Database parameters
    code = None
    recordType = records.Record



    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command(s)
        self.commands = {"ReadDatabaseRange": commands.ReadDatabaseRange(cgm),
                         "ReadDatabase": commands.ReadDatabase(cgm)}

        # Initialize page range
        self.pageRange = None

        # Initialize current page
        self.currentPage = {"Head": None,
                            "Payload": None}

        # Initialize records data
        self.data = []

        # Initialize decoded records
        self.records = []

        # Initialize number of records found in pages
        self.nRecords = 0



    def isEmpty(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ISEMPTY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Check if database is empty.
        """

        # Link to database range command
        command = self.commands["ReadDatabaseRange"]

        # Tell command which database to read from
        command.database = self.code

        # Read range
        command.execute()

        # Decode it
        self.pageRange = [lib.unpack(command.response["Payload"][0:4], "<"),
            lib.unpack(command.response["Payload"][4:8], "<")]

        # Return whether it is empty or not
        return self.pageRange == EMPTY_PAGE_RANGE



    def parsePage(self, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSEPAGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Parse a database page into a head and a payload.
        """

        # Reset database page
        self.currentPage = {"Head": None,
                            "Payload": None}

        # Get page header
        self.currentPage["Head"] = page[:DATABASE_HEAD_SIZE]

        # Get page payload
        self.currentPage["Payload"] = page[DATABASE_HEAD_SIZE:]

        # Parse data, in case record is defined (discard empty bytes)
        if self.recordType is not None:

            # Add number of records in current page to total
            n = page[4]
            self.nRecords += n
            Logger.debug("There are " + str(n) + " record(s) in this page.")

            # Get page data while discarding empty bytes
            self.data.extend(self.currentPage["Payload"][:
                n * self.recordType.size])



    def verifyCRC(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFYCRC
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify database page head CRC.
        """

        # Get and compute header CRCs
        expectedCRC = lib.unpack(self.currentPage["Head"][-2:], "<")
        computedCRC = crc.compute(self.currentPage["Head"][:-2])

        # CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad database page head CRC. Expected: " +
                str(expectedCRC) + ". Computed: " + str(computedCRC) + ".")



    def read(self, n = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Read the database within given page range.
        """

        # Reset database
        self.data = []
        self.records = []
        self.nRecords = 0

        # Database is empty
        if self.isEmpty():
            Logger.warning("Database empty.")
            return

        # Otherwise
        Logger.debug("Database page range: " + str(self.pageRange))

        # Get ends of database range
        [start, end] = self.pageRange[0:2]

        # Compute eventual new lower limit of database range
        if n is not None and start < end - n:
            start = end - n

        # Define command to read database
        command = self.commands["ReadDatabase"]
        command.database = self.code

        # Read database pages
        for i in range(start, end + 1):

            # Info
            Logger.debug("Reading database page " + str(i) + "/" +
                str(end) + "...")

            # Tell command which page to read
            command.page = i

            # Read page
            command.execute()
            page = command.response["Payload"]

            # Parse page: each one of them has a head and a payload
            self.parsePage(page)

            # Verify page CRC
            self.verifyCRC()

        # Extract records from data
        self.findRecords()

        # Store records
        self.storeRecords()



    def findRecords(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FINDRECORDS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Find records in database pages.
        """

        # Info
        Logger.debug("There were a total of " + str(self.nRecords) + " " +
            "record(s) found in the database.")

        # Extract records
        for i in range(self.nRecords):

            # Generate i-th record from corresponding bytes
            record = self.recordType(self.data[i * self.recordType.size :
                (i + 1) * self.recordType.size])

            # Verify its CRC
            record.verifyCRC()

            # Decode it
            record.decode()

            # Store it
            self.records += [record]

            # Show record if it has a string representation
            try:
                Logger.info(record)
            except:
                pass



    def storeRecords(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORERECORDS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Store records found in database.
        """

        pass






class BGDatabase(Database):

    # Database parameters
    code = 4
    recordType = records.BGRecord
    reportType = reporter.BGReport



    def storeRecords(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORERECORDS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding BG records to: " + repr(self.reportType))

        # Initialize values dict
        values = {}

        # Get number of decoded records
        n = len(self.records)

        # Filter them
        for i in range(n):

            # Get value and display time
            value = self.records[i].value
            displayTime = self.records[i].displayTime

            # Only keep normal (numeric) BG values
            if type(value) is float:
                values[displayTime] = value

        # Add entries
        reporter.setDatedEntries(self.reportType, [], values)



class SensorDatabase(Database):

    # Database parameters
    code = 7
    recordType = records.SensorRecord
    reportType = reporter.HistoryReport



    def storeRecords(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORERECORDS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding sensor statuses to: " + repr(self.reportType))

        # Add entries
        reporter.setDatedEntries(self.reportType, ["CGM", "Sensor Statuses"],
            dict([(r.displayTime, r.status) for r in self.records]))



class CalibrationDatabase(Database):

    # Database parameters
    code = 10
    recordType = records.CalibrationRecord
    reportType = reporter.HistoryReport



    def storeRecords(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORERECORDS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding sensor calibrations to: " + repr(self.reportType))

        # Add entries
        reporter.setDatedEntries(self.reportType, ["CGM", "Calibrations"],
            dict([(r.displayTime, r.value) for r in self.records]))



class EventsDatabase(Database):

    # Database parameters
    code = 11
    recordType = records.EventRecord
    reportType = reporter.HistoryReport



class ReceiverDatabase(Database):

    # Database parameters
    code = 8
    recordType = records.ReceiverRecord



class SettingsDatabase(Database):

    # Database parameters
    code = 12
    recordType = records.SettingsRecord



class ManufactureDatabase(Database):

    # Database parameters
    code = 0
    recordType = records.ManufactureRecord



class FirmwareDatabase(Database):

    # Database parameters
    code = 1
    recordType = records.FirmwareRecord



class PCDatabase(Database):

    # Database parameters
    code = 2
    recordType = records.PCRecord