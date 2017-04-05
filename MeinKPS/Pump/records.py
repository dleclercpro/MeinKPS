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
import reporter



# Define a reporter
Reporter = reporter.Reporter()



class Record(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize record's report
        self.report = None

        # Initialize record's bytes
        self.bytes = None

        # Initialize vectors for record times and values
        self.times = []
        self.values = []

        # Compute size of record
        self.size = self.sizes["Head"] + self.sizes["Date"] + self.sizes["Body"]

        # Link with pump
        self.pump = pump



    def find(self, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Search page for specified record
        for i in range(len(page)):

            # Try and find record
            try:

                # Define new possible record
                self.bytes = page[i:i + self.size]

                # Test criteria
                if self.criteria(self.bytes):

                    # Disassemble record
                    self.parse()

                    # Decode record
                    self.decode()

            # If not matching, move to next one
            except:
                pass

        # Print records that were found
        self.show()

        # Store records
        self.store()



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
        t = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

        # Proof record year
        if abs(t.year - now.year) > 1:

            raise ValueError("Record and current year too far " +
                             "apart!")

        # Format time
        t = lib.formatTime(t)

        # Store time
        self.times.append(t)



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
        n = len(self.times) or len(self.values)

        # Get name of record
        record = self.__class__.__name__

        # Give user info
        print "Found " + str(n) + " '" + record + "':"

        # Inject None for missing record times and/or values
        for i in range(n):

            # Get current time
            try:
                t = self.times[i]

            except:
                t = None

            # Get current value
            try:
                value = self.values[i]

            except:
                value = None

            # Print current record
            print str(value) + " (" + str(t) + ")"



class SuspendRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define record characteristics
        self.code = 30
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 0}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize rest of record
        super(self.__class__, self).__init__(pump)



class ResumeRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define record characteristics
        self.code = 31
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 0}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize rest of record
        super(self.__class__, self).__init__(pump)



class BolusRecord(Record):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: Bolus record's time corresponds to beginning of delivery!

        """

        # Define record characteristics
        self.code = 1
        self.sizes = {"Head": 4,
                      "Date": 5,
                      "Body": 0}

        # Define theoretical max bolus
        maxBolus = 25.0

        # Define record's criteria
        # TODO: do something with incomplete boluses?
        self.criteria = (lambda x: x[0] == self.code and
                                   x[1] <= maxBolus and
                                   x[2] <= maxBolus and
                                   x[1] >= x[2] and
                                   x[3] == 0)

        # Initialize rest of record
        super(self.__class__, self).__init__(pump)

        # Define record's report
        self.report = "treatments.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode record time
        super(self.__class__, self).decode()

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

        # Give user info
        print "Adding boluses to report: '" + self.report + "'..."

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(["Boluses"], self.times, self.values)



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

        # Define record characteristics
        self.code = 91
        self.sizes = {"Head": 2,
                      "Date": 5,
                      "Body": 13}

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code

        # Initialize rest of record
        super(self.__class__, self).__init__(pump)

        # Define record's report
        self.report = "treatments.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode record time
        super(self.__class__, self).decode()

        # Define an indicator dictionary to decode BG and carb bytes
        # <i>: [<BGU>, <CU>, <larger BG>, <larger C>]
        indicators = {80: ["mg/dL", "g", False, False],
                      82: ["mg/dL", "g", True, False],
                      84: ["mg/dL", "g", False, True],
                      86: ["mg/dL", "g", True, True],
                      96: ["mg/dL", "exchanges", False, False],
                      98: ["mg/dL", "exchanges", True, False],
                      144: ["mmol/L", "g", False, False],
                      145: ["mmol/L", "g", True, False],
                      148: ["mmol/L", "g", False, True],
                      149: ["mmol/L", "g", True, True],
                      160: ["mmol/L", "exchanges", False, False],
                      161: ["mmol/L", "exchanges", True, False]}

        # Decode units and sizes of BG and carb entries using 2nd
        # body byte as indicator linked with the previously
        # defined dictionary
        [BGU, CU, largerBG, largerC] = indicators[self.body[1]]

        # Define rounding multiplicator for BGs and Cs
        if BGU == "mmol/L":
            mBGU = 1.0

        elif BGU == "mg/dL":
            mBGU = 0

        if CU == "exchanges":
            mCU = 1.0

        elif CU == "g":
            mCU = 0

        # Define number of bytes to add for larger BGs and Cs
        if largerBG:
            
            # Extra number of bytes depends on BG units
            if BGU == "mmol/L":
                mBG = 256

            elif BGU == "mg/dL":
                mBG = 512

        else:
            mBG = 0

        if largerC:
            mC = 256

        else:
            mC = 0

        # Decode record
        BG = (self.head[1] + mBG) / 10 ** mBGU
        C = (self.body[0] + mC) / 10 ** mCU

        # Not really necessary, but those are correct
        BGTargets = [self.body[4] / 10 ** mBGU, self.body[12] / 10 ** mBGU]
        CSF = self.body[2] / 10 ** mCU

        # Store carbs
        self.values.append([C, CU])



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding carbs to report: '" + self.report + "'..."

        # Load report
        Reporter.load(self.report)

        # Add entries
        Reporter.addEntries(["Carbs"], self.times, self.values)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
