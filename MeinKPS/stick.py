#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    stick

    Author:   David Leclerc

    Version:  0.3

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
import os
import json
import datetime
import serial



# USER LIBRARIES
import commands
import errors



class Stick(object):

    # STICK CHARACTERISTICS
    vendor        = 0x0a21
    product       = 0x8001
    serial        = None
    nBytesDefault = 64 # Default number of bytes to read from buffer
    timeout       = 0.1 # Time to read from buffer (s) [0.5]
    emptyTime     = 0.5 # (s)



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Generate serial port handle
        handle = serial.Serial()
        handle.port = "/dev/ttyUSB0"
        handle.rtscts = True
        handle.dsrdtr = True
        handle.timeout = self.timeout

        # Give it to the stick
        self.handle = handle

        # Give the stick a signal
        self.signal = Signal(self)

        # Give the stick a USB interface
        self.USB = USB(self)

        # Give the stick a radio interface
        self.radio = Radio(self)

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

        # Verify if stick is plugged in        
        try:

            # Open serial port
            self.handle.open()

        except:

            # Raise error
            raise errors.NoStick

        # Before anything, make sure buffer is empty
        self.empty()

        # Read infos
        self.infos.read()

        # Read signal strength
        self.signal.read()

        # Read USB state
        self.USB.read()

        # Read radio state
        self.radio.read()



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

        # Try reading for a certain number of attempts, before concluding buffer
        # must really be empty
        while True:

            # Update time
            now = datetime.datetime.now()

            # Empty buffer
            n = len(self.handle.read(self.nBytesDefault))

            # If maximum amount of time reached, exit
            if (now - then).seconds >= self.emptyTime:
                break

        # Give user output
        print "Found " + str(n) + " byte(s) while emptying buffer."



class Signal(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize signal strength
        self.value = 0

        # Give it a minimum strength threshold
        self.threshold = 150

        # Link with its respective command
        self.command = commands.ReadStickSignalStrength(stick, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

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

        # Define a dictionary of state indicators
        self.values = {"Errors": {"CRC": None,
                                  "SEQ": None,
                                  "NAK": None,
                                  "Timeout": None},
                      "Packets": {"Received": None,
                                  "Sent": None}}

        # Initialize command
        self.command = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Print current stick states
        print self.__class__.__name__ + " state:"
        print json.dumps(self.values, indent = 2,
                                      separators = (",", ": "),
                                      sort_keys = True)



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
        self.command = commands.ReadStickUSBState(stick, self)



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
        self.command = commands.ReadStickRadioState(stick, self)



class Infos(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize infos dictionary
        self.values = {"ACK": None,
                       "Status": None,
                       "Frequency": None,
                       "Description": None,
                       "Version": None}

        # Define possible frequencies of operation for the stick (MHz)
        self.frequencies = {0: 916.5,
                            1: 868.35,
                            255: 916.5}

        # Link with its respective command
        self.command = commands.ReadStickInfos(stick, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

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

    # Read stick's infos
    #stick.infos.read()

    # Read stick's signal strength
    #stick.signal.read()

    # Read stick's USB state
    #stick.USB.read()

    # Read stick's radio state
    #stick.radio.read()

    # Stop my stick
    stick.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
