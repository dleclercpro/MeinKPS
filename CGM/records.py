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
import errors
import reporter



# Define instances
Logger = logger.Logger("CGM.records")



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
            Find records in a database page.
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
            Compute and check CRC value of last record.
        """

        # Decode and compute CRCs
        expectedCRC = lib.unpack(self.bytes[-1][-2:], "<")
        computedCRC = crc.compute(self.bytes[-1][:-2])

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad record CRC. Expected: " + str(expectedCRC) +
                ". Computed: " + str(computedCRC) + ".")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-3] SYSTEM TIME
            [4-7] DISPLAY TIME
            [...]
        """

        # Decode system time
        #systemTime = (self.cgm.clock.epoch + datetime.timedelta(seconds =
        #    lib.unpack(self.bytes[-1][0:4], "<")))

        # Decode display time
        displayTime = (self.cgm.clock.epoch + datetime.timedelta(seconds =
            lib.unpack(self.bytes[-1][4:8], "<")))

        # Store it
        self.t.append(displayTime)



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
        super(BGRecord, self).__init__(cgm)

        # Define record size
        self.size = 25

        # Define dictionary for trends
        self.trends = {0: None,
                       1: "↑↑",
                       2: "↑", 
                       3: "↗", 
                       4: "→", 
                       5: "↘", 
                       6: "↓",
                       7: "↓↓",
                       8: " ",
                       9: "OutOfRange"}

        # Define dictionary for special values
        self.special = {0:  None,
                        1:  "SensorInactive",
                        2:  "MinimalDeviation",
                        3:  "NoAntenna",
                        5:  "SensorNotCalibrated",
                        6:  "DeviationCount",
                        9:  "AbsoluteDeviation",
                        10: "PowerDeviation",
                        12: "BadRF"}

        # Define if conversion from mg/dL to mmol/L is needed
        self.convert = True

        # Define report type
        self.reportType = reporter.BGReport



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

        # Decode BG
        BG = lib.unpack(self.bytes[-1][8:10], "<") & 1023

        # Decode trend
        trend = self.trends[self.bytes[-1][19] & 15] # G6
        #trend = self.trends[self.bytes[-1][10] & 15] # G4

        # Deal with special values
        if BG in self.special:

            # Decode special BG
            BG = self.special[BG]

            # Info
            Logger.debug(BG + " (" + lib.formatTime(self.t[-1]) + ")")

        # Deal with normal values
        else:

            # Convert BG units if desired
            if self.convert:

                # Convert them
                BG = round(BG / 18.0, 1)

            # Info
            Logger.info("BG: " + fmt.BG(BG) + " " + str(trend) + " " +
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
        self.size = 25 # G6
        #self.size = 15 # G4

        # Define possible sensor status
        self.statuses = [None,
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
                         "Unknown8",
                         "Unknown9",
                         "Unknown10",
                         "Unknown11" # Sensor ID input?
                         ]

        # Define report type
        self.reportType = reporter.HistoryReport



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
        self.size = 21 # G6
        #self.size = 16 # G4

        # Define report type
        self.reportType = reporter.HistoryReport



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

        # Time entered
        t = (self.cgm.clock.epoch + datetime.timedelta(seconds =
            lib.unpack(self.bytes[-1][11:15], "<")))

        # Decode BG
        BG = round(lib.unpack(self.bytes[-1][8:10], "<") / 18.0, 1)

        # Store it
        self.values.append(BG)

        # Info
        Logger.info("BG calibration: " + str(BG) + " " + self.cgm.units.value +
                    " (" + lib.formatTime(t) + ")")



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

        # Define possible event types
        self.types = [None,
                      "Carbs",
                      "Insulin",
                      "Health",
                      "Exercise"]

        # Define possible event sub-types
        self.subTypes = {"Insulin": [None, "Fast-Acting", "Long-Acting"],
                         "Exercise": [None, "Light", "Medium", "Heavy"],
                         "Health": [None,
                                    "Illness",
                                    "Stress",
                                    "Feel High",
                                    "Feel Low",
                                    "Cycle",
                                    "Alcohol"]}



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

        # Time entered
        t = (self.cgm.clock.epoch + datetime.timedelta(seconds =
            lib.unpack(self.bytes[-1][10:14], "<")))

        # Decode event type
        eventType = self.types[self.bytes[-1][8]]

        # Decode event sub-type
        # No sub-type
        if self.bytes[-1][9] == 0:
            eventSubType = None
            
        # Otherwise
        else:
            eventSubType = self.subTypes[eventType][self.bytes[-1][9]]

        # No value entered for health events
        if eventType == "Health":
            value = None
        
        # Otherwise
        else:
            value = lib.unpack(self.bytes[-1][14:18], "<")

            # Insulin needs post-treatment
            if eventType == "Insulin":
                value /= 100.0

        # Info
        Logger.info("Event: " + str(eventType) + ", " + str(eventSubType) +
                    ": " + str(value) + " (" + lib.formatTime(t) + ")")



class ReceiverRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(ReceiverRecord, self).__init__(cgm)

        # Define record size
        self.size = 20



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

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(SettingsRecord, self).__init__(cgm)

        # Define record size
        self.size = 60



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Decode the record's bytes.

            [0-57]:  ???
            [58-59]: CRC
        """

        pass



class ManufactureRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(ManufactureRecord, self).__init__(cgm)

        # Define record size
        self.size = 500



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
        super(ManufactureRecord, self).decode()

        # Info
        Logger.info("Manufacture record: " + lib.translate(self.bytes[-1][8:-2]))



class FirmwareRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(FirmwareRecord, self).__init__(cgm)

        # Define record size
        self.size = 500



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
        super(FirmwareRecord, self).decode()

        # Info
        Logger.info("Firmware record: " + lib.translate(self.bytes[-1][8:-2]))



class PCRecord(Record):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record
        super(PCRecord, self).__init__(cgm)

        # Define record size
        self.size = 500



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
        super(PCRecord, self).decode()

        # Info
        Logger.info("PC record: " + lib.translate(self.bytes[-1][8:-2]))