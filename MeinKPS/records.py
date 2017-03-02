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
import requester
import decoder



# Instanciate a requester
Requester = requester.Requester()

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



    def find(self, n):

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

        # Assign history pages to decode
        self.pages = self.pump.history.get()

        # Decode record
        self.decode()



class BolusRecord(PumpRecord):

    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump record
        Decoder.decodeBolusRecord(code = 1, size = 9, pages = self.pages)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
