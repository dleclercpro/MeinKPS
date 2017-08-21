#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    tester

    Author:   David Leclerc

    Version:  0.1

    Date:     21.08.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script meant to find new records within history pages
              read from Medtronic MiniMed pumps.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib
from Pump import pump



# Find records based on decoded dates
def findRecords(history):

    # Get current time
    now = datetime.datetime.now()

    # Initialize variable for EOR (end of last record)
    EOR = 0

    # Give user info
    print "Trying to find event records in pump history..."

    for i in range(len(history)):

        try:

            # Assign record date, assuming a date is always 5 bytes
            date = history[i:i + 5]

            # Extract time at which bolus was delivered
            t = lib.decodeTime(date)

            # Build datetime object
            t = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

            # Proof check record year
            if abs(t.year - now.year) > 1:

                raise ValueError("Record and current year too far apart!")

            # Extract head of record
            head = history[EOR:i]

            # Update EOR
            EOR = i + 5

            # Give user output
            print "Record:"
            print str(head) + ", " + str(date) + " - " + str(t)

        except:
            pass



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a pump for me
    myPump = pump.Pump()

    # Start dialogue with pump
    myPump.start()

    # Read pump history
    myPump.history.read(2)

    # Decode it
    findRecords(myPump.history.pages)

    # Stop dialogue with pump
    myPump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()