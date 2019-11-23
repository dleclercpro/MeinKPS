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
import fmt
import logger
import crc
import cgm



# Define instances
Logger = logger.Logger("CGM.records")



# Constants
BG_VALUE_MASK = 1023
BG_NOISE_MASK = 112
BG_TREND_MASK = 15



class Record(object):

    # Record size
    size = 0



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record vectors
        self.bytes = bytes
        self.systemTime = None
        self.displayTime = None
        self.values = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        raise NotImplementedError("No string representation for record.")



    def verifyCRC(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Compute and check CRC value of last record.
        """

        # Decode and compute CRCs
        expectedCRC = lib.unpack(self.bytes[-2:], "<")
        computedCRC = crc.compute(self.bytes[:-2])

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad record CRC. Expected: " + str(expectedCRC) +
                ". Computed: " + str(computedCRC) + ".")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's time-related bytes.

            [0-3] SYSTEM TIME
            [4-7] DISPLAY TIME
            [...]
        """

        # Decode system time
        self.systemTime = (cgm.EPOCH_TIME + datetime.timedelta(seconds =
            lib.unpack(self.bytes[0:4], "<")))

        # Decode display time
        self.displayTime = (cgm.EPOCH_TIME + datetime.timedelta(seconds =
            lib.unpack(self.bytes[4:8], "<")))



class BGRecord(Record):

    # Record size
    size = 25

    # Trend values
    trends = [None, "↑↑", "↑", "↗", "→", "↘", "↓", "↓↓", " ", "OutOfRange"]

    # Special BG values
    special = {0: None,
               1: "SensorInactive",
               2: "MinimalDeviation",
               3: "NoAntenna",
               5: "SensorNotCalibrated",
               6: "DeviationCount",
               9: "AbsoluteDeviation",
               10: "PowerDeviation",
               12: "BadRF"}



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(BGRecord, self).__init__(bytes)

        # BG record properties
        self.value = None
        self.trend = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        
        value = self.value

        if type(value) is float:
            value = fmt.BG(value)
            
        return ("BG: " + str(value) + " " + str(self.trend) + " (" +
            lib.formatTime(self.displayTime) + ")")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3]:   SYSTEM TIME
            [4-7]:   DISPLAY TIME
            [8-9]:   BG
            [10-13]: MEASUREMENT TIME (?)
            [14-18]: ???
            [19]:    TREND
            [20-22]: ???
            [23-24]: CRC
        """

        # Initialize decoding
        super(BGRecord, self).decode()

        # Decode BG value
        self.value = lib.unpack(self.bytes[8:10], "<") & BG_VALUE_MASK

        # Decode trend
        self.trend = self.trends[self.bytes[19] & BG_TREND_MASK] # G6
        #self.trend = self.trends[self.bytes[10] & BG_TREND_MASK] # G4

        # Normal values
        if self.value not in self.special:

            # Convert BG units by default from mg/dL to mmol/L
            self.value = round(self.value / 18.0, 1)

        # Special values
        else:

            # Decode special BG
            self.value = self.special[self.value]



class SensorRecord(Record):

    # Record size
    size = 25 # G6
    #size = 15 # G4

    # Sensor statuses
    statuses = [None,
                "Stopped",
                "Expired",
                "ResidualDeviation",
                "CountsDeviation",
                "SecondSession",
                "OffTimeLoss",
                "Started",
                "BadTransmitter",
                "ManufacturingMode",
                "Unknown1",
                "Unknown2",
                "Unknown3",
                "Unknown4",
                "Unknown5",
                "Unknown6",
                "Unknown7",
                "Expired", # ?
                "Unknown9",
                "Unknown10",
                "SensorIDEntered" # ?
                ]



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(SensorRecord, self).__init__(bytes)

        # Sensor record properties
        self.status = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return ("Sensor status: " + str(self.status) + " (" +
            lib.formatTime(self.displayTime) + ")")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3]:   SYSTEM TIME
            [4-7]:   DISPLAY TIME
            [8-11]:  INSERTION TIME
            [12]:    STATUS
            [13-22]: ???
            [23-24]: CRC
        """

        # Initialize decoding
        super(SensorRecord, self).decode()

        # Decode sensor status
        self.status = self.statuses[self.bytes[12]]



