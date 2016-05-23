#! /usr/bin/python



"""
================================================================================
TITLE:    controlStick

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     22.05.2016

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
LOGS_ADDRESS                = "/home/david/Documents/MeinKPS/stickLogs.txt"
NOW                         = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR                  = 0x0a21
    PRODUCT                 = 0x8001
    SERIAL_NUMBER           = 574180
    SIGNAL_THRESHOLD        = 150
    N_REQUEST_ATTEMPTS      = 3
    N_READ_BYTES            = 64
    SLEEP_TIME              = 0.001
    FREQUENCIES             = {0: 916.5, 1: 868.35, 255: 916.5}
    INTERADIOACES              = {1: "Paradigm RADIO", 3: "USB"}



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

        # Prepare stick to received requests    ###
        self.emptyBuffer()



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



    def emptyBuffer(self):

        """
        ========================================================================
        EMPTYBUFFER
        ========================================================================

        ...
        """

        # Print empty line for easier reading of output in terminal
        print

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
            self.raw_response = self.handle.read(self.N_READ_BYTES)

        print "Buffer emptied!"



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

        # Print vectorized raw response
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

        # Print empty line for easier reading of output in terminal
        print

        # Set request
        self.request = request

        # Send command to stick and wait for response
        self.getRawResponse()

        # Parse response of stick
        self.parseRawResponse()

        # Print stick response in readable formats
        self.printResponse()



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
            self.signal = self.response[3]

            print "Signal read: " + str(n) + "/-"
            print "Signal strength: " + str(self.signal)



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
        self.ack         = self.response[0]

        # Get status
        self.status      = self.response_str[1]

        # Get serial number
        self.serial      = "".join(x[2:] for x in self.response_hex[3:6])

        # Get radiofrequency
        self.frequency   = self.FREQUENCIES[self.response[8]]

        # Get description of communication protocol
        self.description = "".join(self.response_str[9:19])

        # Get software version
        self.version     = 1.00 * self.response[19:21][0] + \
                           0.01 * self.response[19:21][1]

        # Get interfaces
        self.interfaces  = np.trim_zeros(self.response[22:64], "b")

        # Print infos
        print "ACK: " + str(self.ack)
        print "Status: " + self.status
        print "Serial: " + self.serial
        print "Radiofrequency: " + str(self.frequency) + " MHz"
        print "Description: " + self.description
        print "Version: " + str(self.version)
        print "Interfaces: " + str(self.interfaces)



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
        self.usb_errors_crc = self.response[3]
        self.usb_errors_seq = self.response[4]
        self.usb_errors_nak = self.response[5]
        self.usb_errors_timeout = self.response[6]
        self.usb_packets_received = lib.getNumberPackets(self.response[7:11])
        self.usb_packets_sent = lib.getNumberPackets(self.response[11:15])

        # Print USB state
        print "USB Bad CRCs: " + str(self.usb_errors_crc)
        print "USB Sequential errors: " + str(self.usb_errors_seq)
        print "USB NAKs: " + str(self.usb_errors_nak)
        print "USB Timeout errors: " + str(self.usb_errors_timeout)
        print "USB Packets received: " + str(self.usb_packets_received)
        print "USB Packets sent: " + str(self.usb_packets_sent)



    def getRadioState(self):

        """
        ========================================================================
        GETRADIOSTATE
        ========================================================================

        ...
        """

        # Ask stick for its RADIO state
        self.sendRequest([5, 0, 0])

        # Get errors
        self.radio_errors_crc = self.response[3]
        self.radio_errors_seq = self.response[4]
        self.radio_errors_nak = self.response[5]
        self.radio_errors_timeout = self.response[6]
        self.radio_packets_received = lib.getNumberPackets(self.response[7:11])
        self.radio_packets_sent = lib.getNumberPackets(self.response[11:15])

        # Print rf state
        print "RADIO Bad CRCs: " + str(self.radio_errors_crc)
        print "RADIO Sequential errors: " + str(self.radio_errors_seq)
        print "RADIO NAKs: " + str(self.radio_errors_nak)
        print "RADIO Timeout errors: " + str(self.radio_errors_timeout)
        print "RADIO Packets received: " + str(self.radio_packets_received)
        print "RADIO Packets sent: " + str(self.radio_packets_sent)



    def getDownloadState(self):

        """
        ========================================================================
        GETDOWNLOADSTATE
        ========================================================================

        ...
        """

        # Ask stick if data requested is ready to be downloaded
        self.sendRequest([3, 0, 0])



    def powerPump(self):

        """
        ========================================================================
        POWERPUMP
        ========================================================================

        ...
        """

        # Power control
        self.pump_packet_parameters = [1, 10]
        self.pump_packet_button = 85
        self.pump_packet_retries = 0
        self.pump_packet_pages = 0
        self.pump_packet_code = 93

        # Send packet to pump
        self.sendPumpPacket()



    def sendPumpPacket(self):

        """
        ========================================================================
        SENDPUMPPACKET
        ========================================================================

        ...
        """

        # Print empty line for easier reading of output in terminal
        print

        # Prepare packet to send to pump
        self.preparePumpPacket()

        print "This packet will be sent over to the pump: " + \
              str(self.pump_packet)

        # Send packet through stick
        self.sendRequest(self.pump_packet)



    def preparePumpPacket(self):

        """
        ========================================================================
        PREPAREPUMPPACKET
        ========================================================================

        ...
        """

        # Initialize packet to send to pump
        self.pump_packet = []

        # Evaluate some parts of packet based on input
        self.pump_packet_head = [1, 0, 167, 1]
        self.pump_packet_serial = [ord(x) for x in
                                   str(self.SERIAL_NUMBER).decode("hex")]
        self.pump_packet_extremities = [(128 |
                                        (len(self.pump_packet_parameters) >> 8
                                        & 256)),
                                        (len(self.pump_packet_parameters)
                                        & 256)]

        # Build said packet
        self.pump_packet.extend(self.pump_packet_head)
        self.pump_packet.extend(self.pump_packet_serial)
        self.pump_packet.extend(self.pump_packet_extremities)
        self.pump_packet.append(self.pump_packet_button)
        self.pump_packet.append(self.pump_packet_retries)
        self.pump_packet.append(self.pump_packet_pages)
        self.pump_packet.append(0)
        self.pump_packet.append(self.pump_packet_code)
        self.pump_packet.append(lib.computeCRC8(self.pump_packet))
        self.pump_packet.extend(self.pump_packet_parameters)
        self.pump_packet.append(lib.computeCRC8(self.pump_packet_parameters))



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

    # Count packets on RADIO transmitter side of stick
    my_stick.getRadioState()

    # Try to speak with pump
    my_stick.powerPump()

    # Get stick RADIO buffer status (waiting to download)
    #for i in range(10):
    #    my_stick.getDownloadState()

    # Stop my stick
    my_stick.stop()

    # End of script
    print
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
