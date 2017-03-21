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
codes = {"ReadFirmwareHeader": 11, #
         "ReadDatabaseRange": 16, #
         "ReadDatabase": 17, #
         "ReadTransmitterID": 25,
         "ReadLanguage": 27,
         "ReadRTC": 31,
         "ReadBatteryLevel": 33,
         "ReadSystemTime": 34,
         "ReadBGU": 37,
         "ReadBlindedMode": 39,
         "ReadClockMode": 41,
         "ReadBatteryState": 48,
         "ReadFirmwareSettings": 54}

epochTime = datetime.datetime(2009, 1, 1)

batteryStates = [None,
                 "Charging",
                 "NotCharging",
                 "NTCFault",
                 "BadBattery"]

trendArrows = [None,
               "↑↑",
               "↑",
               "↗",
               "→",
               "↘",
               "↓",
               "↓↓",
               "NotComputable",
               "OutOfRange"]

specialBG = {0: None,
             1: "SensorNotActive",
             2: "MinimalDeviation",
             3: "NoAntenna",
             5: "SensorNotCalibrated",
             6: "CountsDeviation",
             9: "AbsoluteDeviation",
            10: "PowerDeviation",
            12: "BadRF"}

languages = {0: None, 1033: "English"}

databases = ["ManufacturingParameters", #
             "FirmwareSettings", #
             "PCParameterRecord", #
             "SensorData", #
             "GlucoseData",
             "CalibrationSet",
             "Deviation",
             "InsertionTime",
             "ReceiverLogData",
             "ReceiverErrorData",
             "MeterData",
             "UserEventsData",
             "UserSettingsData",
             "MaxValues"]



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
        self.responses = None

        # Initialize records
        self.records = {"BG": Record(13),
                        "Sensor": Record(20)}



    def connect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Add serial port
        #os.system("modprobe --quiet --first-time usbserial"
        #    + " vendor=" + str(self.vendor)
        #    + " product=" + str(self.product))

        # Define handle
        try:
            #self.handle.port = "/dev/ttyACM0"
            self.handle.port = "COM7"
            self.handle.baudrate = 115200

        except:
            sys.exit("Can't connect to port. Is CGM plugged in? Exiting...")

        # Open handle
        try:
            self.handle.open()

        except:
            print "Port already open? Continuing..."



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
        self.rawResponse = self.handle.read(n)

        # Convert raw bytes
        self.response = [ord(x) for x in self.rawResponse]

        # Give user info
        print "Received bytes: " + str(self.response)



    def ask(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ASK
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset responses
        self.responses = {"Head": None,
                          "Body": None,
                          "CRC": None}

        # Send command packet
        self.write()

        # First read
        self.read(4)

        # Store response part
        self.responses["Head"] = self.response

        # Compute number of bytes received
        nBytesReceived = pack(self.responses["Head"][1:3])

        # Minimum number of bytes received: 6
        if nBytesReceived > 6:
            nBytesReceived -= 6

        # Second read
        self.read(nBytesReceived)

        # Store response part
        self.responses["Body"] = self.response

        # Third read
        self.read(2)

        # Store response part
        self.responses["CRC"] = self.response

        # CRC computation and verification
        expectedCRC = pack(self.responses["CRC"])
        computedCRC = lib.computeCRC16(self.responses["Head"] +
                                       self.responses["Body"])

        # Give user info
        print "Expected CRC: " + str(expectedCRC)
        print "Computed CRC: " + str(computedCRC)



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
            database = [databases.index(database)]

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
        self.range.append(pack(self.cgm.responses["Body"][0:4]))
        self.range.append(pack(self.cgm.responses["Body"][4:8]))

        # Give user info
        print "Database range: " + str(self.range)



    def read(self, database, record = None, XML = False):

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
            time.sleep(0.1)

            # Build packet to read page i
            self.cgm.packet.build("ReadDatabase", database, i)

            # Read page i
            self.cgm.ask()

            # Get page i
            data = self.cgm.responses["Body"]

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
                record.find(page, n)

        # "Clean" database if desired
        if XML:
            print XMLify(self.value)



class Record(object):

    def __init__(self, size):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store record size
        self.size = size

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



    def decode(self, record):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # FIXME: Move somewhere else?

        # Extract system time
        systemTime = datetime.timedelta(seconds = pack(record[0:4]))
        systemTime += epochTime

        # Extract display time
        displayTime = datetime.timedelta(seconds = pack(record[4:8]))
        displayTime += epochTime

        # Extract BG
        BG = record[8]

        if BG == 5:
            BG = None

        else:
            BG = round(BG / 18.0, 1)

        # Extract trend arrow
        trendArrow = trendArrows[record[10] & 15]

        # Give user info
        print "Record: " + str(record)
        print "System time: " + str(systemTime)
        print "Display time: " + str(displayTime)
        print "BG: " + str(BG)
        print "Trend arrow: " + str(trendArrow)



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

    # Read database
    #cgm.database.read("ManufacturingParameters", None, True)
    #cgm.database.read("FirmwareSettings", None, True)
    #cgm.database.read("PCParameterRecord", None, True)
    #cgm.database.read("SensorData", cgm.records["Sensor"])
    cgm.database.read("GlucoseData", cgm.records["BG"])

    # End connection with CGM
    cgm.disconnect()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
