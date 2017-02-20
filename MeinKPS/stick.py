#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    stick

    Author:   David Leclerc

    Version:  1.2

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
#   - Create report entries for stick infos and state?
#   - Monitor ACK, CRC, SEQ, and NAK bytes?



# LIBRARIES
import json
import os
import serial
import sys
import time
import datetime



# USER LIBRARIES
import lib
import reporter
import requester
import decoder



class Stick:

    # STICK CHARACTERISTICS
    vendor      = 0x0a21
    product     = 0x8001
    timeout     = 0.1 # (s) / 0.5
    frequencies = {0: 916.5, 1: 868.35, 255: 916.5} # MHz



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the stick a reporter
        self.reporter = reporter.Reporter()

        # Give the stick a requester
        self.requester = requester.Requester()

        # Give the stick a decoder
        self.decoder = decoder.Decoder(self)

        # Give the stick a buffer
        self.buffer = Buffer(self)

        # Give the stick a signal
        self.signal = Signal(self)

        # Give the stick interfaces
        self.interfaces = Interfaces(self)

        # Give the stick infos
        self.infos = Infos(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Add serial port
        os.system("modprobe --quiet --first-time usbserial"
            + " vendor=" + str(self.vendor)
            + " product=" + str(self.product))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.rtscts = True
        self.handle.dsrdtr = True
        self.handle.timeout = self.timeout

        # Verify stick is plugged in        
        try:

            # Open serial port
            self.handle.open()

        except:

            # Give user info
            sys.exit("There seems to be a problem with the stick. " +
                      "Are you sure it's plugged in?")

        # Before anything, make sure the stick's buffer is empty
        self.buffer.empty()

        # Initialize requester to speak with stick
        self.requester.start(recipient = "Stick", handle = self.handle)

        # Read stick infos
        self.infos.read()

        # Read signal strength
        self.signal.read()

        # Read state of stick's interfaces
        self.interfaces.USB.state.read()
        self.interfaces.radio.state.read()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("modprobe --quiet --remove usbserial")



def link(recipient, stick):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        LINK
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Link recipient with stick
    recipient.stick = stick

    # Link recipient with reporter
    recipient.reporter = stick.reporter

    # Link recipient with requester
    recipient.requester = stick.requester

    # Link recipient with decoder
    recipient.decoder = stick.decoder



class Buffer:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with stick
        link(self, stick)

        # Give buffer a default number of bytes to read
        self.nBytes = 64

        # Define a time length for emptying stick's buffer
        self.duration = 0.5 # (s)



    def empty(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EMPTY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: This seems to work, contrary to the serial object's methods
              flushInput() and flushOutput()...
        """

        # Read initial time
        then = datetime.datetime.now()

        # Initialize number of bytes read while emptying buffer
        n = 0

        # Give user info
        print "Emptying buffer for " + str(self.duration) + "s..."

        # Try reading for a certain number of attempts, before concluding buffer
        # must really be empty
        while True:

            # Update time
            now = datetime.datetime.now()

            # Empty buffer
            rawResponse = self.stick.handle.read(self.nBytes)

            # Update number of bytes read
            n += len(rawResponse)

            # If maximum amount of time reached, exit
            if (now - then).seconds >= self.duration:
                break

        # Give user output
        print "Found " + str(n) + " byte(s) while emptying buffer."



class Signal:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with stick
        link(self, stick)

        # Give it a minimum strength threshold
        self.threshold = 150

        # Initialize signal strength
        self.value = 0



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        info = "Reading stick signal strength..."

        # Define request
        self.requester.define(info = info,
                              packet = [6, 0, 0],
                              remote = False)

        # Update decoder's target
        self.decoder.target = self

        # Initialize reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.value < self.threshold:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            print "Looking for sufficient signal strength: " + str(n) + "/-"

            # Remake request
            self.requester.make()

            # Decode stick's response
            self.decoder.decode("readSignalStrength")

            # Print signal strength
            print "Signal strength found: " + str(self.value)
            print "Expected minimal signal strength: " + str(self.threshold)



class Interfaces:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give interfaces their USB and radio instances
        self.USB = USB(stick)
        self.radio = Radio(stick)



class USB:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give USB interface a state
        self.state = State(stick, "USB")



class Radio:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give radio interface a state
        self.state = State(stick, "Radio")



class State:

    def __init__(self, stick, interface):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with stick
        link(self, stick)

        # Read interface
        self.interface = interface

        # Define a dictionary of state indicators
        self.values = {"Errors": {"CRC": None,
                                  "SEQ": None,
                                  "NAK": None,
                                  "Timeout": None},
                       "Packets": {"Received": None,
                                   "Sent": None}}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Update decoder's target
        self.decoder.target = self

        # Read USB interface
        if self.interface == "USB":

            # Define request info
            info = "Reading stick's USB state..."

            # Define request
            self.requester.define(info = info,
                                  packet = [5, 1, 0],
                                  remote = False)

            # Make request
            self.requester.make()

            # Decode stick's response
            self.decoder.decode("readUSBState")

        # Read USB interface
        elif self.interface == "Radio":

            # Define request info
            info = "Reading stick's radio state..."

            # Define request
            self.requester.define(info = info,
                                  packet = [5, 0, 0],
                                  remote = False)

            # Make request
            self.requester.make()

            # Decode stick's response
            self.decoder.decode("readRadioState")

        # Print current stick states
        print self.interface + " state:"
        print json.dumps(self.values, indent = 2,
                                      separators = (",", ": "),
                                      sort_keys = True)



class Infos:

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link with stick
        link(self, stick)

        # Initialize infos dictionary
        self.values = {"ACK": None,
                       "Status": None,
                       "Frequency": None,
                       "Description": None,
                       "Version": None}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        info = "Reading stick infos..."

        # Define request
        self.requester.define(info = info,
                              packet = [4, 0, 0],
                              remote = False)

        # Make request
        self.requester.make()

        # Update decoder's target
        self.decoder.target = self

        # Decode stick's response
        self.decoder.decode("readInfos")

        # Print infos
        print "Stick infos:"
        print json.dumps(self.values, indent = 2,
                                      separators = (",", ": "),
                                      sort_keys = True)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a stick for me
    stick = Stick()

    # Start my stick
    stick.start()

    # Stop my stick
    stick.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
