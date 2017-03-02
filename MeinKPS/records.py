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

        # Initialize history pages in which to search for record
        self.pages = None



    def search(self, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEARCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update decoder's device
        Decoder.device = self.pump

        # Update decoder's target
        Decoder.target = self.target

        # Download n pages of pump history (or all of it if none is given)
        self.pump.history.read(n)

        # Find record in precedently read pump history pages
        self.find(self.pump.history.pages)



    def find(self, pages):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Search history pages for specified record
        for i in range(len(pages)):

            # Try and find record
            try:

                # Define new possible record
                record = pages[i:i + self.size]

                # Test criteria
                if self.criteria(record):

                    # Decode record
                    Decoder.decodeRecord(self.__class__.__name__, record)

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

        # Initialize record
        super(self.__class__, self).__init__(pump, target)

        # Define record characteristics
        self.code = 1
        self.size = 9

        # Define record's criteria
        self.criteria = (lambda x: x[0] == self.code and
                                   x[1] == x[2] and
                                   x[3] == 0)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
