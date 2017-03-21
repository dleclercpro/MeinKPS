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
codes = {"ReadFirmwareHeader": 11,
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

batteryStates = {1: "Charging",
                 2: "NotCharging",
                 3: "NTCFault",
                 4: "BadBattery"}

trendArrows = {1: "↑↑",
               2: "↑",
               3: "↗",
               4: "→",
               5: "↘",
               6: "↓",
               7: "↓↓",
               8: "NotComputable",
               9: "OutOfRange"}

specialBG = {0: None,
             1: "SensorNotActive",
             2: "MinimalDeviation",
             3: "NoAntenna",
             5: "SensorNotCalibrated",
             6: "CountsDeviation",
             9: "AbsoluteDeviation",
            10: "PowerDeviation",
            12: "BadRF"}

languages = {1029: "Czech",
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

databases = {"ManufacturingParameters": 0,
             "FirmwareSettings": 1,
             "PCParameterRecord": 2,
             "SensorData": 3,
             "GlucoseData": 4,
             "CalibrationSet": 5,
             "InsertionTime": 7,
             "ReceiverLogData": 8,
             "MeterData": 10,
             "UserSettingsData": 12}

BGU = {1: "mg/dL",
       2: "mmol/L"}

clockModes = {0: "24h",
              1: "AM/PM"}

epochTime = datetime.datetime(2009, 1, 1)



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

        # Give CGM a packet instance
        self.packet = Packet()

        # Give CGM an database instance
        self.database = Database(self)

        # Initialize handle
        self.handle = serial.Serial()

        # Initialize CGM response
        self.response = None

        # Initialize records
        self.records = {"BG": BGRecord(),
                        "Sensor": SensorRecord(),
                        "Insertion": InsertionRecord()}



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
        self.handle.write(bytearray(self.packet.value))

        # Give user info
        print "Sent packet: " + str(self.packet.value)



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

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.value = None

        # Initialize packet characteristics
        self.size = None
        self.code = None
        self.database = None
        self.page = None
        self.CRC = None



    def build(self, code, database = None, page = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet
        self.value = [1, 0, 0]

        # Build code byte
        code = codes[code]

        # Build database byte
        if database is not None:
            database = [databases[database]]

        else:
            database = []

        # Build page bytes
        if page is not None:
            page = unpack(page, 4)
            page.append(1)

        else:
            page = []

        # Build packet
        self.value.append(code)
        self.value.extend(database)
        self.value.extend(page)

        # Build size byte
        size = len(self.value) + 2

        # Update packet
        self.value[1] = size

        # Build CRC bytes
        CRC = lib.computeCRC16(self.value)
        CRC = unpack(CRC, 2)

        # Finish packet
        self.value.extend(CRC)

        # Store packet characteristics
        self.size = size
        self.code = code
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
        return self.value



class Database(object):

    # DATABASE CHARACTERISTICS
    headerSize = 28



    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize database vector
        self.value = []

        # Initialize database range
        self.range = None

        # Link with CGM
        self.cgm = cgm



    def measure(self, database):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MEASURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset database range
        self.range = []

        # Prepare command packet
        self.cgm.packet.build("ReadDatabaseRange", database)

        # Read database range
        self.cgm.ask()

        # Decode database range
        self.range.append(pack(self.cgm.response["Body"][0:4]))
        self.range.append(pack(self.cgm.response["Body"][4:8]))

        # Give user info
        print "Database range: " + str(self.range)



    def read(self, database, record = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get database range for selected database
        self.measure(database)

        # Get ends of database range
        start = self.range[0]
        end = self.range[1]

        # Read database
        for i in range(start, end + 1):

            # Give user info
            print "Reading database page " + str(i) + "/" + str(end) + "..."

            # Build packet to read page i
            self.cgm.packet.build("ReadDatabase", database, i)

            # Read page i
            self.cgm.ask()

            # Get page i
            data = self.cgm.response["Body"]

            # Extract page header
            header = data[:self.headerSize]

            # Get number of records in page
            n = header[4]

            # Get CRC
            CRC = header[-2:]

            # Give user info
            print "Number of records in page: " + str(n)
            print "Header CRC: " + str(CRC)

            # Get actual page of data
            page = data[self.headerSize:]
            
            # Extend database
            self.value.extend(page)

            # Extract records from page if corresponding size given
            if record is not None:
                self.cgm.records[record].find(page, n)



class Record(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record values
        self.values = []



    def find(self, page, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Extract records from page
        for i in range(n):

            # Extract ith record
            record = page[i * self.size: (i + 1) * self.size]

            # Store it
            self.values.append(record)

            # Decode it
            self.decode(record)



    def decode(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Extract system time
        systemTime = datetime.timedelta(seconds = pack(bytes[0:4]))
        systemTime += epochTime

        # Extract local time
        localTime = datetime.timedelta(seconds = pack(bytes[4:8]))
        localTime += epochTime

        # Give user info
        print "Record: " + str(bytes)
        print "System time: " + str(systemTime)
        print "Local time: " + str(localTime)



class BGRecord(Record):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__()

        # Initialize value
        self.value = None

        # Define record size
        self.size = 13



    def decode(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode(bytes)

        # Extract BG
        if bytes[8] != 5:
            self.value = round(bytes[8] / 18.0, 1)

        else:
            self.value = None

        # Extract trend arrow
        trendArrow = trendArrows[bytes[10] & 15]

        # Give user info
        print "BG: " + str(self.value)
        print "Trend arrow: " + str(trendArrow)



class SensorRecord(Record):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__()

        # Define record size
        self.size = 20



class InsertionRecord(Record):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(self.__class__, self).__init__()

        # Initialize type
        self.type = None

        # Define record size
        self.size = 15



    def decode(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(self.__class__, self).decode(bytes)

        # Decode insertion type
        if bytes[12] == 7:
            self.type = "Start"

        elif bytes[12] == 1:
            self.type = "Stop"

        # Give user info
        print "Sensor: " + str(self.type)



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

    # Read XML
    #cgm.packet.build("ReadFirmwareHeader")
    #cgm.ask(True)
    #cgm.packet.build("ReadTransmitterID")
    #cgm.ask()
    #print translate(cgm.response["Body"])
    #cgm.packet.build("ReadLanguage")
    #cgm.ask()
    #print languages[pack(cgm.response["Body"])]
    #cgm.packet.build("ReadBatteryLevel")
    #cgm.ask()
    #print str(pack(cgm.response["Body"])) + "%"
    #cgm.packet.build("ReadSystemTime")
    #cgm.ask()
    #print (epochTime + datetime.timedelta(seconds = pack(cgm.response["Body"])))
    #cgm.packet.build("ReadBGU")
    #cgm.ask()
    #print BGU[pack(cgm.response["Body"])]
    #cgm.packet.build("ReadFirmwareSettings")
    #cgm.ask(True)
    #cgm.packet.build("ReadBatteryState")
    #cgm.ask()
    #print batteryStates[pack(cgm.response["Body"])]
    #cgm.packet.build("ReadClockMode")
    #cgm.ask()
    #print clockModes[pack(cgm.response["Body"])]


    # Read database
    #cgm.database.read("ManufacturingParameters")
    #cgm.database.read("FirmwareSettings")
    #cgm.database.read("PCParameterRecord")

    #cgm.database.read("SensorData", "Sensor")
    #cgm.database.read("GlucoseData", "BG")
    #cgm.database.read("InsertionTime", "Insertion")
    #cgm.database.read("CalibrationSet")
    #cgm.database.read("ReceiverLogData")
    #cgm.database.read("MeterData")
    #cgm.database.read("UserSettingsData")

    # End connection with CGM
    cgm.disconnect()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
