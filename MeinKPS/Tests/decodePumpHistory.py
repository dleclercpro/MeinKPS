#! /usr/bin/python

"""
================================================================================

    Title:    decode

    Author:   David Leclerc

    Version:  0.2

    Date:     15.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that is meant to decode history pages read from
              Medtronic MiniMed pumps.

    Notes:    ...

================================================================================
"""

# LIBRARIES
import numpy as np



# USER LIBRARIES
import lib



# Initialize variable for EOR (end of last record)
EOR = 0

# Find records based on decoded dates
def findRecords(history):

    for i in range(len(history)):

        try:
            # Assign record date, assuming a date is always 5 bytes
            date = history[i:i + 5]

            # Extract time at which bolus was delivered
            time = lib.parseTime(date)

            # Build datetime object
            time = datetime.datetime(time[0], time[1], time[2],
                                     time[3], time[4], time[5])

            # Proof check record year
            if abs(time.year - now.year) > 1:

                raise ValueError("Record and current year too far apart!")

            # Extract head of record
            head = history[EOR:i]

            # Update EOR
            EOR = i + 5

            # Give user output
            print "Record:"
            print str(head) + ", " + str(date) + " - " + str(time)

        except:
            pass
