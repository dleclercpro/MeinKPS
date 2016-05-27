#! /usr/bin/python



"""
================================================================================
Title:    stick
Author:   David Leclerc
Version:  1.0
Date:     27.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: This is a script that allows to retrieve informations from a MiniMed
          insulin pump, using the CareLink USB stick of Medtronic. It is based
          on the PySerial library and is a work of reverse-engineering the USB
          communication protocols of said USB stick.
Notes:    ...
================================================================================
"""



# LIBRARIES
import serial
import os
import sys
import numpy as np



# USER LIBRARIES
import lib



class Stick:

    # STICK CHARACTERISTICS
    TALKATIVE        = True
    VENDOR           = 0x0a21
    PRODUCT          = 0x8001
    SIGNAL_THRESHOLD = 150
    READ_BYTES       = 64
    SLEEP            = 0.1
    FREQUENCIES      = {0 : 916.5, 1 : 868.35, 255 : 916.5}
    INTERFACES       = {1 : "Paradigm RF", 3 : "USB"}



    def getHandle(self):

        """
        ========================================================================
        GETHANDLE
        ========================================================================
        """

        # Generate serial port
        os.system("modprobe --quiet --first-time usbserial"
            + " vendor=" + str(self.VENDOR)
            + " product=" + str(self.PRODUCT))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.timeout = 0.5
        self.handle.rtscts = True
        self.handle.dsrdtr = True

        # Open serial port
        self.handle.open()



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Generate handle for the stick
        self.getHandle()

        # Ask for stick infos
        self.getInfos()

        # Ask for signal strength
        self.getSignalStrength()

        # Get state of stick
        self.getState()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================
        """

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("modprobe --quiet --remove usbserial")



    def emptyBuffer(self):

        """
        ========================================================================
        EMPTYBUFFER
        ========================================================================
        """

        # Tell user the buffer is going to be emptied
        if self.TALKATIVE:
            print "Emptying buffer..."

        # Define emptying buffer attempt variable
        n = 0

        while len(self.raw_response) != 0:

            # Update attempt variable
            n += 1

            # Read buffer
            self.raw_response = self.handle.read(self.READ_BYTES)

        # Give user info
        if self.TALKATIVE:
            print "Buffer emptied after " + str(n - 1) + " attempt(s)."



    def sendRequest(self, request):

        """
        ========================================================================
        SENDREQUEST
        ========================================================================
        """

        # Print request to send to stick
        if self.TALKATIVE:
            print "Sending request: " + str(request)

        # Initialize stick raw response
        self.raw_response = ""

        # Initialize reading attempt variable
        n = 0

        # Ask for response from stick until we get one
        while len(self.raw_response) == 0:

            # Update attempt variable
            n += 1

            # Keep track of number of attempts
            if self.TALKATIVE:
                print "Request attempt: " + str(n) + "/-"

            # Wait a minimum of time before sending request
            time.sleep(self.SLEEP)

            # Send stick request
            self.handle.write(bytearray(request))

            # Give user info
            if self.TALKATIVE:
                print "Storing raw response..."

            # Read stick response
            self.raw_response = self.handle.read(self.READ_BYTES)

        # If no response at all was received, quit
        if len(self.raw_response) == 0:
            sys.exit("Unable to read from stick. :-(")

        # Parse response of stick
        self.parseResponse()

        # Print stick response in readable formats
        self.printResponse()

        # Empty buffer for the next request
        self.emptyBuffer()



    def parseResponse(self):

        """
        ========================================================================
        PARSERESPONSE
        ========================================================================
        """

        # Give user info
        if self.TALKATIVE:
            print "Parsing raw response..."

        # Vectorize raw response
        self.response = [x for x in self.raw_response]

        # Convert stick response to various formats for more convenience
        self.response = np.vectorize(ord)(self.response)
        self.response_hex = np.vectorize(hex)(self.response)
        self.response_str = np.vectorize(chr)(self.response)

        # Pad hexadecimal formatted response
        self.response_hex = np.vectorize(lib.padHexadecimal)(self.response_hex)

        # Correct unreadable characters in string stick response
        self.response_str[self.response < 32] = "."
        self.response_str[self.response > 126] = "."



    def printResponse(self):

        """
        ========================================================================
        PRINTRESPONSE
        ========================================================================
        """

        # Define number of rows [of 8 bytes] to be printed 
        n_rows = len(self.response) / 8 + int(len(self.response) % 8 != 0)

        # Print response
        if self.TALKATIVE:
            print "Response: " + str(self.response)

        # Print hexadecimal and string responses
        if self.TALKATIVE:
            for i in range(n_rows):
                print " ".join(self.response_hex[i * 8 : (i + 1) * 8]) + \
                      "\t" + \
                      "".join(self.response_str[i * 8 : (i + 1) * 8])



    def getInfos(self):

        """
        ========================================================================
        GETINFOS
        ========================================================================
        """

        # Send request for stick infos
        self.sendRequest([4, 0, 0])

        # Extract ACK
        self.ack = self.response[0]

        # Extract status
        self.status = self.response_str[1]

        # Extract serial number
        self.serial = "".join(x[2:] for x in self.response_hex[3:6])

        # Extract radiofrequency
        self.frequency = self.FREQUENCIES[self.response[8]]

        # Extract description of communication protocol
        self.description = "".join(self.response_str[9:19])

        # Extract software version
        self.version = 1.00 * self.response[19:21][0] + \
                       0.01 * self.response[19:21][1]

        # Extract interfaces
        self.interfaces = np.trim_zeros(self.response[22:64], "b")

        # Print infos
        if self.TALKATIVE:
            print "ACK: " + str(self.ack)
            print "Status: " + self.status
            print "Serial: " + self.serial
            print "Radiofrequency: " + str(self.frequency) + " MHz"
            print "Description: " + self.description
            print "Version: " + str(self.version)
            print "Interfaces: " + str(self.interfaces)



    def getSignalStrength(self):

        """
        ========================================================================
        GETSIGNALSTRENGTH
        ========================================================================
        """

        # Initialize signal strength
        self.signal = 0

        # Define reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.SIGNAL_THRESHOLD:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            if self.TALKATIVE:
                print "Look for sufficient signal strength: " + str(n) + "/-"

            # Send request for stick signal strength
            self.sendRequest([6, 0, 0])

            # Extract signal strength from response
            self.signal = self.response[3]

            # Print signal strength
            if self.TALKATIVE:
                print "Signal strength found: " + str(self.signal)
                print "Expected minimal signal strength: " + \
                      str(self.SIGNAL_THRESHOLD)



    def getState(self):

        """
        ========================================================================
        GETSTATE
        ========================================================================
        """

        # Send request for stick USB state
        self.sendRequest([5, 1, 0])

        # Extract errors
        self.usb_errors_crc = self.response[3]
        self.usb_errors_seq = self.response[4]
        self.usb_errors_nak = self.response[5]
        self.usb_errors_timeout = self.response[6]
        self.usb_packets_received = lib.convertBytes(self.response[7:11])
        self.usb_packets_sent = lib.convertBytes(self.response[11:15])

        # Print USB state
        if self.TALKATIVE:
            print "USB Bad CRCs: " + str(self.usb_errors_crc)
            print "USB Sequential errors: " + str(self.usb_errors_seq)
            print "USB NAKs: " + str(self.usb_errors_nak)
            print "USB Timeout errors: " + str(self.usb_errors_timeout)
            print "USB Packets received: " + str(self.usb_packets_received)
            print "USB Packets sent: " + str(self.usb_packets_sent)

        # Send request for stick RF state
        self.sendRequest([5, 0, 0])

        # Extract errors
        self.rf_errors_crc = self.response[3]
        self.rf_errors_seq = self.response[4]
        self.rf_errors_nak = self.response[5]
        self.rf_errors_timeout = self.response[6]
        self.rf_packets_received = lib.convertBytes(self.response[7:11])
        self.rf_packets_sent = lib.convertBytes(self.response[11:15])

        # Print RF state
        if self.TALKATIVE:
            print "RF Bad CRCs: " + str(self.rf_errors_crc)
            print "RF Sequential errors: " + str(self.rf_errors_seq)
            print "RF NAKs: " + str(self.rf_errors_nak)
            print "RF Timeout errors: " + str(self.rf_errors_timeout)
            print "RF Packets received: " + str(self.rf_packets_received)
            print "RF Packets sent: " + str(self.rf_packets_sent)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a stick for me
    stick = Stick()

    # Start my stick
    stick.start()

    # Stop my stick
    stick.stop()

    # End of script
    print "Done!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
