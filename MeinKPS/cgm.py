#! /usr/bin/python

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
import datetime
import serial



# USER LIBRARIES
import lib



# CONSTANTS
codes = {"ReadFirmwareHeader": 11, #
         "ReadHistoryRange": 16, #
         "ReadHistory": 17, #
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

batteryStates = [None, "Charging", "NotCharging", "NTCFault", "BadBattery"]

trendArrows = [None, "DoubleUp", "SingleUp", "45Up", "Flat", "45Down",
                     "SingleDown", "DoubleDown", "NotComputable", "OutOfRange"]

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

recordTypes = ["ManufacturingParameters", #
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



class Packet(object):

    # PACKET CHARACTERISTICS

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.head = [1, None, 0]
        self.body = []
        self.size = None
        self.code = None
        self.payload = None
        self.CRC = None



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            [1, SIZE, 0, CODE, ..., PARAMETERS, CRC]

        """

        firstRead = [0, 0, 0, 0]
        state = firstRead[0]
        nBytesReceived = firstRead[1] + 256 * firstRead[2] - 6
        command[3] = firstRead[3]
        secondRead = []
        thirdRead = [0, 0]
        expectedCRC = thirdRead[0] + 256 * thirdRead[1]
        parameters = []
        self.CRC = [CRC % 256, CRC / 256]



class CGM(object):

    # CGM CHARACTERISTICS
    vendor  = 0x22a3
    product = 0x0047



def read(code, handle, recordType = None, page = None):

    if recordType is not None:
        recordType = [recordTypes.index(recordType)]
    else:
        recordType = []

    if page is not None:
        page = unpack(page)

        page.append(1)
    else:
        page = []

    # Define packet
    packet = []
    head = [1, None, 0]
    packet.extend(head)
    packet.append(code)
    packet.extend(recordType)
    packet.extend(page)
    size = len(packet) + 2
    packet[1] = size
    CRC = lib.computeCRC16(packet)
    CRC = [CRC % 256, CRC / 256]
    packet.extend(CRC)

    # Send command
    print "W: " + str(packet)
    handle.write(bytearray(packet))

    # Read first response
    print "R: " + str(4)
    responseHead = [ord(x) for x in handle.read(4)]
    print "A: " + str(responseHead)
    nBytesReceived = responseHead[1] + 256 * responseHead[2]

    if nBytesReceived > 6:
        nBytesReceived -= 6

    # Read second response
    print "R: " + str(nBytesReceived)
    responseBody = [ord(x) for x in handle.read(nBytesReceived)]
    print "A: " + str(responseBody)
    #translation = translate(responseBody)
    #print "TA: " + translation

    # Read third response
    print "R: " + str(2)
    expectedCRC = [ord(x) for x in handle.read(2)]
    print "A: " + str(expectedCRC)

    # CRC computation and verification
    expectedCRC = expectedCRC[0] + expectedCRC[1] * 256
    computedCRC = lib.computeCRC16(responseHead + responseBody)
    print "Expected CRC: " + str(expectedCRC)
    print "Computed CRC: " + str(computedCRC)

    return responseBody



def translate(bytes):

    return "".join([chr(x) for x in bytes])



def readHistoryRange(handle, recordType):

    rawHistoryRange = read(codes["ReadHistoryRange"], handle, recordType)

    historyRange = [pack(rawHistoryRange[0:4]),
                    pack(rawHistoryRange[4:8])]

    print "History range: " + str(historyRange)

    return historyRange


def readHistory(handle, code, recordType, recordSize = None):

    history = []

    historyRange = readHistoryRange(handle, recordType)

    start = historyRange[0]
    end = historyRange[1] + 1

    for i in range(start, end):

        data = read(codes[code], handle, recordType, i)
        headerSize = 28
        print "Header size: " + str(headerSize)
        header = data[:headerSize]
        nRecords = header[4]
        CRC = header[-2:]
        print "Number of records in page: " + str(nRecords)
        print "Header CRC: " + str(CRC)
        page = data[headerSize:]
        history.extend(page)

        if recordSize is not None:
            findRecords(page, nRecords, recordSize)

    translation = clean(history)

    #print "History: " + str(translation)



def findRecords(page, nRecords, recordSize):

    for i in range(nRecords):

        record = page[i * recordSize: (i + 1) * recordSize]
        systemTime = epochTime + datetime.timedelta(seconds = pack(record[0:4]))
        displayTime = epochTime + datetime.timedelta(seconds = pack(record[4:8]))

        print record
        print "System time: " + str(systemTime)
        print "Display time: " + str(displayTime)
        



def clean(response):

    translation = translate(response)
    size = len(translation)

    started = False

    for i in range(size):

        if translation[i] == "<" and not started :
            start = i
            started = True

        if translation[i] == ">":
            end = i + 1

    return translation[start:end]



def unpack(x):

    return [(x / 256 ** 0) % 256,
            (x / 256 ** 1) % 256,
            (x / 256 ** 2) % 256,
            (x / 256 ** 3) % 256]



def pack(x):

    return (x[0] * 256 ** 0 +
            x[1] * 256 ** 1 +
            x[2] * 256 ** 2 +
            x[3] * 256 ** 3)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Generate serial port handle
    handle = serial.Serial(port = "/dev/ttyACM0", baudrate = 115200)

    # Open handle
    try:
        handle.open()

    except:
        pass

    # Read stuff
    #read(codes["ReadFirmwareHeader"], handle)
    #readHistory(handle, "ReadHistory", "ManufacturingParameters")
    #readHistory(handle, "ReadHistory", "FirmwareSettings")
    #readHistory(handle, "ReadHistory", "PCParameterRecord")
    #readHistory(handle, "ReadHistory", "SensorData", 20)
    readHistory(handle, "ReadHistory", "GlucoseData", 13)

    # Close handle
    handle.close()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
