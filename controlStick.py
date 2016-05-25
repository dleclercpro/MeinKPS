#! /usr/bin/python



"""
================================================================================
TITLE:    controlStick

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     25.05.2016

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
LOGS_ADDRESS = "./stickLogs.txt"
NOW          = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR           = 0x0a21
    PRODUCT          = 0x8001
    SIGNAL_THRESHOLD = 150
    READ_BYTES       = 64
    SLEEP            = 0.1
    FREQUENCIES      = {0: 916.5, 1: 868.35, 255: 916.5}
    INTERFACES       = {1: "Paradigm RF", 3: "USB"}



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
        print "Emptying buffer..."

        # Define emptying buffer attempt variable
        n = 0

        while len(self.raw_response) != 0:

            # Update attempt variable
            n += 1

            # Read buffer
            self.raw_response = self.handle.read(self.READ_BYTES)

        print "Buffer emptied after " + str(n - 1) + " attempt(s)."



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

        # Initialize reading attempt variable
        n = 0

        # Ask for response from stick until we get one
        while len(self.raw_response) == 0:

            # Update attempt variable
            n += 1

            # Keep track of number of attempts
            print "Request attempt: " + str(n) + "/-"

            # Wait a minimum of time before sending request
            time.sleep(self.SLEEP)

            # Send stick request
            self.handle.write(bytearray(self.request))

            # Read stick response
            self.raw_response = self.handle.read(self.READ_BYTES)

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
        self.response_hex = (np.vectorize(lib.padHexadecimalString)
                             (self.response_hex))

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

        # Send request
        self.sendRequest()

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
            print "Look for sufficient signal strength: " + str(n) + "/-"

            # Define request for stick signal strength
            self.request = [6, 0, 0]

            # Send request
            self.sendRequest()

            # Extract signal strength from response
            self.signal = self.response[3]

            # Print signal strength
            print "Signal strength found: " + str(self.signal)
            print "Expected minimal signal strength: " + \
                  str(self.SIGNAL_THRESHOLD)



    def getState(self):

        """
        ========================================================================
        GETSTATE
        ========================================================================

        ...
        """

        # Define request for stick USB state
        self.request = [5, 1, 0]

        # Send request
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

        # Send request
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



    def sendPumpRequest(self):

        """
        ========================================================================
        SENDPUMPREQUEST
        ========================================================================

        ...
        """

        # Initialize pump request
        self.pump_request = []

        # Evaluate parts of pump request based on input
        self.pump_request_head = [1, 0, 167, 1]
        self.pump_request_serial_number = lib.encodePumpSerialNumber(
            self.pump_serial_number)
        self.pump_request_parameter_check = [128 | lib.getByte(
            len(self.pump_request_parameters), 1), lib.getByte(
            len(self.pump_request_parameters), 0)]

        # Build pump request
        self.pump_request.extend(self.pump_request_head)
        self.pump_request.extend(self.pump_request_serial_number)
        self.pump_request.extend(self.pump_request_parameter_check)
        self.pump_request.append(self.pump_request_power)
        self.pump_request.append(self.pump_request_attempts)
        self.pump_request.append(self.pump_request_pages)
        self.pump_request.append(0)
        self.pump_request.append(self.pump_request_code)
        self.pump_request.append(lib.computeCRC8(self.pump_request))
        self.pump_request.extend(self.pump_request_parameters)
        self.pump_request.append(lib.computeCRC8(self.pump_request_parameters))

        # Save pump request to stick request variable
        self.request = self.pump_request

        # Send request
        self.sendRequest()



    def askPumpData(self):

        """
        ========================================================================
        ASKPUMPDATA
        ========================================================================

        ...
        """

        # Initialize number of bytes waiting in buffer
        self.bytes_ready = 0

        # Define asking attempt variable
        n = 0

        # If number of bytes waiting is correct, data is ready
        while (self.bytes_ready < 64) & (self.bytes_ready != 15):

            # Update attempt variable
            n += 1

            # Keep track of attempts
            print "Look for pump data in buffer: " + str(n) + "/-"

            # Define request to ask stick if data was received
            self.request = [3, 0, 0]

            # Send request
            self.sendRequest()

            # Get size of response waiting in radio buffer
            self.bytes_ready = self.response[7]



    def getPumpData(self):

        """
        ========================================================================
        GETPUMPDATA
        ========================================================================

        ...
        """

        # Ask if data was correctly received on first try
        self.askPumpData()

        # If not, resend pump request
        while self.bytes_ready != self.expected_bytes:

            # Give user info
            print "Number of bytes found: " + str(self.bytes_ready)
            print "Expected number of bytes: " + str(self.expected_bytes)

            # Empty buffer after asking repeatedly if data was ready
            self.emptyBuffer()

            # Give user info
            print "Resending pump request..."

            # Reset stick request to pump request
            self.request = self.pump_request

            # Resend request to pump
            self.sendPumpRequest()

            # Ask pump if data is ready to be read
            self.askPumpData()

        # Give user info
        print "Number of bytes ready to be read: " + \
              str(self.bytes_ready)

        # Initialize request asking stick to read data in its buffer
        self.request = []

        # Build request
        self.request.extend([12, 0])
        self.request.extend([lib.getByte(self.bytes_ready, 1),
                            lib.getByte(self.bytes_ready, 0)])
        self.request.append(lib.computeCRC8(self.request))

        # Send request
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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
