#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    records

    Author:   David Leclerc

    Version:  0.1

    Date:     25.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a collection of records produced by the Medtronic MiniMed
              pumps and stored within their history pages.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import logger
import errors
import reporter



# Define instances
Logger = logger.Logger("Pump/records.py")



class Record(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record's bytes
        self.bytes = None

        # Initialize vectors for record times and values
        self.t = []
        self.values = []

        # Compute size of record
        self.size = self.sizes["Head"] + self.sizes["Date"] + self.sizes["Body"]

        # Link with pump
        self.pump = pump



    def find(self, pages):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize index
        i = 0

        # Search pages for specified record
        while i < len(pages):

            # Try and find record
            try:

                # Define new possible record
                self.bytes = pages[i:i + self.size]

                # Test criteria
                if self.criteria(self.bytes):

                    # Disassemble record
                    self.parse()

                    # Decode record
                    self.decode()

                    # Remove record from history pages
                    del pages[i:i + self.size]

                # No match
                else:
                    raise errors.BadPumpRecord

            # If not matching, move to next one
            except:

                # Increment index
                i += 1

        # Verify necessity of storing
        if self.t:

            # Print records that were found
            self.show()

            # Store records
            self.store()

        # Return updated pages (without found records)
        return pages



    def parse(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Extract every part of record using a running variable
        x = 0

        # Extract head
        self.head = self.bytes[x:self.sizes["Head"]]

        # Update running variable
        x += self.sizes["Head"]

        # Extract date
        self.date = self.bytes[x:x + self.sizes["Date"]]

        # Update running variable
        x += self.sizes["Date"]

        # Extract body
        self.body = self.bytes[x:x + self.sizes["Body"]]



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current time
        now = datetime.datetime.now()

        # Decode time
        t = lib.decodeTime(self.date)

        # Build datetime object
        t = datetime.datetime(*t)

        # Record cannot be in the future
        if t > now:

            # Error
            raise ValueError("Record cannot be in the future!")

        # Record cannot be more than a year in the past
        elif (now - t).days >= 365:

            # Error
            raise ValueError("Record and current year cannot be a year (or " +
                             "more) apart!")

        # Store time
        self.t.append(t)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Count number of entries found
        n = len(self.t) or len(self.values)

        # Get name of record
        record = self.__class__.__name__

        # Info
        Logger.info("Found " + str(n) + " '" + record + "':")

        # Inject None for missing record times and/or values
        for i in range(n):

            # Get current time
            try:

                # Store it
                t = self.t[i]

            except:

                # Store it
                t = None

            # Get current value
            try:

                # Store it
                value = self.values[i]

            except:

                # Store it
                value = None

            # Print current record
            Logger.info(str(value) + " (" + lib.formatTime(t) + ")")



class SuspendRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report type
        self.reportType = reporter.TreatmentsReport

        # Define record characteristics
        self.code = 30
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 0}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize rest of record
        super(SuspendRecord, self).__init__(pump)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode record time
        super(SuspendRecord, self).decode()
        
        # Store suspend value
        self.values.append(0)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding suspend time to: " + repr(self.reportType))

        # Add entries
        reporter.addDatedEntries(self.reportType, ["Suspend/Resume"],
            dict(zip(self.t, self.values)))



class ResumeRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report type
        self.reportType = reporter.TreatmentsReport

        # Define record characteristics
        self.code = 31
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 0}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize rest of record
        super(ResumeRecord, self).__init__(pump)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode record time
        super(ResumeRecord, self).decode()
        
        # Store suspend value
        self.values.append(1)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding resume time to: " + repr(self.reportType))

        # Add entries
        reporter.addDatedEntries(self.reportType, ["Suspend/Resume"],
            dict(zip(self.t, self.values)))



class TBRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define report type
        self.reportType = reporter.TreatmentsReport

        # Define record characteristics
        self.code = 51
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 8}

        # Define theoretical min/max in bytes
        minTB = {"U/h": 0 / pump.basal.stroke, "%": 0}
        maxTB = {"U/h": 35 / pump.basal.stroke, "%": 200}
        minDuration = 0
        maxDuration = 24 * 60 / pump.basal.time

        # Define record's criteria
        self.criteria = (lambda x: x[0] == self.code and
                                  (minTB["U/h"] <= x[1] <= maxTB["U/h"] and
                                   0 <= x[7] < 8 or
                                   minTB["%"] <= x[1] <= maxTB["%"] and
                                   x[7] == 8) and
                                   minDuration <= x[9] <= maxDuration)

        # Initialize rest of record
        super(TBRecord, self).__init__(pump)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode record time
        super(TBRecord, self).decode()

        # Decode TB rate and units
        if self.body[0] >= 0 and self.body[0] < 8:

            # Decode rate
            rate = round((lib.unpack([self.head[1], self.body[0]], "<") *
                          self.pump.basal.stroke), 2)

            # Decode units
            units = "U/h"

        elif self.body[0] == 8:

            # Decode rate
            rate = self.head[1]

            # Decode units
            units = "%"

        # Decode TB duration
        duration = self.body[2] * self.pump.basal.time

        # Build TB vector
        TB = [rate, units, duration]
        
        # Store TB
        self.values.append(TB)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding TBs to: " + repr(self.reportType))

        # Add entries
        reporter.addDatedEntries(self.reportType, ["Temporary Basals"],
            dict(zip(self.t, self.values)))



class BolusRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Bolus record's time corresponds to beginning of delivery!
              Last byte in criteria corresponds to duration of bolus in
              30m blocks (max 8h)?
        """

        # Define report type
        self.reportType = reporter.TreatmentsReport

        # Define record characteristics
        self.code = 1
        self.sizes = {"Head": 4,
                      "Date": 5,
                      "Body": 0}

        # Define theoretical max bolus in bytes
        maxBolus = 25 / pump.bolus.stroke

        # Define record's criteria
        self.criteria = (lambda x: x[0] == self.code and
                                   0 <= x[1] <= maxBolus and
                                   0 <= x[2] <= maxBolus and
                                   x[1] >= x[2] and
                                   x[3] == 0)

        # Initialize rest of record
        super(BolusRecord, self).__init__(pump)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Head: [code, planned, given, duration]
        Body: []
        Date: [...]
        """

        # Decode record time
        super(BolusRecord, self).decode()

        # Decode bolus
        bolus = round(self.head[2] * self.pump.bolus.stroke, 1)
        
        # Store bolus
        self.values.append(bolus)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding boluses to: " + repr(self.reportType))

        # Add entries
        reporter.addDatedEntries(self.reportType, ["Boluses"],
            dict(zip(self.t, self.values)))



class CarbsRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: - Boluses and carbs input seem to be stored exactly at sime time
                in pump.
              - No need to run readBGU and readCU functions, since units are
                encoded in message bytes!
              - No idea how to decode large ISF in mg/dL... information seems to
                be stored in 4th body byte, but no other byte enables
                differenciation between < and >= 256 ? This is not critical,
                since those ISF only represent the ones the BolusWizard used in
                its calculations. The ISF profiles can be read with readISF().

        Warning: - Do not change units for no reason, otherwise treatments will
                   not be read correctly!

        TODOs: - Should we store BGs that were input by the user? Those could
                 correspond to calibration BGs...
        """

        # Define report type
        self.reportType = reporter.TreatmentsReport

        # Define record characteristics
        self.code = 91
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 13}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code

        # Initialize rest of record
        super(CarbsRecord, self).__init__(pump)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TODO: decode rest of record (this is actually a bolus wizard record)
        """

        # Decode record time
        super(CarbsRecord, self).decode()

        # Define an indicator dictionary to decode BG and carb bytes
        # <i>: [<BGU>, <CU>, <larger BG>, <larger C>]
        indicators = {80: ["mg/dL", "g", False, False],
                      82: ["mg/dL", "g", True, False],
                      84: ["mg/dL", "g", False, True],
                      86: ["mg/dL", "g", True, True],
                      96: ["mg/dL", "exchange", False, False],
                      98: ["mg/dL", "exchange", True, False],
                      144: ["mmol/L", "g", False, False],
                      145: ["mmol/L", "g", True, False],
                      148: ["mmol/L", "g", False, True],
                      149: ["mmol/L", "g", True, True],
                      160: ["mmol/L", "exchange", False, False],
                      161: ["mmol/L", "exchange", True, False]}

        # Decode units and sizes of BG and carb entries using 2nd
        # body byte as indicator linked with the previously
        # defined dictionary
        [BGU, CU, largerBG, largerC] = indicators[self.body[1]]

        # Define rounding multiplicator
        # BGs
        # mmol/L
        if BGU == "mmol/L":
            mBGU = 1.0

        # mg/dL
        elif BGU == "mg/dL":
            mBGU = 0

        # Carbs
        # exchange
        if CU == "exchange":
            mCU = 1.0

        # g
        elif CU == "g":
            mCU = 0

        # Define number of bytes to add for larger BGs and Cs
        # Larger BG
        if largerBG:
            
            # Extra number of bytes depends on BG units
            if BGU == "mmol/L":
                mBG = 256

            elif BGU == "mg/dL":
                mBG = 512

        # Smaller BG
        else:
            mBG = 0

        # Larger carbs
        if largerC:
            mC = 256

        # Smaller carbs
        else:
            mC = 0

        # Decode record
        C = (self.body[0] + mC) / 10 ** mCU

        # Store carbs
        self.values.append([C, CU])



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding carbs to: " + repr(self.reportType))

        # Add entries
        reporter.addDatedEntries(self.reportType, ["Carbs"],
            dict(zip(self.t, self.values)))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()