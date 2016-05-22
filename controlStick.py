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



# USER LIBRARIES
from lib import *



# DEFINITIONS
LOGS_ADDRESS = "/home/david/Documents/MeinKPS/stickLogs.txt"
NOW          = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR                  = 0x0a21
    PRODUCT                 = 0x8001

    # INITIALIZATION RESPONSE INDICES
    ACK_INDEX               = 0
    NAK_INDEX               = 33
    STATUS_INDEX            = 1
    SERIAL_INDEX            = range(3, 6)
    FREQUENCY_INDEX         = 8
    DESCRIPTION_INDEX       = range(9, 19)
    VERSION_INDEX           = range(19, 21)
    INTERFACES_INDEX        = range(22, 64)

    # STATUS RESPONSE INDICES
    SIGNAL_INDEX            = 3

    # STICK CONSTANTS
    SIGNAL_THRESHOLD        = 150
    N_REQUEST_ATTEMPTS      = 3
    N_READ_BYTES            = 64
    SLEEP_TIME              = 0.001
    FREQUENCIES             = {0: 916.5, 1: 868.35, 255: 916.5}
    INTERFACES              = {1: "Paradigm RF", 3: "USB"}



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
        self.handle.timeout = 0.5
        self.handle.dsrdtr = True
        self.handle.rtscts = True
        self.handle.xonxoff = False

        # Open serial port
        self.handle.open()

        # Flush input and output
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

        # Ask for stick infos
        self.getInfos()

        # Ask for signal strength
        self.getSignalStrength()



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

        # Read request to send to stick
        print "Request to send: " + str(self.request)

        # Initialize stick response
        self.raw_response = ""

        # Ask for response from stick until we get one
        for i in range(self.N_REQUEST_ATTEMPTS):
            if len(self.raw_response) == 0:

                # Keep track of number of attempts
                print "Request attempt: " + \
                      str(i + 1) + "/" + str(self.N_REQUEST_ATTEMPTS)

                # Send stick command
                self.handle.write(bytearray(self.request))

                # Wait for response
                time.sleep(self.SLEEP_TIME)

                # Read stick response
                self.raw_response = self.handle.read(self.N_READ_BYTES)

            else:
                break

        # If no response at all was received, quit
        if len(self.raw_response) == 0:
            sys.exit("Unable to read from stick. :-(")



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

        # Pad hexadecimal formatted response
        self.response_hex = np.vectorize(padHexaString)(self.response_hex)

        # Correct unreadable characters in string stick response
        self.response_str[self.response < 32] = "."
        self.response_str[self.response > 126] = "."



    def printResponse(self):

        """
        ========================================================================
        PRINTRESPONSE
        ========================================================================

        ...
        """

        # Print original response
        #print self.response

        # Print hexadecimal and string responses in rows of 8 bytes
        for i in range(8):
            print " ".join(self.response_hex[i * 8 : (i + 1) * 8]) + \
                  "\t" + \
                  "".join(self.response_str[i * 8 : (i + 1) * 8])



    def sendRequest(self, request):

        """
        ========================================================================
        SENDREQUEST
        ========================================================================

        ...
        """

        # Set request
        self.request = request

        # Send command to stick and wait for response
        self.getRawResponse()

        # Parse response of stick
        self.parseRawResponse()

        # Print stick response in readable formats
        self.printResponse()



    def emptyBuffer(self):

        """
        ========================================================================
        emptyBuffer
        ========================================================================

        ...
        """

        # Define emptying buffer attempt variable
        n = 0

        while len(self.raw_response) != 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts to free buffer
            print "Freeing buffer attempt: " + str(n) + "/-"

            # Read buffer
            self.raw_response = self.handle.read(self.N_READ_BYTES)

        print "Buffer emptied!"



    def getSignalStrength(self):

        """
        ========================================================================
        GETSIGNALSTRENGTH
        ========================================================================

        ...
        """

        self.signal = 0

        # Define reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.SIGNAL_THRESHOLD:

            # Update attempt variable
            n += 1

            self.sendRequest([6, 0, 0])
            self.signal = self.response[self.SIGNAL_INDEX]

            print "Signal read: " + str(n) + "/-"
            print "Signal strength: " + str(self.signal)

        print



    def getInfos(self):

        """
        ========================================================================
        GETINFOS
        ========================================================================

        ...
        """

        # Ask stick for its infos
        self.sendRequest([4, 0, 0])

        # Get ACK
        self.ack         = self.response[self.ACK_INDEX]

        # Get status
        self.status      = self.response_str[self.STATUS_INDEX]

        # Get serial number
        self.serial      = self.response_hex[self.SERIAL_INDEX]
        self.serial      = "".join(x[2:] for x in self.serial)

        # Get radiofrequency
        self.frequency   = self.response[self.FREQUENCY_INDEX]
        self.frequency   = self.FREQUENCIES[self.frequency]

        # Get description of communication protocol
        self.description = self.response_str[self.DESCRIPTION_INDEX]
        self.description = "".join(self.description)

        # Get software version
        self.version     = self.response[self.VERSION_INDEX]
        self.version     = self.version[0] + 0.01 * self.version[1]

        # Get interfaces
        self.interfaces  = self.response[self.INTERFACES_INDEX]
        self.interfaces  = np.trim_zeros(self.interfaces, "b")
        self.interfaces  = list(self.interfaces)

        # Loop over all found interfaces
        for i in range(len(self.interfaces) / 2):
            self.interfaces[2 * i + 1] = self.INTERFACES[self.interfaces[2 * i + 1]]

        # Print infos
        print "ACK: " + str(self.ack)
        print "Status: " + self.status
        print "Serial: " + self.serial
        print "Radiofrequency: " + str(self.frequency) + " MHz"
        print "Description: " + self.description
        print "Version: " + str(self.version)
        print "Interfaces: " + str(self.interfaces)
        print



    def getUSBState(self):

        """
        ========================================================================
        GETUSBSTATE
        ========================================================================

        ...
        """

        # Ask stick for its USB state
        self.sendRequest([5, 1, 0])

        # Get errors
        self.errors_crc = self.response[3]
        self.errors_seq = self.response[4]
        self.errors_nak = self.response[5]
        self.errors_timeout = self.response[6]
        self.packets_received = self.response[7:11]
        self.packets_sent = self.response[11:15]

        #self.packets_received = self.packets_received[0] << 24 | self.packets_received[1] << 16 | self.packets_received[2] << 8 | self.packets_received[3]
        #self.packets_sent = self.packets_received[0] << 24 | self.packets_received[1] << 16 | self.packets_received[2] << 8 | self.packets_received[3]

        print "Bad CRCs: " + str(self.errors_crc)
        print "Sequential errors: " + str(self.errors_seq)
        print "NAKs: " + str(self.errors_nak)
        print "Timeout errors: " + str(self.errors_timeout)
        print "Packets received: " + str(self.packets_received)
        print "Packets sent: " + str(self.packets_sent)
        print



    def getRFState(self):

        """
        ========================================================================
        GETRFSTATE
        ========================================================================

        ...
        """

        # Ask stick for its USB state
        self.sendRequest([5, 0, 0])

        # Get errors
        self.errors_crc = self.response[3]
        self.errors_seq = self.response[4]
        self.errors_nak = self.response[5]
        self.errors_timeout = self.response[6]
        self.packets_received = self.response[7:11]
        self.packets_sent = self.response[11:15]

        #self.packets_received = self.packets_received[0] << 24 | self.packets_received[1] << 16 | self.packets_received[2] << 8 | self.packets_received[3]
        #self.packets_sent = self.packets_received[0] << 24 | self.packets_received[1] << 16 | self.packets_received[2] << 8 | self.packets_received[3]

        print "Bad CRCs: " + str(self.errors_crc)
        print "Sequential errors: " + str(self.errors_seq)
        print "NAKs: " + str(self.errors_nak)
        print "Timeout errors: " + str(self.errors_timeout)
        print "Packets received: " + str(self.packets_received)
        print "Packets sent: " + str(self.packets_sent)
        print



    def getDownloadState(self):

        """
        ========================================================================
        GETDOWNLOADSTATE
        ========================================================================

        ...
        """

        # Ask stick if data requested is ready to be downloaded
        self.sendRequest([3, 0, 0])

        print



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a stick for me
    my_stick = stick()

    # Start my stick
    my_stick.start()
    
    # Count packets on USB side of stick
    my_stick.getUSBState()

    # Count packets on RF transmitter side of stick
    my_stick.getRFState()

    # Get stick RF buffer status (waiting to download)
    #for i in range(10):
    #    my_stick.getDownloadState()

    # Stop my stick
    my_stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
