#! /usr/bin/python



"""
================================================================================
Title:    pump
Author:   David Leclerc
Version:  0.1
Date:     30.05.2016
License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)
Overview: This is a script that defines the requester object, which is
          responsible for dealing with device requests, that is sending over
          or retrieving data from said devices.
Notes:    ...
================================================================================
"""

# TODO
#   - "Prepare requester to send request to device X..."



# LIBRARIES
import os
import sys
import time
import numpy as np



# USER LIBRARIES
import lib
import stick



class Requester:

    # REQUESTER CONSTANTS
    TALKATIVE = True



    def link(self, recipient, handle):

        """
        ========================================================================
        LINK
        ========================================================================
        """

        # Give requester the future recipient of its requests, that is the
        # device
        self.recipient = recipient

        # Link requester with the previously generated USB serial handle of said
        # device
        self.handle = handle



    def define(self, info = None,
                     sleep = None,
                     sleep_reason = None,
                     n_bytes_expected = None,
                     power = None,
                     attempts = None,
                     size = None,
                     code = None,
                     parameters = None):

        """
        ========================================================================
        DEFINE
        ========================================================================
        """

        # If recipient is stick
        if self.recipient == "Stick":

            # Store definition of request
            pass

        # If recipient is buffer
        elif self.recipient == "Buffer":

            # Store definition of request
            pass

        # If recipient is pump
        elif self.recipient == "Pump":

            # Store definition of request
            self.info = info
            self.sleep = sleep
            self.sleep_reason = sleep_reason
            self.n_bytes_expected = n_bytes_expected
            self.power = power
            self.attempts = attempts
            self.size = size
            self.code = code
            self.parameters = parameters

        # If recipient is CGM
        elif self.recipient == "CGM":

            # Store definition of request
            pass



    def build(self):

        """
        ========================================================================
        BUILD
        ========================================================================
        """

        # If recipient is stick
        if recipient == "Stick":

            # Build request packet
            pass

        # If recipient is buffer
        elif recipient == "Buffer":

            # Build request packet
            self.packet = []
            self.packet.extend([12, 0])
            self.packet.append(lib.getByte(self.n_bytes_expected, 1))
            self.packet.append(lib.getByte(self.n_bytes_expected, 0))
            self.packet.append(lib.computeCRC8(self.packet))

        # If recipient is pump
        elif recipient == "Pump":

            # Build request packet
            self.packet = []
            self.packet.extend(self.HEAD)
            self.packet.extend(self.ENCODED_SERIAL_NUMBER)
            self.packet.append(128 | lib.getByte(len(self.parameters), 1))
            self.packet.append(lib.getByte(len(self.parameters), 0))
            self.packet.append(self.power)
            self.packet.append(self.attempts)
            self.packet.append(self.size)
            self.packet.append(0)
            self.packet.append(self.code)
            self.packet.append(lib.computeCRC8(self.packet))
            self.packet.extend(self.parameters)
            self.packet.append(lib.computeCRC8(self.parameters))

        # If recipient is CGM
        elif recipient == "CGM":

            # Build request packet
            pass



    def send(self, packet):

        """
        ========================================================================
        SEND
        ========================================================================
        """

        # Store packet
        self.packet = packet

        # Transform request packet to bytes
        self.packet = bytearray(self.packet)

        # Send request packet to device
        self.handle.write(self.packet)



    def ask(self):

        """
        ========================================================================
        ASK
        ========================================================================
        """

        # Reset number of bytes received
        self.n_bytes_received = 0

        # Define asking attempt variable
        n = 0

        # Ask recipient if data is ready
        while self.n_bytes_received == 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts
            if self.TALKATIVE:
                print "Asking if data was received: " + str(n) + "/-"

            # If recipient is stick
            if self.recipient == "Stick":

                pass

            # If recipient is buffer
            elif self.recipient == "Buffer":

                # Send request
                self.send([3, 0, 0])

                # Get size of response waiting in radio buffer
                self.n_bytes_received = self.response[7] # FIXME

            # If recipient is pump
            elif self.recipient == "Pump":

                pass

            # If recipient is CGM
            elif self.recipient == "CGM":

                pass

        # Give user info
        if self.TALKATIVE:
            print "Number of bytes found: " + str(self.n_bytes_received)
            print "Expected number of bytes: " + str(self.n_bytes_expected)



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Verify if received data is as expected. If not, resend pump request
        # until it is
        while self.n_bytes_received != self.n_bytes_expected:

            # Verify connection with pump, quit if inexistent (this number of
            # bytes means no data was received from pump)
            if self.n_bytes_received == 14:
                sys.exit("Pump is either out of range, or will not take "
                         "commands anymore because of low battery level... :-(")

            # Give user info
            if self.TALKATIVE:
                print "Data does not correspond to expectations."
                print "Resending pump request..."

            # Resend pump request to stick
            self.send()

            # Ask pump if data is now ready to be read
            self.ask()

        # Give user info
        if self.TALKATIVE:
            print "Data corresponds to expectations."



    def retrieve(self):

        """
        ========================================================================
        RETRIEVE
        ========================================================================
        """
        
        # Ask if some pump data was received
        self.ask()

        # Verify if pump data corresponds to expectations
        self.verify()

        # Give user info
        if self.TALKATIVE:
            print "Retrieving pump data on stick..."

        # Initialize packet to retrieve pump data on stick
        self.packet = []

        # Build said packet
        self.packet.extend([12,
                            0,
                            lib.getByte(self.n_bytes_expected, 1),
                            lib.getByte(self.n_bytes_expected, 0)])
        self.packet.append(lib.computeCRC8(self.packet))

        # Initialize pump response vectors for all formats
        self.response = []
        self.response_hex = []
        self.response_str = []

        # Download pump data on stick until the buffer has been emptied
        # FIXME Do not hardcode!
        for i in range(3):

            # Download pump data by sending packet to stick
            self.send()

            # Fill the pump response vectors with the new response
            self.response.append(self.stick.response)
            self.response_hex.append(self.stick.response_hex)
            self.response_str.append(self.stick.response_str)

        # If user is looking to download pump history, there will be more
        #if self.n_bytes_expected == 206:

            #for i in range(2):

                # Resend download request
                #self.send()

                # Store pump data in all formats
                #self.response = self.stick.response
                #self.response_hex = self.stick.response_hex
                #self.response_str = self.stick.response_str



    def make(self):

        """
        ========================================================================
        MAKE
        ========================================================================
        """

        # Print pump request info
        print self.info

        # Build request associated packet
        self.build()

        # Send said packet over stick to pump
        self.send()

        # If data was requested, retrieve it
        if self.n_bytes_expected > 0:

            # Retrieve pump data
            self.retrieve()

        # Give pump time to execute request if needed
        if self.sleep > 0:

            # Give sleep reason
            print self.sleep_reason

            # Sleep
            time.sleep(self.sleep)



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    # Instanciate a requester for me
    requester = Requester()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
