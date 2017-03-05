#! /usr/bin/python

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

# USER LIBRARIES
import lib
import decoder



# Instanciate a decoder
Decoder = decoder.Decoder()



# PUMP RECORDS
class PumpRecord(object):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute size of record
        self.size = self.headSize + self.dateSize + self.bodySize

        # Store pump
        self.pump = pump

        # Store target
        self.target = target



    def extract(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Extract every part of record using a running variable
        x = 0

        # Extract head
        self.head = self.bytes[x:self.headSize]

        # Update running variable
        x += self.headSize

        # Extract date
        self.date = self.bytes[x:x + self.dateSize]

        # Update running variable
        x += self.dateSize

        # Extract body
        self.body = self.bytes[x:x + self.bodySize]



    def find(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update decoder's device
        Decoder.device = self.pump

        # Update decoder's target
        Decoder.target = self.target

        # Get precedently read pump history pages
        pages = self.pump.history.pages

        # Search history pages for specified record
        for i in range(len(pages)):

            # Try and find record
            try:

                # Define new possible record
                self.bytes = pages[i:i + self.size]

                # Test criteria
                if self.criteria(self.bytes):

                    # Disassemble record
                    self.extract()

                    # Decode record
                    Decoder.decodeRecord(self.__class__.__name__, self.head,
                                                                  self.date,
                                                                  self.body)

            # If not matching, move to next one
            except:
                pass

        # Print records that were found
        self.give()



    def give(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Count number of entries found
        n = len(self.target.times) or len(self.target.values)

        # Get name of record
        record = self.__class__.__name__

        # Give user info
        print "Found " + str(n) + " '" + record + "':"

        for i in range(n):

            # Get current time
            try:
                time = self.target.times[i]

            except:
                time = None

            # Get current value
            try:
                value = self.target.values[i]

            except:
                value = None

            # Print current record
            print str(value) + " (" + str(time) + ")"



class SuspendRecord(PumpRecord):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define record characteristics
        self.code = 30
        self.headSize = 2
        self.dateSize = 5
        self.bodySize = 0

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize record
        super(self.__class__, self).__init__(pump, target)



class ResumeRecord(PumpRecord):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define record characteristics
        self.code = 31
        self.headSize = 2
        self.dateSize = 5
        self.bodySize = 0

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code and x[1] == 0

        # Initialize record
        super(self.__class__, self).__init__(pump, target)



class BolusRecord(PumpRecord):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define record characteristics
        self.code = 1
        self.headSize = 4
        self.dateSize = 5
        self.bodySize = 0

        # Define record's criteria
        self.criteria = (lambda x: x[0] == self.code and
                                   x[1] == x[2] and
                                   x[3] == 0)

        # Initialize record
        super(self.__class__, self).__init__(pump, target)



class CarbsRecord(PumpRecord):

    def __init__(self, pump, target):

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
        self.headSize = 2
        self.dateSize = 5
        self.bodySize = 13

        # Define record's criteria
        self.criteria = lambda x: x[0] == self.code

        # Initialize record
        super(self.__class__, self).__init__(pump, target)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
