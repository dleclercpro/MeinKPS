#! /usr/bin/python



"""
================================================================================
Title:    stick

Author:   David Leclerc

Version:  1.2

Date:     01.06.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that allows to retrieve informations from a MiniMed
          insulin pump, using the CareLink USB stick of Medtronic. It is based
          on the PySerial library and is a work of reverse-engineering the USB
          communication protocols of said USB stick.

Notes:    It is important to not interact with the pump while this script
          communicates with it, otherwise some commands could not be actually
          performed!
================================================================================
"""

# TODO
#   - Create report entries for stick infos and state?



# LIBRARIES
import json
import os
import serial
import sys



# USER LIBRARIES
import lib
import reporter
import requester



class Stick:

    # STICK CHARACTERISTICS
    VERBOSE          = True
    VENDOR           = 0x0a21
    PRODUCT          = 0x8001
    SIGNAL_THRESHOLD = 150
    N_BYTES          = 64
    SLEEP            = 0.1
    FREQUENCIES      = {0 : 916.5, 1 : 868.35, 255 : 916.5}



    def start(self):

        """
        ========================================================================
        START
        ========================================================================
        """

        # Add serial port
        os.system("modprobe --quiet --first-time usbserial"
            + " vendor=" + str(self.VENDOR)
            + " product=" + str(self.PRODUCT))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.timeout = 0.1
        self.handle.rtscts = True
        self.handle.dsrdtr = True

        # Verify stick is plugged in        
        try:

            # Open serial port
            self.handle.open()

        except:

            # Give user info
            sys.exit("There seems to be a problem with the stick. " + \
                      "Are you sure it's plugged in?")

        # Give the stick a reporter
        self.reporter = reporter.Reporter()

        # Give the stick a requester
        self.requester = requester.Requester()

        # Prepare requester to send requests to the stick
        self.requester.prepare(recipient = "Stick", handle = self.handle)

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



    def getInfos(self):

        """
        ========================================================================
        GETINFOS
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
                              packet = [4, 0, 0])

        # Make request
        self.requester.make()

        # Extract infos
        self.infos["ACK"] = self.requester.response[0]
        self.infos["Status"] = self.requester.response_chr[1]
        self.infos["Serial"] = "".join(x[2:] for x in
                                       self.requester.response_hex[3:6])
        self.infos["Frequency"] = (str(self.FREQUENCIES[
                                       self.requester.response[8]]) + " MHz")
        self.infos["Description"] = "".join(self.requester.response_chr[9:19])
        self.infos["Version"] = (1.00 * self.requester.response[19:21][0] +
                                 0.01 * self.requester.response[19:21][1])

        # Print infos
        if self.VERBOSE:
            print "Stick infos:"
            print json.dumps(self.infos, indent = 2,
                                         separators = (",", ": "),
                                         sort_keys = True)



    def getSignalStrength(self):

        """
        ========================================================================
        GETSIGNALSTRENGTH
        ========================================================================
        """

        # Define request
        self.requester.define(info = "Reading stick signal strength...",
                              packet = [6, 0, 0])

        # Initialize signal strength
        self.signal = 0

        # Initialize reading signal strength attempt variable
        n = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.SIGNAL_THRESHOLD:

            # Update attempt variable
            n += 1

            # Keep track of attempts reading signal strength
            if self.VERBOSE:
                print "Looking for sufficient signal strength: " + str(n) + "/-"

            # Make request
            self.requester.make()

            # Extract signal strength from response
            self.signal = self.requester.response[3]

            # Print signal strength
            if self.VERBOSE:
                print "Signal strength found: " + str(self.signal)
                print ("Expected minimal signal strength: " +
                       str(self.SIGNAL_THRESHOLD))



    def getState(self):

        """
        ========================================================================
        GETSTATE
        ========================================================================
        """

        # Define state indicators
        state_indicators = {"Errors": {"CRC": None,
                                       "SEQ": None,
                                       "NAK": None,
                                       "Timeout": None},
                            "Packets": {"Received": None,
                                        "Sent": None}}

        # Define state dictionary for USB and RF interfaces
        self.state = {"USB": state_indicators, "RF": state_indicators}

        # Define request
        self.requester.define(info = "Reading stick USB state...",
                              packet = [5, 1, 0])

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

        # Define request
        self.requester.define(info = "Reading stick RF state...",
                              packet = [5, 0, 0])

        # Make request
        self.requester.make()

        # Extract state
        self.state["RF"]["Errors"]["CRC"] = self.requester.response[3]
        self.state["RF"]["Errors"]["SEQ"] = self.requester.response[4]
        self.state["RF"]["Errors"]["NAK"] = self.requester.response[5]
        self.state["RF"]["Errors"]["Timeout"] = self.requester.response[6]
        self.state["RF"]["Packets"]["Received"] = (
            lib.convertBytes(self.requester.response[7:11]))
        self.state["RF"]["Packets"]["Sent"] = (
            lib.convertBytes(self.requester.response[11:15]))

        # Give user info
        if self.VERBOSE:

            # Print current stick state
            print "Stick state:"
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
