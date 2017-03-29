#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    commands

    Author:   David Leclerc

    Version:  0.2

    Date:     21.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a collection of commands available for the Carelink stick
              as well as the Medtronic MiniMed pumps.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import time



# USER LIBRARIES
import lib
import errors
import packets



class Command(object):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize info
        self.info = None

        # Initialize bytes
        self.bytes = None

        # Initialize decoded response
        self.response = None

        # Define byte counts
        self.nBytesDefault = 64
        self.nBytesExpected = 0
        self.nBytesReceived = 0

        # Define sleep times
        self.writeSleep = 0
        self.readSleep = 0

        # Link with stick
        self.stick = stick



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Sending packet: " + str(self.packet.bytes)

        # Send request packet as bytes to device
        self.stick.write(self.packet.bytes)

        # Give device some time to respond
        time.sleep(self.writeSleep)

        # Read response
        self.receive()



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decide on number of bytes to read. If less bytes expected than usual,
        # set to default value. Otherwise, read expected number of bytes.
        nBytes = self.nBytesExpected or self.nBytesDefault

        # Give user info
        print "Trying to read " + str(nBytes) + " bytes from device..."

        # Initialize reading attempt variable
        n = 0

        # Read until there is a response
        while True:

            # Update reading attempt variable
            n += 1

            print "Reading attempt: " + str(n) + "/-"

            # Read raw request response from device
            self.bytes = self.stick.read(nBytes)

            # Exit condition
            if len(self.bytes) > 0:

                break

            else:

                # Give device a break before reading again
                time.sleep(self.readSleep)

        # Give user info
        print "Read data in " + str(n) + " attempt(s)."

        # Store number of bytes read from device
        self.nBytesReceived = len(self.bytes)

        # Give user info
        print "Number of bytes received: " + str(self.nBytesReceived)

        # Print response in readable formats
        self.show()



    def show(self, n = 8):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute number of exceeding bytes
        nBytesExceeding = self.nBytesReceived % n

        # Define number of rows to be printed 
        nRows = self.nBytesReceived / n + int(nBytesExceeding != 0)

        # Format response
        responseHex = lib.hexify(self.bytes)
        responseChr = lib.charify(self.bytes)

        # Print response
        print "Device response to precedent request: "

        # Print formatted response
        for i in range(nRows):

            # Define line in all formats
            lineHex = " ".join(responseHex[i * n : (i + 1) * n])
            lineChr = "".join(responseChr[i * n : (i + 1) * n])
            lineDec = "".join(str(self.bytes[i * n : (i + 1) * n]))

            # On last line, some extra space may be needed
            if (i == nRows - 1) and (nBytesExceeding != 0):

                # Define line
                line = (lineHex + (n - nBytesExceeding) * 5 * " " + " " +
                        lineChr + (n - nBytesExceeding) * " " + " " +
                        lineDec)

            # First lines don't need extra space
            else:

                # Define line
                line = lineHex + " " + lineChr + " " + lineDec

            # Show response
            print line



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Build packet
        self.packet.build()

        # Give user info about command
        print self.info

        # Send command
        self.send()

        # Decode response
        self.decode()



class StickCommand(Command):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(StickCommand, self).__init__(stick)

        # Give the command a packet
        self.packet = packets.StickPacket(self)



