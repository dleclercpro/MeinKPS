#! /usr/bin/python

"""
================================================================================

    Title:    decoder

    Author:   David Leclerc

    Version:  0.1

    Date:     18.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that decoding functions for all devices used
              within MeinKPS.

    Notes:    ...

================================================================================
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib



class Decoder:

    # DECODER CHARACTERISTICS



    def decode(self, device, command):

        """
        ========================================================================
        DECODE
        ========================================================================
        """

        # Decode readTime command
        if command == "readTime":

            # Extract pump time from received data
            second = device.requester.data[2]
            minute = device.requester.data[1]
            hour   = device.requester.data[0]
            day    = device.requester.data[6]
            month  = device.requester.data[5]
            year   = lib.bangInt(device.requester.data[3:5])

            # Generate time object
            time = datetime.datetime(year, month, day, hour, minute, second)

            # Store formatted time
            device.time = lib.formatTime(time)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    #print command.__class__.__name__



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
