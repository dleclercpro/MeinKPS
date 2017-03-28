#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    cgm

    Author:   David Leclerc

    Version:  0.1

    Date:     08.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import sys
import datetime
import serial



# USER LIBRARIES
import lib
import reporter



# Define a reporter
Reporter = reporter.Reporter()



class CGM(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define vendor
        self.vendor = 0x22a3

        # Define product
        self.product = 0x0047

        # Give CGM a handle
        self.handle = serial.Serial()

        # Give CGM databases
        self.databases = {
            "ManufacturingParameters": ManufacturingParametersDatabase(self),
            "FirmwareSettings": FirmwareSettingsDatabase(self),
            "PCParameterRecord": PCParameterRecordDatabase(self),
            "BG": BGDatabase(self),
            "Sensor": SensorDatabase(self),
            "Receiver": ReceiverDatabase(self),
            "Calibration": CalibrationDatabase(self),
            "Events": EventsDatabase(self),
            "Settings": SettingsDatabase(self)}

        # Give CGM a battery
        self.battery = Battery(self)

        # Give CGM a language
        self.language = Language(self)

        # Give CGM a clock
        self.clock = Clock(self)

        # Give CGM units
        self.units = Units(self)

        # Give CGM a firmware
        self.firmware = Firmware(self)

        # Give CGM a transmitter
        self.transmitter = Transmitter(self)



    def connect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        try:
            # Define handle
            self.handle.port = "/dev/ttyACM0"
            self.handle.baudrate = 115200

            # Open handle
            self.handle.open()

        except:
            sys.exit("Can't connect to CGM. Is it plugged in? Exiting...")



    def disconnect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DISCONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Close handle
        self.handle.close()



    def write(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Sending packet: " + str(bytes)

        # Send packet
        self.handle.write(bytearray(bytes))



    def read(self, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read raw bytes
        rawResponse = self.handle.read(n)

        # Convert raw bytes
        response = [ord(x) for x in rawResponse]

        # Give user info
        print "Received bytes: " + str(response)

        # Return response
        return response



class Packet(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.bytes = None

        # Initialize packet characteristics
        self.size = None
        self.code = None
        self.database = None
        self.page = None



    def build(self, code, database, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet
        self.bytes = []

        # Build database byte
        if database is not None:
            database = [database]

        else:
            database = []

        # Build page bytes
        if page is not None:
            page = lib.unpack(page, 4)
            page.append(1)

        else:
            page = []

        # Build packet
        self.bytes.extend([1, 0, 0])
        self.bytes.append(code)
        self.bytes.extend(database)
        self.bytes.extend(page)

        # Build size byte
        size = len(self.bytes) + 2

        # Update packet
        self.bytes[1] = size

        # Build CRC bytes
        CRC = lib.computeCRC16(self.bytes)
        CRC = lib.unpack(CRC, 2)

        # Finish packet
        self.bytes.extend(CRC)

        # Store packet characteristics
        self.size = size
        self.code = code
        self.database = database
        self.page = page



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return packet
        return self.bytes



class Request(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize request code byte
        self.code = None

        # Initialize request database byte
        self.database = None

        # Initialize request page byte
        self.page = None

        # Initialize request response
        self.response = None

        # Give the request a packet
        self.packet = Packet()

        # Link with CGM
        self.cgm = cgm



    def execute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXECUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset response
        self.response = {"Head": None,
                         "Body": None,
                         "CRC": None}

        # Prepare packet
        self.packet.build(self.code, self.database, self.page)

        # Send packet
        self.cgm.write(self.packet.bytes)

        # First read
        self.response["Head"] = self.cgm.read(4)

        # Compute number of bytes received
        nBytesReceived = lib.pack(self.response["Head"][1:3])

        # Minimum number of bytes received: 6
        if nBytesReceived > 6:
            nBytesReceived -= 6

        # Second read
        self.response["Body"] = self.cgm.read(nBytesReceived)

        # Try and find XML structure in response
        print "XML: " + str(lib.XMLify(self.response["Body"]))

        # Third read
        self.response["CRC"] = self.cgm.read(2)

        # Verify response
        self.verify()



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get and compute response CRCs
        expectedCRC = lib.pack(self.response["CRC"])
        computedCRC = lib.computeCRC16(self.response["Head"] +
                                       self.response["Body"])

        # Give user info
        print "Expected CRC: " + str(expectedCRC)
        print "Computed CRC: " + str(computedCRC)

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:

            # Give user info
            sys.exit("Expected and computed CRCs do not match. Exiting...")



class ReadDatabaseRangeRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 16



class ReadDatabaseRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 17



class ReadFirmwareHeaderRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 11



class ReadTransmitterIDRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 25



class ReadFirmwareSettingsRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 54



class ReadBatteryLevelRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 33



class ReadBatteryStateRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 48



class ReadLanguageRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 27



class ReadSystemTimeRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 34



class ReadClockModeRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 41



class ReadUnitsRequest(Request):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize request code
        self.code = 37



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

        # Initialize database range
        self.range = None

        # Initialize database number of pages
        self.n = None

        # Initialize database page
        self.page = None

        # Initialize database data
        self.data = None

        # Define response head size
        self.headSize = 28

        # Define empty range response
        self.emptyRange = [lib.pack([255] * 4)] * 2

        # Define request(s)
        self.requests = {"ReadDatabaseRange": ReadDatabaseRangeRequest(cgm),
                         "ReadDatabase": ReadDatabaseRequest(cgm)}

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

        # Link to database range request
        request = self.requests["ReadDatabaseRange"]

        # Tell request which database to read from
        request.database = self.code

        # Read range
        request.execute()

        # Decode it
        self.range.append(lib.pack(request.response["Body"][0:4]))
        self.range.append(lib.pack(request.response["Body"][4:8]))

        # Deal with empty database
        if self.range == self.emptyRange:

            # Give user info
            print "Database empty."

            return False

        else:

            # Give user info
            print "Database range: " + str(self.range)

            return True



    def read(self):

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

            # Link to read database request
            request = self.requests["ReadDatabase"]

            # Tell request which database to read from
            request.database = self.code

            # Read database
            for i in range(start, end + 1):

                # Reset database page
                self.page = {"Header": None, "Data": None}

                # Give user info
                print "Reading database page " + str(i) + "/" + str(end) + "..."

                # Tell request which page to read
                request.page = i

                # Read page
                request.execute()

                # Get page
                self.page["Header"] = request.response["Body"][:self.headSize]
                self.page["Data"] = request.response["Body"][self.headSize:]
                
                # Extend database
                self.data.extend(self.page["Data"])

                # Verify page
                self.verify()

                # Get number of records in page
                self.n = self.page["Header"][4]

                # Give user info
                print "Number of records in page: " + str(self.n)

                # Extract records from page if defined
                if self.record is not None:
                    self.record.find(self.page["Data"], self.n)



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to header
        header = self.page["Header"]

        # Get and compute header CRCs
        expectedCRC = lib.pack(header[-2:])
        computedCRC = lib.computeCRC16(header[:-2])

        # Give user info
        print "Expected header CRC: " + str(expectedCRC)
        print "Computed header CRC: " + str(computedCRC)

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:

            # Give user info
            sys.exit("Expected and computed header CRCs do not match. " +
                     "Exiting...")



class ManufacturingParametersDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 0



class FirmwareSettingsDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 1



class PCParameterRecordDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 2



class BGDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 4

        # Link with record
        self.record = BGRecord(cgm)



class SensorDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 7

        # Link with record
        self.record = SensorRecord(cgm)



class ReceiverDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 8



class CalibrationDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 10

        # Link with record
        self.record = CalibrationRecord(cgm)



class EventsDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 11

        # Link with record
        self.record = EventRecord(cgm)



class SettingsDatabase(Database):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Define database code
        self.code = 12



class Record(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record vectors
        self.t = None
        self.values = None
        self.bytes = None

        # Link with CGM
        self.cgm = cgm



    def find(self, page, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset record vectors
        self.t = []
        self.values = []
        self.bytes = []

        # Extract records from page
        for i in range(n):

            # Extract ith record's bytes
            bytes = page[i * self.size: (i + 1) * self.size]

            # Give user info
            print "Record bytes: " + str(bytes)

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
        expectedCRC = lib.pack(self.bytes[-1][-2:])
        computedCRC = lib.computeCRC16(self.bytes[-1][:-2])

        # Give user info
        print "Expected CRC: " + str(expectedCRC)
        print "Computed CRC: " + str(computedCRC)

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:

            # Give user info
            sys.exit("Expected and computed CRCs do not match. Exiting...")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode local time
        t = (datetime.timedelta(seconds = lib.pack(self.bytes[-1][4:8])) +
             self.cgm.clock.epoch)

        # Format it
        t = lib.formatTime(t)

        # Store it
        self.t.append(t)

        # Give user info
        print "Time: " + str(t)



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

        # Define record size
        self.size = 13

        # Define dictionary for trends
        self.trends = {1: "↑↑",
                       2: "↑",
                       3: "↗",
                       4: "→",
                       5: "↘",
                       6: "↓",
                       7: "↓↓",
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
        BG = lib.pack(self.bytes[-1][8:10]) & 1023

        # Deal with special values
        if BG in self.special:

            # Give user info
            print "Special value: " + self.special[BG]

        else:

            # Convert BG units if desired
            if self.convert:
                BG = round(BG / 18.0, 1)

            # Decode trend
            trend = self.trends[self.bytes[-1][10] & 15]

            # Store them
            self.values.append({"BG": BG, "Trend": trend})

            # Give user info
            print "BG: " + str(BG) + " " + str(trend)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "BG.json"

        # Give user info
        print "Adding BG records to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Get number of records found
        n = len(self.values)

        # Add entries
        for i in range(n):
            Reporter.addEntry([], self.t[i], self.values[i]["BG"])



class SensorRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

        # Define record size
        self.size = 15



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Decode sensor event
        if self.bytes[-1][12] == 7:
            event = "Start"

        elif self.bytes[-1][12] == 1:
            event = "Stop" 

        # Store it
        self.values.append(event)

        # Give user info
        print "Sensor event: " + str(event)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Adding sensor events to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Get number of records found
        n = len(self.values)

        # Add entries
        for i in range(n):
            Reporter.addEntry(["Sensor Events"],
                              self.t[i], self.values[i])



class CalibrationRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__(cgm)

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
        BG = round(lib.pack(self.bytes[-1][8:10]) / 18.0, 1)

        # Store it
        self.values.append(BG)

        # Give user info
        print "BG: " + str(BG) + " " + self.cgm.units.value



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Adding sensor calibrations to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Get number of records found
        n = len(self.values)

        # Add entries
        for i in range(n):
            Reporter.addEntry(["Calibrations"], self.t[i], self.values[i])



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



class Battery(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.t = None

        # Initialize battery level
        self.level = None

        # Initialize battery state
        self.state = None

        # Define battery states
        self.states = {1: "Charging",
                       2: "NotCharging",
                       3: "NTCFault",
                       4: "BadBattery"}

        # Define request(s)
        self.requests = {"ReadLevel": ReadBatteryLevelRequest(cgm),
                         "ReadState": ReadBatteryStateRequest(cgm)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current time
        self.t = datetime.datetime.now()

        # Format current time
        self.t = lib.formatTime(self.t)

        # Link to request
        request = self.requests["ReadLevel"]

        # Execute request
        request.execute()

        # Assign response
        self.level = str(lib.pack(request.response["Body"])) + "%"

        # Give user info
        print "Battery level: " + self.level

        # Link to battery state request
        request = self.requests["ReadState"]

        # Execute request
        request.execute()

        # Assign response
        self.state = self.states[lib.pack(request.response["Body"])]

        # Give user info
        print "Battery state: " + self.state

        # Store battery level
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Storing BG units to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Add entry
        Reporter.addEntry(["Battery Levels"], self.t, self.level)



class Language(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Define languages
        self.values = {1029: "Czech",
                       1030: "Danish",
                       1031: "German",
                       1033: "English",
                       1034: "Spanish",
                       1035: "Finnish",
                       1036: "French (FR)",
                       1038: "Hungarian",
                       1040: "Italian",
                       1043: "Dutch",
                       1044: "Norwegian",
                       1045: "Polish",
                       1046: "Portuguese",
                       1053: "Swedish",
                       1055: "Turkish",
                       3084: "French (CA)"}

        # Define request(s)
        self.request = ReadLanguageRequest(cgm)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to request
        request = self.request

        # Execute request
        request.execute()

        # Assign response
        self.value = self.values[lib.pack(request.response["Body"])]

        # Give user info
        print "Language: " + self.value

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Storing language to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Add entry
        Reporter.addEntry([], "Language", self.value, True)



class Clock(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize system time
        self.systemTime = None

        # Initialize mode
        self.mode = None

        # Define modes
        self.modes = {0: "24h", 1: "AM/PM"}

        # Define epoch
        self.epoch = datetime.datetime(2009, 1, 1)

        # Define request(s)
        self.requests = {"ReadSystemTime": ReadSystemTimeRequest(cgm),
                         "ReadMode": ReadClockModeRequest(cgm)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to request
        request = self.requests["ReadSystemTime"]

        # Execute request
        request.execute()

        # Compute time delta since epoch
        delta = datetime.timedelta(seconds = lib.pack(request.response["Body"]))

        # Assign response
        self.systemTime = self.epoch + delta

        # Give user info
        print "System time: " + str(self.systemTime)

        # Link to request
        request = self.requests["ReadMode"]

        # Execute request
        request.execute()

        # Assign response
        self.mode = self.modes[lib.pack(request.response["Body"])]

        # Give user info
        print "Clock mode: " + self.mode

        # Store clock mode
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Storing clock mode to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Add entry
        Reporter.addEntry([], "Clock Mode", self.mode, True)



class Units(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value to default
        self.value = "mmol/L"

        # Define values
        self.values = {1: "mg/dL", 2: "mmol/L"}

        # Define request(s)
        self.request = ReadUnitsRequest(cgm)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to request
        request = self.request

        # Execute request
        request.execute()

        # Assign response
        self.value = self.values[lib.pack(request.response["Body"])]

        # Give user info
        print "Units: " + self.value

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Storing BG units to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Add entry
        Reporter.addEntry([], "Units", self.value, True)



class Firmware(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request(s)
        self.requests = {"ReadHeader": ReadFirmwareHeaderRequest(cgm),
                         "ReadSettings": ReadFirmwareSettingsRequest(cgm)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to request
        request = self.requests["ReadHeader"]

        # Execute request
        request.execute()

        # Link to request
        request = self.requests["ReadSettings"]

        # Execute request
        request.execute()



class Transmitter(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize ID
        self.id = None

        # Define request(s)
        self.request = ReadTransmitterIDRequest(cgm)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to request
        request = self.request

        # Execute request
        request.execute()

        # Assign response
        self.id = lib.translate(request.response["Body"])

        # Give user info
        print "Transmitter ID: " + str(self.id)

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report
        report = "CGM.json"

        # Give user info
        print "Storing current transmitter ID to report: '" + report + "'..."

        # Load report
        Reporter.load(report)

        # Add entry
        Reporter.addEntry([], "Transmitter ID", self.id, True)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate CGM
    cgm = CGM()

    # Establish connection with CGM
    cgm.connect()

    # Read battery
    cgm.battery.read()

    # Read language
    cgm.language.read()

    # Read clock
    cgm.clock.read()

    # Read units
    cgm.units.read()

    # Read firmware
    cgm.firmware.read()

    # Read transmitter
    cgm.transmitter.read()

    # Read databases
    cgm.databases["ManufacturingParameters"].read()
    cgm.databases["FirmwareSettings"].read()
    cgm.databases["PCParameterRecord"].read()
    cgm.databases["BG"].read()
    cgm.databases["Sensor"].read()
    cgm.databases["Receiver"].read()
    cgm.databases["Calibration"].read()
    cgm.databases["Events"].read()
    cgm.databases["Settings"].read()

    # End connection with CGM
    cgm.disconnect()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
