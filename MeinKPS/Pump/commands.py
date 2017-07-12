#! /usr/bin/python
# -*- coding: utf-8 -*-

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
import datetime
import time



# USER LIBRARIES
import lib
import errors
import packets
import reporter



# Define a reporter
Reporter = reporter.Reporter()



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

        # Initialize report
        self.report = None

        # Define byte counts
        self.nBytesDefault = 64
        self.nBytesExpected = 0
        self.nBytesReceived = 0

        # Define max attempts
        self.nReadAttempts = 100

        # Define sleep times (s)
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

        # Send packet as bytes to device
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

        # Reset bytes
        self.bytes = []

        # Decide on number of bytes to read. If less bytes expected than usual,
        # set to default value. Otherwise, read expected number of bytes.
        nBytes = max(self.nBytesExpected, self.nBytesDefault)

        # Give user info
        print "Trying to read " + str(nBytes) + " bytes from device..."

        # Initialize reading attempt variable
        n = 0

        # Read until there is a response
        while len(self.bytes) == 0:

            # Update reading attempt variable
            n += 1

            # Give user info
            print "Reading: " + str(n) + "/" + str(self.nReadAttempts)

            # Read raw bytes from device
            self.bytes = self.stick.read(nBytes)

            # Exit after a maximal number of attempts
            if n == self.nReadAttempts:

                # Raise error
                raise errors.MaxRead(self.nReadAttempts)

            # Otherwise
            else:

                # Give stick a break before reading again
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
        print "Device's response: "

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



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
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



class StickCommand(Command):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(StickCommand, self).__init__(stick)

        # Define report
        self.report = "stick.json"

        # Give the command a packet
        self.packet = packets.StickPacket(self)



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start doing
        super(StickCommand, self).do()

        # Decode response
        self.decode()



