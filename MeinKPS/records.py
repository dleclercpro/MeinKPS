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

        # Store pump
        self.pump = pump

        # Store target of command response
        self.target = target

        # Compute size of record
        self.size = self.headSize + self.dateSize + self.bodySize



    def find(self, n = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update decoder's device
        Decoder.device = self.pump

        # Update decoder's target
        Decoder.target = self.target

        # Download n pages of pump history (or all of it if none is given)
        self.pump.history.read(n)

        # Get precedently read pump history pages
        pages = self.pump.history.pages

        # Search history pages for specified record
        for i in range(len(pages)):

            # Try and find record
            try:

                # Define new possible record
                record = pages[i:i + self.size]

                # Test criteria
                if self.criteria(record):

                    # Deassemble record with running variable
                    x = 0

                    # Isolate head
                    head = record[x:self.headSize]

                    # Update running variable
                    x += self.headSize

                    # Isolate date
                    date = record[x:x + self.dateSize]

                    # Update running variable
                    x += self.dateSize

                    # Isolate body
                    body = record[x:x + self.bodySize]

                    # Decode record
                    Decoder.decodeRecord(self.__class__.__name__, head,
                                                                  date,
                                                                  body)

            # If not matching, move to next one
            except:
                pass



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



class BolusWizardRecord(PumpRecord):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
