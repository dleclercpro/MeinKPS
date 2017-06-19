#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    stick

    Author:   David Leclerc

    Version:  0.4

    Date:     01.06.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that allows to retrieve informations from a
              MiniMed insulin pump, using the CareLink USB stick of Medtronic.
              It is based on the PySerial library and is a work of
              reverse-engineering the USB communication protocols of said USB
              stick.

    Notes:    It is important to not interact with the pump while this script
              communicates with it, otherwise some commands could not be
              actually performed!

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO
#   - Monitor ACK, CRC, SEQ, and NAK bytes



# LIBRARIES
import os
import datetime
import serial



# USER LIBRARIES
import lib
import errors
import commands



class Stick(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define stick characteristics
        self.vendor = 0x0a21
        self.product = 0x8001

        # Define times
        self.timeout = 0.1
        self.emptyTime = 0.5

        # Give the stick a handle
        self.handle = serial.Serial()

        # Give the stick infos
        self.infos = Infos(self)

        # Give the stick a signal
        self.signal = Signal(self)

        # Give the stick a USB and a radio interface
        self.interfaces = {"USB": USB(self),
                           "Radio": Radio(self)}



    def connect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        try:

            # Define serial port
            os.system("sudo modprobe --quiet --first-time usbserial " +
                      "vendor=" + str(self.vendor) + " " +
                      "product=" + str(self.product))

            # Define handle
            self.handle.port = "/dev/ttyUSB0"
            self.handle.rtscts = True
            self.handle.dsrdtr = True
            self.handle.timeout = self.timeout

            # Open handle
            self.handle.open()

        except:

            # Raise error
            raise errors.NoStick



    def disconnect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DISCONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("modprobe --quiet --remove usbserial")



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Before anything, make sure buffer is empty
        #self.empty()

        # Read infos
        self.infos.read()

        # Read signal strength
        self.signal.read()

        # Read USB state
        self.interfaces["USB"].read()

        # Read radio state
        self.interfaces["Radio"].read()



    def write(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Write bytes
        self.handle.write(bytearray(bytes))



    def read(self, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read raw bytes
        rawResponse = self.handle.read(n)

        # Convert raw bytes
        response = [ord(x) for x in rawResponse]

        # Return response
        return response



    def empty(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EMPTY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read initial time
        then = datetime.datetime.now()

        # Give user info
        print "Emptying buffer for " + str(self.emptyTime) + "s..."

        # Initialize byte count
        n = 0

        # Try reading for a certain number of attempts, before concluding buffer
        # must really be empty
        while True:

            # Update time
            now = datetime.datetime.now()

            # Empty buffer
            n += len(self.handle.read(64))

            # If maximum amount of time reached, exit
            if (now - then).seconds >= self.emptyTime:
                break

        # Give user output
        print "Found " + str(n) + " byte(s) while emptying buffer."



class Infos(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize infos
        self.values = None

        # Link with its respective command
        self.command = commands.ReadStickInfos(stick)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.values = self.command.response

        # Give user info
        print "Stick infos:"

        # Print infos
        lib.printJSON(self.values)



class Signal(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize signal strength
        self.value = 0

        # Define minimum strength threshold
        self.threshold = 150

        # Link with its respective command
        self.command = commands.ReadStickSignalStrength(stick)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.value < self.threshold:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            print "Looking for sufficient signal strength: " + str(n) + "/-"

            # Do command
            self.command.do()

            # Get command response
            self.value = self.command.response

            # Print signal strength
            print "Signal strength found: " + str(self.value)
            print "Expected minimal signal strength: " + str(self.threshold)



class Interface(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize states
        self.values = None

        # Initialize command
        self.command = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Do command
        self.command.do()

        # Get command response
        self.values = self.command.response

        # Give user info
        print self.__class__.__name__ + " state:"

        # Print current stick states
        lib.printJSON(self.values)



class USB(Interface):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize interface
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadStickUSBState(stick)



class Radio(Interface):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize interface
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadStickRadioState(stick)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a stick for me
    stick = Stick()

    # Connect to stick
    stick.connect()

    # Start stick
    stick.start()

    # Disconnect from stick
    stick.disconnect()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
