#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    cgm

    Author:   David Leclerc

    Version:  0.1

    Date:     08.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import datetime
import serial



# CONSTANTS
codes = {"ReadFirmwareHeader": 11,
         "ReadNumberPages": 16,
         "ReadPages": 17,
         "ReadTransmitterID": 25,
         "ReadLanguage": 27,
         "ReadRTC": 31,
         "ReadBatteryLevel": 33,
         "ReadSystemTime": 34,
         "ReadBGU": 37,
         "ReadBlindedMode": 39,
         "ReadClockMode": 41,
         "ReadBatteryState": 48}

baseTime = datetime.datetime(2009, 1, 1)

batteryStates = [None, 'Charging', 'NotCharging', 'NTCFault', 'BadBattery']

trendArrows = [None, 'DoubleUp', 'SingleUp', '45Up', 'Flat', '45Down',
                     'SingleDown', 'DoubleDown', 'NotComputable', 'OutOfRange']

specialBG = {0: None,
             1: 'SensorNotActive',
             2: 'MinimalDeviation',
             3: 'NoAntenna',
             5: 'SensorNotCalibrated',
             6: 'CountsDeviation',
             9: 'AbsoluteDeviation',
            10: 'PowerDeviation',
            12: 'BadRF'}

languages = {0: None, 1033: 'English'}



class Packet(object):

    # PACKET CHARACTERISTICS

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.head = [1, None, 0]
        self.body = []
        self.size = None
        self.code = None
        self.payload = None
        self.CRC = None



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            [1, SIZE, 0, CODE, ..., PAYLOAD, CRC]

        """



class CGM(object):

    # CGM CHARACTERISTICS
    vendor  = 0x22a3
    product = 0x0047



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