class PumpCommand(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PumpCommand, self).__init__(pump.stick)

        # Initialize downloaded data
        self.data = None

        # Define end of download byte
        self.EOD = 128

        # Define max attempts
        self.nPollAttempts = 100
        self.nDownloadAttempts = 50

        # Define sleep times (s)
        self.pollSleep = 0.1
        self.downloadSleep = 0
        self.executionSleep = 0.5

        # Define report
        self.report = "pump.json"

        # Give the command a packet
        self.packet = packets.PumpPacket(self)

        # Link with pump
        self.pump = pump



    def poll(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            POLL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Q: does expecting no less than 15 bytes solve the critical number of
           bytes problem?
        """

        # Reset number of bytes expected
        self.nBytesExpected = 0

        # Build poll packet
        self.packet.build("Poll")

        # Define polling attempt variable
        n = 0

        # Poll until data is ready to be read
        while self.nBytesExpected == 0:

            # Update attempt variable
            n += 1

            # Keep track of attempts
            print "Polling: " + str(n) + "/" + str(self.nPollAttempts)

            # Send packet
            self.send()

            # Get size of response waiting in radio buffer
            self.nBytesExpected = self.bytes[7]

            # Exit after a maximal number of attempts
            if n == self.nPollAttempts:

                # Raise error
                raise errors.MaxPoll(self.nPollAttempts)

            # Otherwise
            else:

                # Poll sleep
                time.sleep(self.pollSleep)

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
            print "Downloading: " + str(n) + "/" + str(self.nDownloadAttempts)

            # Poll data
            self.poll()

            # Build download packet
            self.packet.build("Download")

		    # Send packet
            self.send()

            # Verify downloaded data
            if self.verify():

                # Exit loop
                break

            # Exit after a maximal number of attempts
            elif n == self.nDownloadAttempts:

                # Raise error
                raise errors.MaxDownload(self.nDownloadAttempts)

            # Otherwise
            else:

                # Download sleep
                time.sleep(self.downloadSleep)

        # Give user info
        print "End of data. Exiting download loop."
        print "Downloaded data in " + str(n) + " attempt(s)."



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Parse response
        [head, body, CRC] = self.parse()

        # Check for communication problems
        if head[2] == 5:

            # Raise error
            raise errors.BadCommunications()

        # Check for problematic number of bytes
        if self.nBytesExpected < 14:

            # Raise error
            raise errors.BadNExpectedBytes()

        # Check for mismatching numbers of bytes
        if self.nBytesReceived != self.nBytesExpected:

            # Raise error
            raise errors.NBytesMismatch(self.nBytesExpected,
                                        self.nBytesReceived)

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

        # Store response body
        self.data.extend(body)

        # If end of data
        if head[5] >= self.EOD:

            # Exit
            return True

        # Otherwise keep downloading
        else:

            # Do not exit
            return False



    def parse(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Parse response
        head = self.bytes[0:13]
        body = self.bytes[13:-1]
        CRC = self.bytes[-1]

        # Return parsed response
        return [head, body, CRC]



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

        # Decode response
        self.decode()

        # Store response
        self.store()

        # Give enough time for last command to be executed
        time.sleep(self.executionSleep)



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

        # Define possible statuses
        statuses = {85: "OK",
                    102: "Error"}

        # Define possible frequencies of operation for the stick (MHz)
        frequencies = {0: 916.5,
                       1: 868.35,
                       255: 916.5}

        # Decode and assign infos
        self.response = {"ACK": self.bytes[0],
                         "Status": statuses[self.bytes[1]],
                         "Description": "".join(lib.charify(self.bytes[9:19])),
                         "Version": self.bytes[19] + self.bytes[20] / 100.0,
                         "Frequency": frequencies[self.bytes[8]]}



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
                         "Received": lib.unpack(self.bytes[7:11], ">"),
                         "Sent": lib.unpack(self.bytes[11:15], ">")}



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

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

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
        self.executionSleep = 12

        # Define report
        self.report = "history.json"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's last power up to '" + self.report + "'..."

        # Get current formatted time
        now = lib.formatTime(datetime.datetime.now())

        # Add entry
        Reporter.add(self.report, ["Pump"], {"Power": now}, True)



class ReadPumpTime(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's time..."

        # Define packet bytes
        self.packet.code = 112



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump time
        second = self.data[2]
        minute = self.data[1]
        hour = self.data[0]
        day = self.data[6]
        month = self.data[5]
        year = lib.unpack(self.data[3:5], ">")

        # Generate time object
        time = datetime.datetime(year, month, day, hour, minute, second)

        # Store formatted time
        self.response = lib.formatTime(time)



class ReadPumpModel(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's model..."

        # Define packet bytes
        self.packet.code = 141



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump model
        self.response = "".join(lib.charify(self.data[1:4]))



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's model to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Properties"], {"Model": self.response}, True)



class ReadPumpFirmware(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's firmware..."

        # Define packet bytes
        self.packet.code = 116



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump firmware
        self.response = ("".join(lib.charify(self.data[4:8])) + " " +
                         "".join(lib.charify(self.data[8:11])))



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's firmware to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Properties"], {"Firmware": self.response}, True)



class PushPumpButton(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Pushing button..."

        # Define packet bytes
        self.packet.attempts = 1
        self.packet.size = 0
        self.packet.code = 91

        # Define buttons
        self.values = {"EASY": 0,
                       "ESC": 1,
                       "ACT": 2,
                       "UP": 3,
                       "DOWN": 4}



    def do(self, value):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define packet parameters byte
        self.packet.parameters = [self.values[value]]
        
        # Do rest of command
        super(self.__class__, self).do()



class ReadPumpBattery(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's battery level..."

        # Define packet bytes
        self.packet.code = 114

        # Define report
        self.report = "history.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode battery voltage
        self.response = round(lib.unpack(self.data[1:3], ">") / 100.0, 2)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's battery level to '" + self.report + "'..."

        # Get current time
        now = datetime.datetime.now()

        # Add entry
        Reporter.add(self.report, ["Pump", "Battery Levels"], {now: self.response})



class ReadPumpReservoir(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's reservoir level..."

        # Define packet bytes
        self.packet.code = 115

        # Define report
        self.report = "history.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode reservoir level
        self.response = round(lib.unpack(self.data[0:2], ">") *
                              self.pump.bolus.stroke, 1)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's reservoir level to '" + self.report + "'..."

        # Get current time
        now = datetime.datetime.now()

        # Add entry
        Reporter.add(self.report, ["Pump", "Reservoir Levels"], {now: self.response})



class ReadPumpStatus(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's status..."

        # Define packet bytes
        self.packet.code = 206



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump status
        self.response = {"Normal": self.data[0] == 3,
                         "Bolusing": self.data[1] == 1,
                         "Suspended": self.data[2] == 1}



class SuspendPump(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Suspending pump..."

        # Define packet bytes
        self.packet.code = 77
        self.packet.parameters = [1]



class ResumePump(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Resuming pump..."

        # Define packet bytes
        self.packet.code = 77
        self.packet.parameters = [0]



class ReadPumpSettings(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's settings..."

        # Define packet bytes
        self.packet.code = 192



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump status
        self.response = {"DIA": self.data[17],
                         "Max Bolus": self.data[5] * self.pump.bolus.stroke,
                         "Max Basal": (lib.unpack(self.data[6:8], ">") *
                                       self.pump.TB.stroke)}



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's settings to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Settings": self.response}, True)



class ReadPumpBGU(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's BG units..."

        # Define packet bytes
        self.packet.code = 137



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode BG units set on pump
        if self.data[0] == 1:
            self.response = "mg/dL"

        elif self.data[0] == 2:
            self.response = "mmol/L"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's BG units to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Units"], {"BG": self.response}, True)



class ReadPumpCU(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's carb units..."

        # Define packet bytes
        self.packet.code = 136



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode carb units set on pump
        if self.data[0] == 1:
            self.response = "g"

        elif self.data[0] == 2:
            self.response = "exchange"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's carb units to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Units"], {"Carbs": self.response}, True)



class SetPumpTBU(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Setting pump's TB units..."

        # Define packet bytes
        self.packet.attempts = 0
        self.packet.size = 1
        self.packet.code = 104



    def do(self, units):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If absolute TB
        if units == "U/h":
            self.packet.parameters = [0]

        # If percentage
        elif units == "%":
            self.packet.parameters = [1]
        
        # Do rest of command
        super(self.__class__, self).do()



class ReadPumpBGTargets(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's BG target(s)..."

        # Define packet bytes
        self.packet.code = 159



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize response
        self.response = {"Times": [],
                         "Targets": [],
                         "Units": None}

        # Decode units
        if self.data[0] == 1:
            self.response["Units"] = "mg/dL"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "mmol/L"

            # Define a multiplicator to decode bytes
            m = 1.0

        # Initialize index as well as times and targets
        i = 0
        times = []
        targets = []

        # Extract BG targets
        while True:

            # Define start (a) and end (b) indexes of current factor based
            # on number of bytes per entry
            n = 3
            a = 1 + n * i
            b = a + n

            # Get current target entry
            entry = self.data[a:b]

            # Exit condition: no more targets stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[0] * self.pump.TB.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                target = [entry[1] / 10 ** m, entry[2] / 10 ** m]

                # Store decoded target and its corresponding ending time
                targets.append(target)
                times.append(time)

            # Increment index
            i += 1

        # Assign times and targets
        self.response["Times"] = times
        self.response["Targets"] = targets



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # VERIFY

        # Link with values
        t = self.response["Times"]
        targets = self.response["Targets"]
        units = self.response["Units"]

        # Give user info
        print "Adding pump's BG targets to '" + self.report + "'..."

        # Store targets
        Reporter.add(self.report, ["BG Targets"], dict(zip(t, targets)), True)

        # Store BG units
        Reporter.add(self.report, ["Units"], {"BG": units}, True)



class ReadPumpISF(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's ISF(s)..."

        # Define packet bytes
        self.packet.code = 139



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize response
        self.response = {"Times": [],
                         "Factors": [],
                         "Units": None}

        # Decode units
        if self.data[0] == 1:
            self.response["Units"] = "mg/dL/U"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "mmol/L/U"

            # Define a multiplicator to decode bytes
            m = 1.0

        # Initialize index as well as times and factors
        i = 0
        times = []
        factors = []

        # Extract ISF
        while True:

            # Define start (a) and end (b) indexes of current factor based
            # on number of bytes per entry
            n = 2
            a = 1 + n * i
            b = a + n

            # Get current factor entry
            entry = self.data[a:b]

            # Exit condition: no more factors stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[0] % 64 * self.pump.TB.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                factor = lib.unpack([entry[0] / 64,
                                     entry[1]], order = ">") / 10 ** m

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Assign times and factors
        self.response["Times"] = times
        self.response["Factors"] = factors



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # VERIFY

        # Link with values
        t = self.response["Times"]
        factors = self.response["Factors"]
        units = self.response["Units"]

        # Give user info
        print "Adding pump's ISF(s) to '" + self.report + "'..."

        # Store factors
        Reporter.add(self.report, ["ISF"], dict(zip(t, factors)), True)

        # Update units for BGs
        units = units[:-2]

        # Store BG units (without insulin units)
        Reporter.add(self.report, ["Units"], {"BG": units}, True)



class ReadPumpCSF(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's CSF(s)..."

        # Define packet bytes
        self.packet.code = 138



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize response
        self.response = {"Times": [],
                         "Factors": [],
                         "Units": None}

        # Decode units
        if self.data[0] == 1:
            self.response["Units"] = "g/U"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "U/exchange"

            # Define a multiplicator to decode bytes
            m = 1.0

        # Initialize index as well as times and factors
        i = 0
        times = []
        factors = []

        # Extract ISF
        while True:

            # Define start (a) and end (b) indexes of current factor based
            # on number of bytes per entry
            n = 2
            a = 1 + n * i
            b = a + n

            # Get current factor entry
            entry = self.data[a:b]

            # Exit condition: no more factors stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[0] % 64 * self.pump.TB.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                factor = lib.unpack([entry[0] / 64,
                                     entry[1]], order = ">") / 10 ** m

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Assign times and factors
        self.response["Times"] = times
        self.response["Factors"] = factors



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # VERIFY

        # Link with values
        t = self.response["Times"]
        factors = self.response["Factors"]
        units = self.response["Units"]

        # Give user info
        print "Adding pump's CSF(s) to '" + self.report + "'..."

        # Store factors
        Reporter.add(self.report, ["CSF"], dict(zip(t, factors)), True)

        # Update units for carbs
        if units == "g/U":
            units = units[:-2]

        else:
            units = units[2:] + "s"

        # Store carb units (without insulin units)
        Reporter.add(self.report, ["Units"], {"Carbs": units}, True)



class ReadPumpBasal(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Initialize profile
        self.profile = None

        # Define packet bytes
        self.packet.size = 2



    def do(self, value):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define info
        self.info = "Reading pump's basal profile '" + value + "'..."

        # If standard profile
        if value == "Standard":
            self.packet.code = 146

        # If profile A
        elif value == "A":
            self.packet.code = 147

        # If profile B
        elif value == "B":
            self.packet.code = 148

        # Store profile
        self.profile = value
        
        # Do rest of command
        super(self.__class__, self).do()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize response
        self.response = {"Times": [],
                         "Rates": []}

        # Initialize index as well as times and rates
        i = 0
        times = []
        rates = []

        # Extract ISF
        while True:

            # Define start (a) and end (b) indexes of current rate based
            # on number of bytes per entry
            n = 3
            a = n * i
            b = a + n

            # Get current rate entry
            entry = self.data[a:b]

            # Exit condition: no more rates stored
            if not sum(entry) or len(entry) != n:
                break

            else:

                # Decode time
                time = entry[2] * self.pump.TB.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                rate = lib.unpack(entry[0:2]) / self.pump.bolus.rate

                # Store decoded rate and its corresponding ending time
                rates.append(rate)
                times.append(time)

            # Increment index
            i += 1

        # Assign times and rates
        self.response["Times"] = times
        self.response["Rates"] = rates



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print ("Adding pump's basal profile " + self.profile + " to '" + 
               self.report + "'...")

        # Store basal
        Reporter.add(self.report, ["Basal Profile (" + self.profile + ")"],
                     dict(zip(self.response["Times"],
                              self.response["Rates"])), True)



class ReadPumpDailyTotals(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's daily totals..."

        # Define packet bytes
        self.packet.code = 121



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode daily totals
        self.response = {"Today": round(lib.unpack(self.data[0:2], ">") *
                                        self.pump.bolus.stroke, 2),
                         "Yesterday": round(lib.unpack(self.data[2:4], ">") *
                                            self.pump.bolus.stroke, 2)}



class MeasurePumpHistory(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading pump's number of history pages..."

        # Define packet bytes
        self.packet.code = 157



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode and store number of history pages
        self.response = self.data[3] + 1



class ReadPumpHistory(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define packet bytes
        self.packet.size = 2
        self.packet.code = 128



    def do(self, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        self.info = "Reading pump's history page: " + str(page) + "..."

        # Define packet parameters byte
        self.packet.parameters = [page]
        
        # Do rest of command
        super(self.__class__, self).do()

        # Link with pump history
        records = self.pump.history.records

        # Find records within page and decode them
        for record in records:
            records[record].find(self.data)

        # Return pump history page
        self.response = self.data



class DeliverPumpBolus(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define packet bytes
        self.packet.attempts = 0
        self.packet.code = 66



    def do(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        self.info = "Sending bolus: " + str(bolus) + " U"

        # Compute time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        self.executionSleep = (self.pump.bolus.rate * bolus +
                               self.pump.bolus.sleep)

        # Define parameters byte
        self.packet.parameters = [int(round(bolus / self.pump.bolus.stroke))]
        
        # Do rest of command
        super(self.__class__, self).do()



class ReadPumpTB(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading current TB..."

        # Define packet bytes
        self.packet.code = 152



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize response
        self.response = {"Units": None,
                         "Rate": None,
                         "Duration": None}

        # Decode TB [U/h]
        if self.data[0] == 0:

            # Decode TB characteristics
            self.response["Units"] = "U/h"
            self.response["Rate"] = round(lib.unpack(self.data[2:4], ">") *
                                          self.pump.TB.stroke, 2)

        # Decode TB [%]
        elif self.data[0] == 1:

            # Decode TB characteristics
            self.response["Units"] = "%"
            self.response["Rate"] = round(self.data[1], 2)

        # Decode TB remaining time
        self.response["Duration"] = round(lib.unpack(self.data[4:6], ">"), 0)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's TB units to '" + self.report + "'..."

        # Store TB units
        Reporter.add(self.report, ["Units"], {"TB": self.response["Units"]},
                     True)



class SetPumpTB(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define packet bytes
        self.packet.attempts = 0



    def do(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define info
        self.info = ("Setting TB...")

        # If absolute TB
        if TB["Units"] == "U/h":

            # Define packet code
            self.packet.code = 76

            # Define packet parameters
            self.packet.parameters = ([0] * 2 +
                                      lib.pack(round(TB["Rate"] /
                                                     self.pump.TB.stroke),
                                               ">"))[-2:]

        # If percentage TB
        elif TB["Units"] == "%":

            # Define packet code
            self.packet.code = 105

            # Define packet parameters
            self.packet.parameters = [int(TB["Rate"])]

        # Define rest of packet parameters
        self.packet.parameters += [int(TB["Duration"] /
                                       self.pump.TB.timeBlock)]

        # Do rest of command
        super(self.__class__, self).do()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
