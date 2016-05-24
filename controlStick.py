#! /usr/bin/python



"""
================================================================================
TITLE:    controlStick

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     24.05.2016

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
import lib



# DEFINITIONS
LOGS_ADDRESS    = "./stickLogs.txt"
NOW             = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR                  = 0x0a21
    PRODUCT                 = 0x8001
    PUMP_SERIAL_NUMBER      = 574180
    SIGNAL_THRESHOLD        = 150
    REQUEST_ATTEMPTS        = 3
    DOWNLOAD_ATTEMPTS       = 15
    READ_BYTES              = 64
    SLEEP_TIME              = 0.1
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
        self.handle.timeout = 0.5
        self.handle.rtscts = True
        self.handle.dsrdtr = True

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

        # Prepare stick to received requests
        self.emptyBuffer()

        # Get state of stick
        self.getState()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================

        ...
        """

        # Print empty line to make output easier to read
        print

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("sudo modprobe -r usbserial")



    def emptyBuffer(self):

        """
        ========================================================================
        EMPTYBUFFER
        ========================================================================

        ...
        """

        # Tell user the buffer is going to be emptied
        print "Trying to empty buffer..."

        # Define emptying buffer attempt variable
        n = 0

        while len(self.raw_response) != 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts to free buffer
            print "Freeing buffer attempt: " + str(n) + "/-"

            # Read buffer
            self.raw_response = self.handle.read(self.READ_BYTES)

        print "Buffer emptied!"



    def sendRequest(self):

        """
        ========================================================================
        SENDREQUEST
        ========================================================================

        ...
        """

        # Print request to send to stick
        print "Sending request: " + str(self.request)

        # Initialize stick response
        self.raw_response = ""

        # Ask for response from stick until we get one
        for i in range(self.REQUEST_ATTEMPTS):
            if len(self.raw_response) == 0:

                # Keep track of number of attempts
                print "Request attempt: " + \
                      str(i + 1) + "/" + str(self.REQUEST_ATTEMPTS)

                # Send stick command
                self.handle.write(bytearray(self.request))

                # Wait for response
                time.sleep(self.SLEEP_TIME)

                # Read stick response
                self.raw_response = self.handle.read(self.READ_BYTES)

            else:
                break

        # If no response at all was received, quit
        if len(self.raw_response) == 0:
            sys.exit("Unable to read from stick. :-(")

        # Parse response of stick
        self.parseResponse()

        # Print stick response in readable formats
        self.printResponse()



    def parseResponse(self):

        """
        ========================================================================
        PARSERESPONSE
        ========================================================================

        ...
        """

        # Vectorize raw response
        self.response = [x for x in self.raw_response]

        # Convert stick response to various formats for more convenience
        self.response = np.vectorize(ord)(self.response)
        self.response_hex = np.vectorize(hex)(self.response)
        self.response_str = np.vectorize(chr)(self.response)

        # Pad hexadecimal formatted response
        self.response_hex = np.vectorize(lib.padHexadecimalString) \
                                        (self.response_hex)

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

        # Define number of rows [of 8 bytes] to be printed 
        n_rows = len(self.response) / 8 + int(len(self.response) % 8 != 0)

        # Print response
        #print self.response

        # Print hexadecimal and string responses
        for i in range(n_rows):
            print " ".join(self.response_hex[i * 8 : (i + 1) * 8]) + \
                  "\t" + \
                  "".join(self.response_str[i * 8 : (i + 1) * 8])



    def getInfos(self):

        """
        ========================================================================
        GETINFOS
        ========================================================================

        ...
        """

        # Define request for stick infos
        self.request = [4, 0, 0]

        # Send said request
        self.sendRequest()

        # Extract ACK
        self.ack         = self.response[0]

        # Extract status
        self.status      = self.response_str[1]

        # Extract serial number
        self.serial      = "".join(x[2:] for x in self.response_hex[3:6])

        # Extract radiofrequency
        self.frequency   = self.FREQUENCIES[self.response[8]]

        # Extract description of communication protocol
        self.description = "".join(self.response_str[9:19])

        # Extract software version
        self.version     = 1.00 * self.response[19:21][0] + \
                           0.01 * self.response[19:21][1]

        # Extract interfaces
        self.interfaces  = np.trim_zeros(self.response[22:64], "b")

        # Print infos
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

        ...
        """

        self.signal = 0

        # Define reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.SIGNAL_THRESHOLD:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            print "Signal read: " + str(n) + "/-"

            # Define request for stick signal strength
            self.request = [6, 0, 0]

            # Send said request
            self.sendRequest()

            # Extract signal strength from response
            self.signal = self.response[3]

            # Print signal strength
            print "Signal strength: " + str(self.signal)



    def getState(self):

        """
        ========================================================================
        GETSTATE
        ========================================================================

        ...
        """

        # Define request for stick USB state
        self.request = [5, 1, 0]

        # Send said request
        self.sendRequest()

        # Extract errors
        self.usb_errors_crc = self.response[3]
        self.usb_errors_seq = self.response[4]
        self.usb_errors_nak = self.response[5]
        self.usb_errors_timeout = self.response[6]
        self.usb_packets_received = lib.convertBytesDecimal(self.response[7:11])
        self.usb_packets_sent = lib.convertBytesDecimal(self.response[11:15])

        # Print USB state
        print "USB Bad CRCs: " + str(self.usb_errors_crc)
        print "USB Sequential errors: " + str(self.usb_errors_seq)
        print "USB NAKs: " + str(self.usb_errors_nak)
        print "USB Timeout errors: " + str(self.usb_errors_timeout)
        print "USB Packets received: " + str(self.usb_packets_received)
        print "USB Packets sent: " + str(self.usb_packets_sent)

        # Define request for stick RF state
        self.request = [5, 0, 0]

        # Send said request
        self.sendRequest()

        # Extract errors
        self.rf_errors_crc = self.response[3]
        self.rf_errors_seq = self.response[4]
        self.rf_errors_nak = self.response[5]
        self.rf_errors_timeout = self.response[6]
        self.rf_packets_received = lib.convertBytesDecimal(self.response[7:11])
        self.rf_packets_sent = lib.convertBytesDecimal(self.response[11:15])

        # Print RF state
        print "RF Bad CRCs: " + str(self.rf_errors_crc)
        print "RF Sequential errors: " + str(self.rf_errors_seq)
        print "RF NAKs: " + str(self.rf_errors_nak)
        print "RF Timeout errors: " + str(self.rf_errors_timeout)
        print "RF Packets received: " + str(self.rf_packets_received)
        print "RF Packets sent: " + str(self.rf_packets_sent)



    def sendPumpRequest(self, expecting_data = False):

        """
        ========================================================================
        SENDPUMPREQUEST
        ========================================================================

        ...
        """

        # Initialize request to send to pump
        self.request = []

        # Evaluate some parts of request first
        self.request_head = [1, 0, 167, 1]
        self.request_serial_number = [ord(x) for x in
            str(self.PUMP_SERIAL_NUMBER).decode("hex")]
        self.request_parameters_info = [128 |
            lib.getByte(len(self.request_parameters), 1),
            lib.getByte(len(self.request_parameters), 0)]

        # Build said request
        self.request.extend(self.request_head)
        self.request.extend(self.request_serial_number)
        self.request.extend(self.request_parameters_info)
        self.request.append(self.request_power)
        self.request.append(self.request_attempts)
        self.request.append(self.request_pages)
        self.request.append(0)
        self.request.append(self.request_code)
        self.request.append(lib.computeCRC8(self.request))
        self.request.extend(self.request_parameters)
        self.request.append(lib.computeCRC8(self.request_parameters))

        # Send said request
        self.sendRequest()

        # If expecting data, ask stick to get it on the radio buffer
        if expecting_data:

            # Initialize number of waiting bytes
            self.bytes_waiting = 0

            # Define downloading attempt variable
            n = 0

            # Ask stick if data requested is ready to be downloaded until it is
            for i in range(self.DOWNLOAD_ATTEMPTS):

                # Verify if number of bytes waiting is correct
                if (self.bytes_waiting < 64) & (self.bytes_waiting != 15):

                    # Update attempt variable
                    n += 1

                    # Keep track of attempts
                    print "Pump data read attempt: " + \
                          str(n) + "/" + str(self.DOWNLOAD_ATTEMPTS)

                    # Define request to ask if data is received
                    self.request = [3, 0, 0]

                    # Send said request
                    self.sendRequest()

                    # Get size of response waiting in radio buffer
                    self.bytes_waiting = self.response[7]

                else:
                    break

            # If number of waiting bytes was always incorrectly found, quit
            if (self.bytes_waiting < 64) & (self.bytes_waiting != 15):
                sys.exit("Unable to get a correct number of bytes waiting " + \
                         "to be downloaded. :-(")

            # Otherwise, download data
            else:
                print "Number of bytes waiting to be downloaded: " + \
                      str(self.bytes_waiting)

                # Initialize request asking stick to download data in the buffer
                self.request = []

                # Build said request
                self.request.extend([12, 0])
                self.request.extend([lib.getByte(self.bytes_waiting, 1),
                                    lib.getByte(self.bytes_waiting, 0)])
                self.request.append(lib.computeCRC8(self.request))

                # Send said request
                self.sendRequest()

                # Empty buffer for next command
                self.emptyBuffer()



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

    # Stop my stick
    my_stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
