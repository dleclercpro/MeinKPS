#! /usr/bin/python

"""
================================================================================

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

================================================================================
"""

# TODO
#   - Create report entries for stick infos and state?



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



class Stick:

    # STICK CHARACTERISTICS
    vendor          = 0x0a21
    product         = 0x8001
    nBytesDefault   = 64
    signalThreshold = 150
    timeout         = 0.1 # (s) / 0.5
    emptySleep      = 1   # (s)
    frequencies     = {0: 916.5, 1: 868.35, 255: 916.5} # MHz



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Add serial port
        os.system("modprobe --quiet --first-time usbserial"
            + " vendor=" + str(self.vendor)
            + " product=" + str(self.product))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.timeout = self.timeout
        self.handle.rtscts = True
        self.handle.dsrdtr = True

        # Verify stick is plugged in        
        try:

            # Open serial port
            self.handle.open()

        except:

            # Give user info
            sys.exit("There seems to be a problem with the stick. " +
                      "Are you sure it's plugged in?")

        # Before anything, make sure the stick's buffer is empty
        self.empty()

        # Give the stick a reporter
        self.reporter = reporter.Reporter()

        # Give the stick a requester
        self.requester = requester.Requester()

        # Initialize requester to speak with stick
        self.requester.initialize(recipient = "Stick", handle = self.handle)

        # Define state indicators
        stateIndicators = {"Errors": {"CRC": None, "SEQ": None, "NAK": None,
                                      "Timeout": None},
                           "Packets": {"Received": None, "Sent": None}}

        # Initialize a state dictionary for the stick's USB and radio interfaces
        self.state = {"USB": stateIndicators, "Radio": stateIndicators}

        # Ask for stick infos
        self.readInfos()

        # Ask for signal strength
        self.readSignalStrength()

        # Get state of stick
        self.readStates()



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



    def empty(self):

        """
        ========================================================================
        EMPTY
        ========================================================================

        Note: This seems to work, contrary to the serial object's methods
              flushInput() and flushOutput()...
        """

        # Read initial time
        then = datetime.datetime.now()

        # Initialize number of bytes read while emptying buffer
        n = 0

        # Give user info
        print "Emptying buffer for " + str(self.emptySleep) + "s..."

        # Try reading for a certain number of attempts, before concluding buffer
        # must really be empty
        while True:

            # Update time
            now = datetime.datetime.now()

            # Empty buffer
            self.rawResponse = self.handle.read(self.nBytesDefault)

            # Update number of bytes read
            n += len(self.rawResponse)

            # If maximum amount of time reached, exit
            if (now - then).seconds >= self.emptySleep:

                break

        # Give user output
        print "Found " + str(n) + " byte(s) while emptying buffer."



    def readInfos(self):

        """
        ========================================================================
        READINFOS
        ========================================================================
        """

        # Define stick infos dictionary
        self.infos = {"ACK": None,
                      "Status": None,
                      "Serial": None,
                      "Frequency": None,
                      "Description": None,
                      "Version": None}

        # Define request
        self.requester.define(info = "Reading stick infos...",
                              packet = [4, 0, 0],
                              remote = False)

        # Make request
        self.requester.make()

        # Extract infos
        self.infos["ACK"] = self.requester.response[0]
        self.infos["Status"] = self.requester.responseChr[1]
        self.infos["Serial"] = "".join(x[2:] for x in
                               self.requester.responseHex[3:6])
        self.infos["Frequency"] = (str(self.frequencies[
                                   self.requester.response[8]]) + " MHz")
        self.infos["Description"] = "".join(self.requester.responseChr[9:19])
        self.infos["Version"] = (1.00 * self.requester.response[19:21][0] +
                                 0.01 * self.requester.response[19:21][1])

        # Print infos
        print "Stick infos:"
        print json.dumps(self.infos, indent = 2,
                                     separators = (",", ": "),
                                     sort_keys = True)



    def readSignalStrength(self):

        """
        ========================================================================
        READSIGNALSTRENGTH
        ========================================================================
        """

        # Define request
        self.requester.define(info = "Reading stick signal strength...",
                              packet = [6, 0, 0],
                              remote = False)

        # Initialize signal strength
        self.signal = 0

        # Initialize reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.signalThreshold:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            print "Looking for sufficient signal strength: " + str(n) + "/-"

            # Make request
            self.requester.make()

            # Extract signal strength from response
            self.signal = self.requester.response[3]

            # Print signal strength
            print "Signal strength found: " + str(self.signal)
            print ("Expected minimal signal strength: " +
                   str(self.signalThreshold))



    def readUSBState(self):

        """
        ========================================================================
        READUSBSTATE
        ========================================================================
        """

        # Define request
        self.requester.define(info = "Reading stick USB state...",
                              packet = [5, 1, 0],
                              remote = False)

        # Make request
        self.requester.make()

        # Extract state
        self.state["USB"]["Errors"]["CRC"] = self.requester.response[3]
        self.state["USB"]["Errors"]["SEQ"] = self.requester.response[4]
        self.state["USB"]["Errors"]["NAK"] = self.requester.response[5]
        self.state["USB"]["Errors"]["Timeout"] = self.requester.response[6]
        self.state["USB"]["Packets"]["Received"] = (
            lib.convertBytes(self.requester.response[7:11]))
        self.state["USB"]["Packets"]["Sent"] = (
            lib.convertBytes(self.requester.response[11:15]))



    def readRadioState(self):

        """
        ========================================================================
        READRADIOSTATE
        ========================================================================
        """

        # Define request
        self.requester.define(info = "Reading stick radio state...",
                              packet = [5, 0, 0],
                              remote = False)

        # Make request
        self.requester.make()

        # Extract state
        self.state["Radio"]["Errors"]["CRC"] = self.requester.response[3]
        self.state["Radio"]["Errors"]["SEQ"] = self.requester.response[4]
        self.state["Radio"]["Errors"]["NAK"] = self.requester.response[5]
        self.state["Radio"]["Errors"]["Timeout"] = self.requester.response[6]
        self.state["Radio"]["Packets"]["Received"] = (
            lib.convertBytes(self.requester.response[7:11]))
        self.state["Radio"]["Packets"]["Sent"] = (
            lib.convertBytes(self.requester.response[11:15]))



    def readStates(self):

        """
        ========================================================================
        READSTATES
        ========================================================================
        """

        # Read USB and radio states
        self.readUSBState()
        self.readRadioState()

        # Print current stick states
        print "Stick states:"
        print json.dumps(self.state, indent = 2,
                                     separators = (",", ": "),
                                     sort_keys = True)



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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