class CalibrationRecord(Record):

    # Record size
    size = 21 # G6
    #size = 16 # G4



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(CalibrationRecord, self).__init__(bytes)

        # Calibration record properties
        self.enteredTime = None
        self.value = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return ("BG calibration value: " + str(self.value) + " mmol/L (" +
            lib.formatTime(self.enteredTime) + ")")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3]:   SYSTEM TIME
            [4-7]:   DISPLAY TIME
            [8:9]:   CALIBRATION BG VALUE
            [10]:    ???
            [11-14]: ENTERED TIME
            [15-18]: ???
            [19-20]: CRC
        """

        # Initialize decoding
        super(CalibrationRecord, self).decode()

        # Entered time
        self.enteredTime = (cgm.EPOCH_TIME + datetime.timedelta(seconds =
            lib.unpack(self.bytes[11:15], "<")))

        # Decode BG
        self.value = round(lib.unpack(self.bytes[8:10], "<") / 18.0, 1)



class EventRecord(Record):

    # Record size
    size = 20

    # Event types
    types = [None, "Carbs", "Insulin", "Health", "Exercise"]

    # Event sub-types
    subTypes = {"Insulin": [None, "Fast-Acting", "Long-Acting"],
                "Exercise": [None, "Light", "Medium", "Heavy"],
                "Health": [None, "Illness", "Stress", "Feel High", "Feel Low",
                                 "Cycle", "Alcohol"]}



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(EventRecord, self).__init__(bytes)

        # Event record properties
        self.enteredTime = None
        self.type = None
        self.subType = None
        self.value = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return ("Event: " + str(self.type) + ", " + str(self.subType) + ": " +
            str(self.value) + " (" + lib.formatTime(self.enteredTime) + ")")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3]:   SYSTEM TIME
            [4-7]:   DISPLAY TIME
            [8]:     EVENT TYPE
            [9]:     EVENT SUB-TYPE
            [10-13]: ENTERED TIME
            [14-17]: VALUE
            [18-19]: CRC
        """

        # Initialize decoding
        super(EventRecord, self).decode()

        # Entered time
        self.enteredTime = (cgm.EPOCH_TIME + datetime.timedelta(seconds =
            lib.unpack(self.bytes[10:14], "<")))

        # Decode event type
        self.type = self.types[self.bytes[8]]

        # Decode event sub-type
        # No sub-type
        if self.bytes[9] == 0:
            self.subType = None
            
        # Otherwise
        else:
            self.subType = self.subTypes[self.type][self.bytes[9]]

        # No value entered for health events
        if self.type == "Health":
            self.value = None
        
        # Otherwise
        else:
            self.value = lib.unpack(self.bytes[14:18], "<")

            # Insulin needs post-treatment
            if self.type == "Insulin":
                self.value /= 100.0



class ReceiverRecord(Record):

    # Record size
    size = 20



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3]:   SYSTEM TIME
            [4-7]:   DISPLAY TIME
            [8-17]:  ???
            [18-19]: CRC
        """

        # Initialize decoding
        super(ReceiverRecord, self).decode()



class SettingsRecord(Record):

    # Record size
    size = 60



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-57]:  ???
            [58-59]: CRC
        """

        # Initialize decoding
        super(SettingsRecord, self).decode()



class XMLRecord(Record):

    # Record size
    size = 500



    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(XMLRecord, self).__init__(bytes)

        # XML parameters
        self.value = None



    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return "XML record: " + str(self.value)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.
            
            [0-3]:     SYSTEM TIME
            [4-7]:     DISPLAY TIME
            [8-497]:   CONTENT (XML)
            [498-499]: CRC
        """

        # Initialize decoding
        super(XMLRecord, self).decode()

        # XML value
        self.value = lib.translate(self.bytes[8:-2])



class ManufactureRecord(XMLRecord):

    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return "Manufacture record: " + str(self.value)



class FirmwareRecord(XMLRecord):

    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return "Firmware record: " + str(self.value)



class PCRecord(XMLRecord):

    def __str__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STR
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        return "PC record: " + str(self.value)