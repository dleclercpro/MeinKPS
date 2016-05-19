#! /usr/bin/python

"""
================================================================================
TITLE:    controlStick

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     19.05.2016

LICENSE:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

OVERVIEW: This is a script that allows to retrieve informations from a MiniMed
          insulin pump, using the CareLink USB stick of Medtronic. It is based
          on the PySerial library and is a work of reverse-engineering the USB
          communication protocols of said USB stick.

NOTES:    ...
================================================================================
"""

# LIBRARIES
import serial
import os
import sys
import time
import datetime
import numpy as np

# DEFINITIONS
LOGS_ADDRESS = '/home/david/Documents/MeinKPS/stickLogs.txt'
NOW          = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR                  = 0x0a21
    PRODUCT                 = 0x8001

    # INITIALIZATION RESPONSE INDICES
    ACK                     = 0
    STATUS                  = 1
    SERIAL                  = range(3, 6)
    RADIOFREQUENCY          = 8
    DESCRIPTION             = range(9, 19)
    VERSION                 = range(19, 21)
    INTERFACES              = range(21, 64)

    # STATUS RESPONSE INDICES
    SIGNAL                  = 3

    # STICK CONSTANTS
    SIGNAL_THRESHOLD        = 150
    N_READ_ATTEMPTS         = 5
    N_READ_BYTES            = 64
    SLEEP_TIME              = 0.25



    def getHandle(self):

        """
        ========================================================================
        GETHANDLE
        ========================================================================

        ...
        """

        # Generate serial port
        os.system("sudo modprobe --first-time usbserial"
            + " vendor=" + str(self.VENDOR)
            + " product=" + str(self.PRODUCT))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.baudrate = 9600
        self.handle.xonxoff = False
        self.handle.rtscts = True
        self.handle.dsrdtr = True
        self.handle.timeout = 0.5

        # Open serial port
        self.handle.open()
        self.handle.flushInput()
        self.handle.flushOutput()



    def start(self):

        """
        ========================================================================
        START
        ========================================================================

        ...
        """

        # Generate handle for the stick
        self.getHandle()

        # Ask for stick info
        self.sendRequest([4, 0, 0])

        self.ack            = self.response[self.ACK]
        self.status         = self.response[self.STATUS]
        self.serial         = self.response[self.SERIAL]
        self.radiofrequency = self.response[self.RADIOFREQUENCY]
        self.description    = self.response[self.DESCRIPTION]
        self.version        = self.response[self.VERSION]
        self.interfaces     = self.response[self.INTERFACES]

        print "ACK: " + str(self.ack)
        print "Status: " + str(self.status)
        print "Serial: " + str(self.serial)
        print "Radiofrequency: " + str(self.radiofrequency)
        print "Description: " + str(self.description)
        print "Version: " + str(self.version)
        print "Interfaces: " + str(self.interfaces)

        # Ask for stick status, namely signal strength
        self.signal = 0

        while self.signal < self.SIGNAL_THRESHOLD:
            self.sendRequest([6, 0, 0])
            self.signal = self.response[self.SIGNAL]

            print "Signal strength: " + str(self.signal)



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================

        ...
        """    

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("sudo modprobe -r usbserial")



    def getRawResponse(self):

        """
        ========================================================================
        GETRAWRESPONSE
        ========================================================================

        ...
        """

        # Read command to send to stick
        print "Request to send: " + str(self.request)

        # Initialize stick response
        self.raw_response = ""

        # Ask for response from stick until we get one
        for i in range(self.N_READ_ATTEMPTS):
            if len(self.raw_response) == 0:

                # Keep track of number of reading trials
                print "Reading attempt: " + str(i + 1) +
                      "/" + str(self.N_READ_ATTEMPTS)

                # Send stick command
                self.handle.write(bytearray(self.request))

                # Wait for response
                time.sleep(self.SLEEP_TIME)

                # Read stick response
                self.raw_response = self.handle.read(self.N_READ_BYTES)

            else:
                break



    def parseRawResponse(self):

        """
        ========================================================================
        PARSERAWRESPONSE
        ========================================================================

        ...
        """

        # Vectorize raw response
        self.raw_response = [x for x in self.raw_response]

        # Convert stick response to various formats for more convenience
        self.response = np.vectorize(ord)(self.raw_response)
        self.response_hex = np.vectorize(hex)(self.response)
        self.response_str = np.vectorize(chr)(self.response)

        # Correct unreadable characters in string stick response
        self.response_str[self.response < 32] = "."
        self.response_str[self.response > 126] = "."



    def sendRequest(self, request):

        """
        ========================================================================
        SENDREQUEST
        ========================================================================

        ...
        """

        # Save request in stick instance
        self.request = request

        # Send command to stick and wait for response
        self.getRawResponse()

        # Parse response of stick
        self.parseRawResponse()

        # Print stick response in readable formats
        print self.response

        for i in range(8):
            print ' '.join(self.response_hex[i * 8 : (i + 1) * 8])

        for i in range(8):
            print ''.join(self.response_str[i * 8 : (i + 1) * 8])



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a stick for me
    my_stick = stick()

    # Start stick
    my_stick.start()

    # Get stick status
    #response = sendRequest(self.handle, [3, 0, 0], 0)
    #print "ACK: " + str(response)
    #print "\n"
    
    # Count packets on USB side of stick
    #response = sendRequest(self.handle, [5, 1, 0], 0)
    #print "ACK: " + str(response)
    #print "\n"

    # Count packets on RF side of stick
    #response = sendRequest(self.handle, [5, 0, 0], 0)
    #print "ACK: " + str(response)
    #print "\n"

    #for i in range(5):
    #    if len(response) == 0:
    #        print "No response..."
    #        time.sleep(0.5)
    #        response = self.handle.read(self.N_READ_BYTES)
    #    else:
    #        print "Got response!"
    #        print response.decode()
    #        break

    # Stop stick
    my_stick.stop()

    # End of script
    print 'Done!'



# Run script when called from terminal
if __name__ == '__main__':
    main()