class PumpCommand(Command):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PumpCommand, self).__init__(stick)

        # Initialize downloaded data
        self.data = None

        # Define end of download byte
        self.EOD = 128

        # Define max number of poll attempts
        self.nPollAttempts = 100

        # Define sleep times
        self.pollSleep = 0.1
        self.commandSleep = 0.1

        # Give the command a packet
        self.packet = packets.PumpPacket(self)



    def poll(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            POLL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset number of bytes expected
        self.nBytesExpected = 0

        # Update packet type
        self.packet.type = "Poll"

        # Build poll packet
        self.packet.build()

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

            # Send packet
            self.send()

            # Get size of response waiting in radio buffer
            self.nBytesExpected = self.bytes[7]

            # Exit after a maximal number of poll attempts
            if n == self.nPollAttempts:

                # Raise error
                raise errors.MaxPoll(n)

        # Give user info
        print "Polled data in " + str(n) + " attempt(s)."
        print "Number of bytes expected: " + str(self.nBytesExpected)



    def download(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOWNLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Downloading data from pump..."

        # Reset data vector
        self.data = []

	    # Initialize download attempt variable
        n = 0

        # Download whole data on device
        while True:

		    # Update download attempt variable
            n += 1

            # Keep track of download process
            print "Downloading data: " + str(n) + "/-"

            # Poll data
            self.poll()

            # Update packet type
            self.packet.type = "Download"

            # Build download packet
            self.packet.build()

		    # Send packet
            self.send()

            # Verify and store downloaded data if it corresponds to expectations
            self.verify()

	        # Look for end of data (EOD) condition
            if self.bytes[5] >= self.EOD:

                # Give user info
                print "End of data. Exiting download loop."

                break

        # Give user info
        print "Downloaded data in " + str(n) + " attempt(s)."



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Check for incorrect number of bytes
        if self.nBytesExpected == 14:

            # Raise error
            raise errors.FatalNBytes(self.nBytesExpected)

        elif self.nBytesReceived != self.nBytesExpected:

            # Raise error
            raise errors.MismatchNBytes([self.nBytesExpected,
                                         self.nBytesReceived])

        # Parse response
        head = self.bytes[0:13]
        body = self.bytes[13:-1]
        CRC = self.bytes[-1]

        # Compute CRC based on received data
        computedCRC = lib.computeCRC8(body)

        # Check for CRC mismatch
        if computedCRC != CRC:

            # Give user info
            print ("Error: computed CRC (" + str(computedCRC) + ") does " +
                   "not match received CRC (" + str(CRC) + "). Ignoring...")

            # Exit: ignore faulty data!
            return

        # Give user info
        print ("Data passed integrity checks. Storing it...")

        # Store body of request response
        self.data.extend(body)



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start do
        super(PumpCommand, self).do()

        # Download data
        self.download()

        # Give enough time for last command to be executed
        time.sleep(self.commandSleep)



# STICK COMMANDS
class ReadStickInfos(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(stick)

        # Define possible statuses
        self.statuses = {85: "OK",
                         102: "Error"}

        # Define possible frequencies of operation for the stick (MHz)
        self.frequencies = {0: 916.5,
                            1: 868.35,
                            255: 916.5}

        # Define info
        self.info = "Reading stick's infos..."

        # Define packet code
        self.packet.code = [4]



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode and assign infos
        self.response = {"ACK": self.bytes[0],
                         "Status": self.statuses[self.bytes[1]],
                         "Description": "".join(lib.charify(self.bytes[9:19])),
                         "Version": self.bytes[19] + self.bytes[20] / 100.0,
                         "Frequency": self.frequencies[self.bytes[8]]}



class ReadStickSignalStrength(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(stick)

        # Define info
        self.info = "Reading stick's signal strength..."

        # Define packet code
        self.packet.code = [6]



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode and assign signal strength
        self.response = self.bytes[3]



class ReadStickState(StickCommand):

    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode and assign state
        self.response = {"CRC": self.bytes[3],
                         "SEQ": self.bytes[4],
                         "NAK": self.bytes[5],
                         "Timeout": self.bytes[6],
                         "Received": lib.pack(self.bytes[7:11], ">"),
                         "Sent": lib.pack(self.bytes[11:15], ">")}



class ReadStickUSBState(ReadStickState):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(stick)

        # Define info
        self.info = "Reading stick's USB state..."

        # Define packet code
        self.packet.code = [5, 0]



class ReadStickRadioState(ReadStickState):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(stick)

        # Define info
        self.info = "Reading stick's radio state..."

        # Define packet code
        self.packet.code = [5, 1]



# PUMP COMMANDS
class PowerPump(PumpCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick)

        # Define info
        self.info = "Powering pump's radio transmitter..."

        # Define time for which pump will listen to RF communications (m)
        self.sessionTime = 10

        # Define packet bytes
        self.packet.power = 85
        self.packet.attempts = 0
        self.packet.size = 0
        self.packet.code = 93
        self.packet.parameters = [1, self.sessionTime]

        # Define time needed for the pump's radio to power up (s)
        self.commandSleep = 10



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
