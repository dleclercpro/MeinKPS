#! /usr/bin/python



"""
================================================================================
Title:    requester

Author:   David Leclerc

Version:  1.0

Date:     01.06.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that defines the requester object, which is
          responsible for dealing with device requests, that is sending over
          or retrieving data from said devices.

Notes:    ...
================================================================================
"""



# LIBRARIES
import numpy as np
import sys
import time
import datetime



# USER LIBRARIES
import lib



class Requester:

    # REQUESTER CONSTANTS
    VERBOSE        = True
    BREATHE_TIME   = 0.1
    N_BYTES        = 64



    def prepare(self, recipient = None,
                      handle = None):

        """
        ========================================================================
        PREPARE
        ========================================================================
        """

        # Verify if requester can be properly prepared
        if (recipient == None) | (handle == None):

            # If user forgot to give required input, quit
            sys.exit("Please define a request recipient as well as a handle " +
                     "for the requester.")

        # Give requester the future recipient of its requests, that is the
        # device
        self.recipient = recipient

        # Link requester with the previously generated USB serial handle of said
        # device
        self.handle = handle



    def define(self, info = None,
                     packet = None,
                     n_bytes_expected = 0,
                     sleep = 0,
                     sleep_reason = None,
                     head = None,
                     serial = None,
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

        # Store definition of request
        self.info = info
        self.packet = packet
        self.n_bytes_expected = n_bytes_expected
        self.sleep = sleep
        self.sleep_reason = sleep_reason
        self.head = head
        self.serial = serial
        self.power = power
        self.attempts = attempts
        self.size = size
        self.code = code
        self.parameters = parameters

        # Build packets associated with request
        self.build()



    def build(self):

        """
        ========================================================================
        BUILD
        ========================================================================
        """

        # Initialize a packet dictionary for the requester
        self.packets = {"Normal": None,
                        "Ask": None,
                        "Download": None}

        # Initialize packets
        packet_normal = []
        packet_ask = []
        packet_download = []

        # If packet was passed as a defining argument to the parser, it is the
        # normal packet
        if self.packet != None:

            # Assign input packet to normal request packet
            packet_normal = self.packet

        # If recipient is stick
        if self.recipient == "Stick":

            pass

        # If recipient is pump
        elif self.recipient == "Pump":

            # Build normal request packet
            packet_normal.extend(self.head)
            packet_normal.extend(self.serial)
            packet_normal.append(128 | lib.getByte(len(self.parameters), 1))
            packet_normal.append(lib.getByte(len(self.parameters), 0))
            packet_normal.append(self.power)
            packet_normal.append(self.attempts)
            packet_normal.append(self.size)
            packet_normal.append(0)
            packet_normal.append(self.code)
            packet_normal.append(lib.computeCRC8(packet_normal))
            packet_normal.extend(self.parameters)
            packet_normal.append(lib.computeCRC8(self.parameters))

            # Build ask request packet
            packet_ask = [3, 0, 0]

            # Build download request packet
            packet_download.extend([12, 0])
            packet_download.append(lib.getByte(self.n_bytes_expected, 1))
            packet_download.append(lib.getByte(self.n_bytes_expected, 0))
            packet_download.append(lib.computeCRC8(packet_download))

        # If recipient is CGM
        elif self.recipient == "CGM":

            pass

        # Add packets to requester packet dictionary
        self.packets["Normal"] = packet_normal
        self.packets["Ask"] = packet_ask
        self.packets["Download"] = packet_download



    def send(self, packet_type = None):

        """
        ========================================================================
        SEND
        ========================================================================
        """

        # Give user info
        print "Sending packet: " + str(self.packets[packet_type])

        # Save request time
        self.time = datetime.datetime.now()

        # Send request packet as bytes to device
        self.handle.write(bytearray(self.packets[packet_type]))

        # Get device response to request
        self.get()



    def get(self):

        """
        ========================================================================
        GET
        ========================================================================
        """

        # Read response on device
        self.read()

        # Format response
        self.format()

        # Print response in readable formats (lines of 8 bytes)
        self.show(n_bytes = 8)



    def read(self):

        """
        ========================================================================
        READ
        ========================================================================
        """

        # Initialize response vector
        self.response = []

        # Initialize reading attempt variable
        n = 0

        # Ask for response from device until we get a full one
        while True:

            # Update reading attempt variable
            n += 1

            # Keep track of number of attempts
            if self.VERBOSE:
                print "Reading data from device: " + str(n) + "/-"

            # Read raw request response from device
            self.raw_response = self.handle.read(self.N_BYTES)

            # When device has given all of response, exit loop
            if (len(self.raw_response) == 0) & (sum(self.response) != 0):

                break

            # Otherwise, store current response and ask for the rest
            else:

                # Vectorize raw response and transform its bytes to decimals
                self.raw_response = [ord(x) for x in self.raw_response]

                # Append raw response to final response vector
                self.response.extend(self.raw_response)

                # Give the device a bit of time to breathe before reading again
                time.sleep(self.BREATHE_TIME)

        # Give user info
        if self.VERBOSE:
            print "Read data from device in " + str(n) + " attempt(s)."



    def format(self):

        """
        ========================================================================
        FORMAT
        ========================================================================
        """

        # Give user info
        if self.VERBOSE:
            print "Formatting response..."

        # Format response to padded hexadecimals
        self.response_hex = [lib.padHex(hex(x)) for x in self.response]

        # Format response to readable characters
        self.response_chr = ["." if (x < 32) | (x > 126)
                                 else chr(x)
                                 for x in self.response]



    def show(self, n_bytes = 8):

        """
        ========================================================================
        SHOW
        ========================================================================
        """

        # Define exceeding bytes
        n_exceeding_bytes = len(self.response) % n_bytes

        # Define number of rows to be printed 
        n_rows = len(self.response) / n_bytes + int(n_exceeding_bytes != 0)

        # Give user info
        if self.VERBOSE:

            # Print response
            print "Device response to precedent request: "

            # Print formatted response
            for i in range(n_rows):

                # Define hexadecimal line
                line_hex = " ".join(self.response_hex[i * n_bytes :
                                                     (i + 1) * n_bytes])

                # Define character line
                line_chr = "".join(self.response_chr[i * n_bytes :
                                                    (i + 1) * n_bytes])

                # Define decimal line
                line_dec = "".join(str(self.response[i * n_bytes :
                                                    (i + 1) * n_bytes]))

                # On last line, some extra space may be needed
                if (i == n_rows - 1) & (n_exceeding_bytes != 0):

                    # Define line
                    line = (line_hex +
                           (n_bytes - n_exceeding_bytes) * 5 * " " +
                            " " +
                            line_chr +
                           (n_bytes - n_exceeding_bytes) * " " +
                            " " +
                            line_dec)

                # First lines don't need extra space
                else:

                    # Define line
                    line = line_hex + " " + line_chr + " " + line_dec

                # Print line
                print line



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

        # Ask recipient if data is ready until something is received
        while self.n_bytes_received == 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts
            if self.VERBOSE:
                print "Asking if data was received: " + str(n) + "/-"

            # Send ask request packet
            self.send(packet_type = "Ask")

            # Get size of response waiting in radio buffer
            # FIXME for all devices
            self.n_bytes_received = self.response[7]

        # Give user info
        if self.VERBOSE:
            print "Number of bytes found: " + str(self.n_bytes_received)
            print "Expected number of bytes: " + str(self.n_bytes_expected)



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Verify if received data is as expected. If not, resend request until
        # it is
        while self.n_bytes_received != self.n_bytes_expected:

            # Verify connection with pump, quit if inexistent (this number of
            # bytes means no data was received from pump)
            # FIXME for all devices
            if self.n_bytes_received == 14:
                sys.exit("Pump is either out of range, or will not take "
                         "commands anymore because of low battery level... "
                         ":-(")

            # Give user info
            if self.VERBOSE:
                print "Data does not correspond to expectations."
                print "Resending request..."

            # Resend request packet to device
            self.send(packet_type = "Normal")

            # Ask pump if data is now ready to be read
            self.ask()

        # Give user info
        if self.VERBOSE:
            print "Data corresponds to expectations."



    def download(self):

        """
        ========================================================================
        DOWNLOAD
        ========================================================================
        """
        
        # Ask if some data was received
        self.ask()

        # Verify if data corresponds to expectations
        self.verify()

        # Give user info
        if self.VERBOSE:
            print "Downloading data from device..."

        # Initialize data vector
        self.data = []

        # Initialize download attempt variable
        n = 0

        # Download whole data on device
        while True:

		    # Update download attempt variable
		    n += 1

		    # Download data by sending request packet
		    self.send(packet_type = "Download")

		    # Store device request response
		    self.data.extend(self.response)

		    # End of download condition FIXME ?
		    if sum(self.response[-6:-1]) == 0:

			    break

        # Give user info
        print "Downloaded data in " + str(n) + " attempt(s)."



    def make(self):

        """
        ========================================================================
        MAKE
        ========================================================================
        """

        # Print request info
        print self.info

        # Send request to device
        self.send(packet_type = "Normal")

        # If data was requested, download it
        if self.n_bytes_expected > 0:

            # Download data
            self.download()

        # Wait before next request if needed (give device time to fully execute
        # last request)
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



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
