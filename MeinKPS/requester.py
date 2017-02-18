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

# TODO: - recover from 14 bytes expected when downloading?



# LIBRARIES
import sys
import time
import datetime
import json



# USER LIBRARIES
import lib



class Requester:

    # REQUESTER CONSTANTS
    nBytesDefault = 64
    nBytesFormat  = 8
    nPollAttempts = 100 # 50
    readSleep     = 0   # 0.01
    responseSleep = 0   # 0.001
    requestSleep  = 0.1 # 0.25
    pollSleep     = 0.1 # 0.25
    EOD           = 128



    def initialize(self, recipient = None, serial = None, handle = None):

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

        # Read and store encoded version of recipient's serial number
        if serial is not None:
            self.serial = lib.encodeSerialNumber(serial)

        # Link requester with the previously generated USB serial handle of said
        # device
        self.handle = handle

        # Initialize a packet dictionary for the requester
        self.packets = {"Normal": [],
                        "Poll": [],
                        "Download": []}



    def define(self, info = None,
                     packet = None,
                     remote = True,
                     sleep = 0,
                     sleepReason = None,
                     power = 0,
                     attempts = None,
                     size = None,
                     code = None,
                     parameters = []):

        """
        ========================================================================
        DEFINE
        ========================================================================
        """

        # Store definition of request
        self.info = info
        self.packet = packet
        self.remote = remote
        self.sleep = sleep
        self.sleepReason = sleepReason
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
                packet.extend([1, 0, 167, 1])
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
                packet.append(lib.getByte(self.nBytesExpected, 1))
                packet.append(lib.getByte(self.nBytesExpected, 0))
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

        # Give device some time to respond
        time.sleep(self.responseSleep)

        # Get response to request
        self.get()



    def get(self):

        """
        ========================================================================
        GET
        ========================================================================
        """

        # Decide on number of bytes to read. If less bytes expected than usual,
        # set to default value (64). Otherwise, read expected number of bytes.
        if self.nBytesExpected == 0:
            nBytes = self.nBytesDefault
        else: 
            nBytes = self.nBytesExpected

        # Give user info
        print "Trying to read " + str(nBytes) + " bytes from device..."

        # Initialize reading attempt variable
        n = 0

        # Retry reading if there was no response
        while True:

            # Update reading attempt variable
            n += 1

            # Give user info
            print "Reading attempt: " + str(n) + "/-"

            # Read raw request response from device
            self.rawResponse = self.handle.read(nBytes)

            # Exit condition
            if len(self.rawResponse) > 0:

                break

            else:

                # Give device a break before reading again
                time.sleep(self.readSleep)

        # Give user info
        print "Read data in " + str(n) + " attempt(s)."

        # Vectorize raw response, transform its bytes to decimals, and
        # append it to the response vector
        self.response = [ord(x) for x in self.rawResponse]

        # Store number of bytes read from device
        self.nBytesReceived = len(self.response)

        # Give user info
        print "Number of bytes received: " + str(self.nBytesReceived)

        # Format response
        self.format()

        # Print response in readable formats (lines of N bytes)
        self.show(self.nBytesFormat)



    def format(self):

        """
        ========================================================================
        FORMAT
        ========================================================================
        """

        # Give user info
        print "Formatting response..."

        # Format response to padded hexadecimals
        self.responseHex = [lib.padHex(hex(x)) for x in self.response]

        # Format response to readable characters
        self.responseChr = ["." if (x < 32) | (x > 126)
                                 else chr(x)
                                 for x in self.response]



    def show(self, n = 8):

        """
        ========================================================================
        SHOW
        ========================================================================
        """

        # Compute number of exceeding bytes
        nBytesExceeding = len(self.response) % n

        # Define number of rows to be printed 
        nRows = len(self.response) / n + int(nBytesExceeding != 0)

        # Print response
        print "Device response to precedent request: "

        # Print formatted response
        for i in range(nRows):

            # Define hexadecimal line
            lineHex = " ".join(self.responseHex[i * n : (i + 1) * n])

            # Define character line
            lineChr = "".join(self.responseChr[i * n : (i + 1) * n])

            # Define decimal line
            lineDec = "".join(str(self.response[i * n : (i + 1) * n]))

            # On last line, some extra space may be needed
            if (i == nRows - 1) & (nBytesExceeding != 0):

                # Define line
                line = (lineHex + (n - nBytesExceeding) * 5 * " " + " " +
                        lineChr + (n - nBytesExceeding) * " " + " " +
                        lineDec)

            # First lines don't need extra space
            else:

                # Define line
                line = lineHex + " " + lineChr + " " + lineDec

            # Print line
            print line



    def poll(self):

        """
        ========================================================================
        POLL
        ========================================================================
        """

        # Reset number of bytes expected
        self.nBytesExpected = 0

        # Build poll packet
        self.build("Poll")

        # Define polling attempt variable
        n = 0

        # Poll until data is ready to be read
        while self.nBytesExpected == 0:

            # Update attempt variable
            n += 1

            # Poll sleep
            time.sleep(self.pollSleep)

            # Keep track of attempts
            print "Polling data: " + str(n) + "/" + str(self.nPollAttempts)

            # Send poll request packet
            self.send("Poll")

            # Get size of response waiting in radio buffer
            self.nBytesExpected = self.response[7]

            # Exit after a maximal number of poll attempts
            # FIXME
            if n == self.nPollAttempts:

                # Give user info
                sys.exit("Error: maximal number of polling attempts (" +
                         str(self.nPollAttempts) + ") " + "reached. Exiting...")

        # Give user info
        print "Polled data in " + str(n) + " attempt(s)."
        print "Number of bytes expected: " + str(self.nBytesExpected)



    def verify(self):

        """
        ========================================================================
        VERIFY
        ========================================================================
        """

        # Check for incorrect number of bytes
        if self.nBytesExpected == 14:

            # Exit
            sys.exit("Error: a problem occured while communicating with the " +
                     "pump (number of bytes expected: 14). Exiting...")

        elif self.nBytesReceived != self.nBytesExpected:

            # Exit
            sys.exit("Error: expected " + str(self.nBytesExpected) +
                     " bytes, but received " + str(self.nBytesReceived) +
                     " instead. Exiting...")

        # Parse data
        head = self.response[0:13]
        body = self.response[13:-1]
        CRC = self.response[-1]

        # Compute expected CRC based on received data
        expectedCRC = lib.computeCRC8(body)

        # Check for incorrect CRC
        if CRC != expectedCRC:

            # Give user info
            print ("Error: expected CRC: " + str(expectedCRC) + ", " +
                   "CRC found: " + str(CRC))

            # Exit, ignore faulty data!
            return

        # Give user info
        print ("Data passed integrity checks. Storing it...")

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
        n = 0

        # Download whole data on device
        while True:

		    # Update download attempt variable
            n += 1

            # Keep track of download process
            print "Downloading data: " + str(n) + "/-"

            # Ask if some data was received
            self.poll()

            # Update download packet
            self.build("Download")

		    # Download data
            self.send("Download")

            # Verify if data corresponds to expectations
            self.verify()

	        # Look for end of data (EOD) condition
            if self.response[5] >= self.EOD:

                # Give user info
                print "End of data. Exiting download loop."

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

        # Initialize number of expected bytes
        self.nBytesExpected = 0

        # Build request packet if not already existent
        self.build()

        # Send request to device
        self.send()

        # Give device some time before starting to poll
        time.sleep(self.requestSleep)

        # If remote data was requested, download it
        if self.remote:

            # Download data
            self.download()

        # Give enough time for last request to be executed
        if self.sleep > 0:

            # Explain why sleeping is necessary
            print self.sleepReason

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
