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
import time



# USER LIBRARIES
import lib



# CONSTANTS
specialBG = {1: "SensorNotActive",
             2: "MinimalDeviation",
             3: "NoAntenna",
             5: "SensorNotCalibrated",
             6: "CountsDeviation",
             9: "AbsoluteDeviation",
             10: "PowerDeviation",
             12: "BadRF"}



class CGM(object):

    # CGM CHARACTERISTICS
    vendor  = 0x22a3
    product = 0x0047

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize handle
        self.handle = serial.Serial()

        # Give CGM a packet
        self.packet = Packet(self)

        # Initialize CGM response
        self.response = None

        # Give CGM databases
        self.databases = {"ManufacturingParameters": ManufacturingParametersDatabase(self),
                          "FirmwareSettings": FirmwareSettingsDatabase(self),
                          "PCParameterRecord": PCParameterRecordDatabase(self),
                          "Sensor": SensorDatabase(self),
                          "BG": BGDatabase(self),
                          "Calibration": CalibrationDatabase(self),
                          "Insertion": InsertionDatabase(self),
                          "Receiver": ReceiverDatabase(self),
                          "Meter": MeterDatabase(self),
                          "UserSettings": UserSettingsDatabase(self)}

        # Give CGM commands
        self.commands = {"ReadFirmwareHeader": 11,
                         "ReadDatabaseRange": 16,
                         "ReadDatabase": 17,
                         "ReadTransmitterID": 25,
                         "ReadLanguage": 27,
                         "ReadBatteryLevel": 33,
                         "ReadSystemTime": 34,
                         "ReadBGU": 37,
                         "ReadClockMode": 41,
                         "ReadBatteryState": 48,
                         "ReadFirmwareSettings": 54}

        # Give CGM a battery
        self.battery = Battery(self)

        # Give CGM a language
        self.language = Language(self)

        # Give CGM a clock
        self.clock = Clock(self)

        # Give CGM BG units
        self.BGU = BGU(self)

        # Give CGM a firmware
        self.firmware = Firmware(self)



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



    def write(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send packet
        self.handle.write(bytearray(self.packet.bytes))

        # Give user info
        print "Sent packet: " + str(self.packet.bytes)



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



    def ask(self, XML = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ASK
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset response
        self.response = {"Head": None,
                         "Body": None,
                         "CRC": None}

        # Send command packet
        self.write()

        # First read
        self.response["Head"] = self.read(4)

        # Compute number of bytes received
        nBytesReceived = pack(self.response["Head"][1:3])

        # Minimum number of bytes received: 6
        if nBytesReceived > 6:
            nBytesReceived -= 6

        # Second read
        self.response["Body"] = self.read(nBytesReceived)

        # Third read
        self.response["CRC"] = self.read(2)

        # CRC computation and verification
        expectedCRC = pack(self.response["CRC"])
        computedCRC = lib.computeCRC16(self.response["Head"] +
                                       self.response["Body"])

        # Give user info
        print "Expected CRC: " + str(expectedCRC)
        print "Computed CRC: " + str(computedCRC)

        # Translate response to XML if desired
        if XML:
            print XMLify(self.response["Body"])



class Packet(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.bytes = None

        # Initialize packet characteristics
        self.size = None
        self.command = None
        self.database = None
        self.page = None
        self.CRC = None

        # Link with CGM
        self.cgm = cgm



    def build(self, command, database = None, page = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet
        self.bytes = [1, 0, 0]

        # Build command byte
        command = self.cgm.commands[command]

        # Build database byte
        if database is not None:
            database = [database]

        else:
            database = []

        # Build page bytes
        if page is not None:
            page = unpack(page, 4)
            page.append(1)

        else:
            page = []

        # Build packet
        self.bytes.append(command)
        self.bytes.extend(database)
        self.bytes.extend(page)

        # Build size byte
        size = len(self.bytes) + 2

        # Update packet
        self.bytes[1] = size

        # Build CRC bytes
        CRC = lib.computeCRC16(self.bytes)
        CRC = unpack(CRC, 2)

        # Finish packet
        self.bytes.extend(CRC)

        # Store packet characteristics
        self.size = size
        self.command = command
        self.database = database
        self.page = page
        self.CRC = CRC



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return packet
        return self.bytes



class Database(object):

    # DATABASE CHARACTERISTICS
    headerSize = 28

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize database data
        self.data = None

        # Initialize database range
        self.range = None

        # Initialize database code
        self.code = None

        # Initialize database record
        self.record = None

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

        # Prepare command packet
        self.cgm.packet.build("ReadDatabaseRange", self.code)

        # Read database range
        self.cgm.ask()

        # Decode database range
        self.range.append(pack(self.cgm.response["Body"][0:4]))
        self.range.append(pack(self.cgm.response["Body"][4:8]))

        # Give user info
        print "Database range: " + str(self.range)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset database data
        self.data = []

        # Get database range for selected database
        self.measure()

        # Get ends of database range
        start = self.range[0]
        end = self.range[1]

        # Read database
        for i in range(start, end + 1):

            # Give user info
            print "Reading database page " + str(i) + "/" + str(end) + "..."

            # Build packet to read page i
            self.cgm.packet.build("ReadDatabase", self.code, i)

            # Read page i
            self.cgm.ask()

            # Get page i
            page = self.cgm.response["Body"]

            # Extract page header
            header = page[:self.headerSize]

            # Get number of records in page
            n = header[4]

            # Get CRC
            CRC = header[-2:]

            # Give user info
            print "Number of records in page: " + str(n)
            print "Header CRC: " + str(CRC)

            # Get actual page of data
            page = page[self.headerSize:]
            
            # Extend database
            self.data.extend(page)

            # Extract records from page if defined
            if self.record is not None:
                self.record.find(page, n)



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
        self.code = 3

        # Link with record
        self.record = SensorRecord(cgm)



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
        self.code = 5



class InsertionDatabase(Database):

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
        self.record = InsertionRecord(cgm)



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



class MeterDatabase(Database):

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



class UserSettingsDatabase(Database):

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

        # Initialize last record vector
        self.last = None

        # Initialize all records vector
        self.all = None

        # Link with CGM
        self.cgm = cgm



    def find(self, page, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset record vectors
        self.last = None
        self.all = []

        # Extract records from page
        for i in range(n):

            # Extract ith record
            bytes = page[i * self.size: (i + 1) * self.size]

            # Store it as current record
            self.last = bytes

            # Store it with rest of records
            self.all.append(bytes)

            # Decode it
            self.decode()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Extract system time
        systemTime = datetime.timedelta(seconds = pack(self.last[0:4]))
        systemTime += self.cgm.clock.epoch

        # Extract local time
        localTime = datetime.timedelta(seconds = pack(self.last[4:8]))
        localTime += self.cgm.clock.epoch

        # Give user info
        print "Record: " + str(self.last)
        print "System time: " + str(systemTime)
        print "Local time: " + str(localTime)



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

        # Initialize record values
        self.BG = None
        self.trendArrow = None

        # Define dictionary for trend arrows
        self.trendArrows = {1: "↑↑",
                            2: "↑",
                            3: "↗",
                            4: "→",
                            5: "↘",
                            6: "↓",
                            7: "↓↓",
                            8: "NotComputable",
                            9: "OutOfRange"}



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Extract BG
        if self.last[8] != 5:
            self.BG = round(self.last[8] / 18.0, 1)

        # Extract trend arrow
        self.trendArrow = self.trendArrows[self.last[10] & 15]

        # Give user info
        print "BG: " + str(self.BG)
        print "Trend arrow: " + str(self.trendArrow)



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
        self.size = 20



class InsertionRecord(Record):

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

        # Initialize type
        self.type = None



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode()

        # Decode insertion type
        if self.last[12] == 7:
            self.type = "Start"

        elif self.last[12] == 1:
            self.type = "Stop"

        # Give user info
        print "Sensor: " + str(self.type)



class Battery(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize battery level
        self.level = None

        # Initialize battery state
        self.state = None

        # Define battery states
        self.states = {1: "Charging",
                       2: "NotCharging",
                       3: "NTCFault",
                       4: "BadBattery"}

        # Link with CGM
        self.cgm = cgm



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Request battery level
        self.cgm.packet.build("ReadBatteryLevel")
        self.cgm.ask()

        # Store it
        self.level = str(pack(self.cgm.response["Body"])) + "%"

        # Give user info
        print "Battery level: " + self.level

        # Request battery state
        self.cgm.packet.build("ReadBatteryState")
        self.cgm.ask()

        # Store it
        self.state = self.states[pack(self.cgm.response["Body"])]

        # Give user info
        print "Battery state: " + self.state



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

        # Link with CGM
        self.cgm = cgm



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Request language
        self.cgm.packet.build("ReadLanguage")
        self.cgm.ask()

        # Store it
        self.value = self.values[pack(self.cgm.response["Body"])]

        # Give user info
        print "Language: " + self.value



class Clock(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize mode
        self.mode = None

        # Initialize system time
        self.systemTime = None

        # Define epoch
        self.epoch = datetime.datetime(2009, 1, 1)

        # Define modes
        self.modes = {0: "24h", 1: "AM/PM"}

        # Link with CGM
        self.cgm = cgm



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Request system time
        self.cgm.packet.build("ReadSystemTime")
        self.cgm.ask()

        # Compute time delta since epoch
        delta = datetime.timedelta(seconds = pack(self.cgm.response["Body"]))

        # Store it
        self.systemTime = self.epoch + delta

        # Give user info
        print "System time: " + str(self.systemTime)

        # Request mode
        self.cgm.packet.build("ReadClockMode")
        self.cgm.ask()

        # Store it
        self.mode = self.modes[pack(self.cgm.response["Body"])]

        # Give user info
        print "Clock mode: " + self.mode



class BGU(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Define values
        self.values = {1: "mg/dL", 2: "mmol/L"}

        # Link with CGM
        self.cgm = cgm



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Request system time
        self.cgm.packet.build("ReadBGU")
        self.cgm.ask()

        # Store it
        self.value = self.values[pack(self.cgm.response["Body"])]

        # Give user info
        print "BGU: " + self.value



class Firmware(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with CGM
        self.cgm = cgm



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """



def unpack(x, n):

    # Initialize bytes
    bytes = []

    # Unpack x in n bytes
    for i in range(n):

        # Compute ith byte
        bytes.append((x / 256 ** i) % 256)

    return bytes



def pack(bytes):

    # Initialize result
    x = 0

    # Pack bytes in x
    for i in range(len(bytes)):

        # Add ith byte
        x += bytes[i] * 256 ** i

    return x



def translate(bytes):

    return "".join([chr(x) for x in bytes])



def XMLify(bytes):

    # Get number of bytes
    n = len(bytes)

    # Translate bytes
    bytes = translate(bytes)

    # Extract XML structure from bytes
    a = 0
    b = 0
    begun = False

    for i in range(n):

        if bytes[i] == "<" and not begun :
            a = i
            begun = True

        if bytes[i] == ">":
            b = i + 1

    return bytes[a:b]



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
    #cgm.battery.read()

    # Read language
    #cgm.language.read()

    # Read clock
    #cgm.clock.read()

    # Read BGU
    #cgm.BGU.read()

    # Read databases
    #cgm.databases["ManufacturingParameters"].read()
    #cgm.databases["FirmwareSettings"].read()
    #cgm.databases["PCParameterRecord"].read()
    #cgm.databases["Sensor"].read()
    #cgm.databases["BG"].read()
    #cgm.databases["Calibration"].read()
    #cgm.databases["Insertion"].read()
    #cgm.databases["Receiver"].read()
    #cgm.databases["Meter"].read()
    #cgm.databases["UserSettings"].read()

    # FIXME
    #cgm.packet.build("ReadFirmwareHeader")
    #cgm.ask(True)
    #cgm.packet.build("ReadTransmitterID")
    #cgm.ask()
    #print translate(cgm.response["Body"])
    #cgm.packet.build("ReadFirmwareSettings")
    #cgm.ask(True)

    # End connection with CGM
    cgm.disconnect()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
