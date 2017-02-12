#! /usr/bin/python



"""
================================================================================
Title:    requester

Author:   David Leclerc

Version:  1.1

Date:     09.02.2017

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that defines a requester object, which is
          responsible for dealing with device requests, that is sending over
          or retrieving data from said devices.

Notes:    ...
================================================================================
"""



# LIBRARIES
import sys
import time
import datetime
import json



# USER LIBRARIES
import lib



class Requester:

    # REQUESTER CONSTANTS
    N_BYTES        = 64
    N_BYTES_FORMAT = 8



    def initialize(self, recipient = None, handle = None):

        """
        ========================================================================
        INITIALIZE
        ========================================================================
        """

        # Verify if requester can be properly initialized
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

        # Initialize a packet dictionary for the requester
        self.packets = {"Normal": [],
                        "Poll": [],
                        "Download": []}



    def define(self, info = None,
                     packet = None,
                     read = False,
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
        self.read = read
        self.sleep = sleep
        self.sleep_reason = sleep_reason
        self.head = head
        self.serial = serial
        self.power = power
        self.attempts = attempts
        self.size = size
        self.code = code
        self.parameters = parameters



    def build(self, sort = "Normal"):

        """
        ========================================================================
        BUILD
        ========================================================================
        """

        # Initialize packet
        packet = []

        # If packet was given in definition of request, just take it
        if self.packet != None:
            packet = self.packet

        # If recipient is stick
        if self.recipient == "Stick":

            pass

        # If recipient is pump
        elif self.recipient == "Pump":

            # Build normal request packet
            if sort == "Normal":
                packet.extend(self.head)
                packet.extend(self.serial)
                packet.append(128 | lib.getByte(len(self.parameters), 1))
                packet.append(lib.getByte(len(self.parameters), 0))
                packet.append(self.power)
                packet.append(self.attempts)
                packet.append(self.size)
                packet.append(0)
                packet.append(self.code)
                packet.append(lib.computeCRC8(packet))
                packet.extend(self.parameters)
                packet.append(lib.computeCRC8(self.parameters))

            # Build poll request packet
            elif sort == "Poll":
                packet = [3, 0, 0]

            # Build download request packet
            elif sort == "Download":
                packet.extend([12, 0])
                packet.append(lib.getByte(self.n_bytes_expected, 1))
                packet.append(lib.getByte(self.n_bytes_expected, 0))
                packet.append(lib.computeCRC8(packet))

        # If recipient is CGM
        elif self.recipient == "CGM":

            pass

        # Update requester's packet dictionary
        self.packets[sort] = packet


    def send(self, sort = "Normal"):

        """
        ========================================================================
        SEND
        ========================================================================
        """

        # Give user info
        print "Sending packet: " + str(self.packets[sort])

        # Send request packet as bytes to device
        self.handle.write(bytearray(self.packets[sort]))

        # Sleep a bit before reading (0.001s)
        time.sleep(0.001)

        # Get response to request
        self.get()



    def get(self):

        """
        ========================================================================
        GET
        ========================================================================
        """

        # Decide on number of bytes to read. If less bytes expected than usual,
        # set to default value. Otherwise, read expected number of bytes.
        if (self.n_bytes_expected < self.N_BYTES):
            n = self.N_BYTES
        else: 
            n = self.n_bytes_expected

        # Give user info
        print "Trying to read " + str(n) + " bytes from device..."

        # Read raw request response from device
        self.raw_response = self.handle.read(n)

        # Vectorize raw response, transform its bytes to decimals, and
        # append it to the response vector
        self.response = [ord(x) for x in self.raw_response]

        # Store number of bytes read from device
        self.n_bytes_received = len(self.response)

        # Give user info
        print "Number of bytes received: " + str(self.n_bytes_received)

        # Format response
        self.format()

        # Print response in readable formats (lines of N bytes)
        self.show(self.N_BYTES_FORMAT)



    def format(self):

        """
        ========================================================================
        FORMAT
        ========================================================================
        """

        # Give user info
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



    def poll(self):

        """
        ========================================================================
        POLL
        ========================================================================
        """

        # Reset number of bytes received
        self.n_bytes_expected = 0

        # Build poll packet
        self.build("Poll")

        # Define polling attempt variable
        n = 0

        # Poll until data is ready to be read
        while self.n_bytes_expected == 0:

            # Update attempt variable
            n += 1

            # First poll of first download attempt: sleep 0.25s
            if (self.n_download_attempts) == 1 & (n == 1):
                time.sleep(0.25)

            # First poll of next download attempts: sleep 0.2s
            elif n == 1:
                time.sleep(0.2)
            # No response to poll? Sleep 0.1s
            else:
                time.sleep(0.1)

            # Keep track of attempts
            print "Polling data: " + str(n) + "/-"

            # Send poll request packet
            self.send("Poll")

            # Get size of response waiting in radio buffer
            self.n_bytes_expected = self.response[7]

        # Give user info
        print "Number of bytes expected: " + str(self.n_bytes_expected)



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Parse data
        head = self.response[0:13]
        body = self.response[13:-1]
        CRC = self.response[-1]

        # Compute expected CRC based on received data
        expected_CRC = lib.computeCRC8(body)

        # Check for incorrect CRC
        if CRC != expected_CRC:

            # Exit
            sys.exit("Error: expected CRC: " + str(expected_CRC) + ", " +
                     "CRC found: " + str(CRC))

        # Check for incorrect number of bytes.
        if self.n_bytes_received != self.n_bytes_expected:

            # There should always be a minimum of 64 bytes received. Sometimes,
            # the expected number of bytes is lower than 64 (e.g. 15), in this
            # case don't exit loop, just go with the 64 that were read.
            if self.n_bytes_expected >= 64:

                # Exit
                sys.exit("Error: expected number of bytes: " + 
                         str(self.n_bytes_expected) + ", " +
                         "number of bytes received: " +
                         str(self.n_bytes_received))

        # Give user info
        print ("Data corresponds to expectations. Storing it...")

	    # Store body of request response
        self.data.extend(body)



    def download(self):

        """
        ========================================================================
        DOWNLOAD
        ========================================================================
        """

        # Give user info
        print "Downloading data from device..."

        # Initialize data vector
        self.data = []

	    # Initialize download attempt variable
        self.n_download_attempts = 0

        # Download whole data on device
        while True:

		    # Update download attempt variable
            self.n_download_attempts += 1

            # Keep track of download process
            print "Downloading data: " + str(self.n_download_attempts) + "/-"

            # Ask if some data was received
            self.poll()

            # Update download packet
            self.build("Download")

		    # Download data
            self.send("Download")

            # Verify if data corresponds to expectations
            self.verify()

	        # Look for end of data (EOD) condition
            if self.response[5] == 128:

                # Give user info
                print "End of data. Exiting download loop."

                break

        # Give user info
        print "Downloaded data after " + str(self.n_download_attempts) + " request(s)."



    def make(self):

        """
        ========================================================================
        MAKE
        ========================================================================
        """

        # Print request info
        print self.info

        # Initialize number of expected bytes
        self.n_bytes_expected = 0

        # Build request packet if not already existent
        self.build()

        # Send request to device
        self.send()

        time.sleep(0.25)

        # If data was requested, download it
        if self.read:

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
