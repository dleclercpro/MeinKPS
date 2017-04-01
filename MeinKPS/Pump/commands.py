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
import time
import datetime



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

            # Read raw bytes from device
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

        # Define max number of poll attempts
        self.nPollAttempts = 100

        # Define sleep times
        self.pollSleep = 0.1
        self.executionSleep = 0.1

        # Give the command a packet
        self.packet = packets.PumpPacket(self)

        # Link with pump
        self.pump = pump



    def poll(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            POLL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

            # Build download packet
            self.packet.build("Download")

		    # Send packet
            self.send()

            # Verify and store downloaded data if it corresponds to expectations
            self.verify()

	        # Look for end of data (EOD) condition
            if self.bytes[5] >= self.EOD:

                # Give user info
                print "End of data. Exiting download loop."

                break

        # Reset number of bytes expected after download
        self.nBytesExpected = 0

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

        # Store response body
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

        # Decode response
        self.decode()

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
        self.executionSleep = 10



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
        hour   = self.data[0]
        day    = self.data[6]
        month  = self.data[5]
        year   = lib.bangInt(self.data[3:5])

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



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode battery voltage
        self.response = round(lib.bangInt([self.data[1],
                                           self.data[2]]) / 100.0, 1)



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



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode reservoir level
        self.response = round(lib.bangInt(self.data[0:2]) *
                              self.pump.bolus.stroke, 1)



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
                         "Max Basal": (lib.bangInt(self.data[6:8]) *
                                       self.pump.TBR.stroke / 2.0)}



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
            self.response = "exchanges"



class SetPumpTBRU(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Setting pump's TBR units..."

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

        # If absolute TBR
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
        self.info = "Reading pump's BG targets..."

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
            a = 2 + n * i
            b = a + n

            # Get current target entry
            entry = self.data[a:b]

            # Exit condition: no more targets stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[2] * self.pump.TBR.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                target = [entry[0] / 10 ** m, entry[1] / 10 ** m]

                # Store decoded target and its corresponding ending time
                targets.append(target)
                times.append(time)

            # Increment index
            i += 1

        # Rearrange and store targets to have starting times instead of ending
        # times
        for i in range(len(targets)):
            self.response["Times"].append(times[i - 1])
            self.response["Targets"].append(targets[i])



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
        self.info = "Reading pump's ISF..."

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
            self.response["Units"] = "mg/dL"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "mmol/L"

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
            a = 2 + n * i
            b = a + n

            # Get current factor entry
            entry = self.data[a:b]

            # Exit condition: no more factors stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[1] * self.pump.TBR.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                factor = entry[0] / 10 ** m

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Rearrange and store factors to have starting times instead of ending
        # times
        for i in range(len(factors)):
            self.response["Times"].append(times[i - 1])
            self.response["Factors"].append(factors[i])



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
        self.info = "Reading pump's CSF..."

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
            self.response["Units"] = "g"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "exchanges"

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
            a = 2 + n * i
            b = a + n

            # Get current factor entry
            entry = self.data[a:b]

            # Exit condition: no more factors stored
            if not sum(entry):
                break

            else:

                # Decode time
                time = entry[1] * self.pump.TBR.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                factor = entry[0] / 10 ** m

                # Store decoded factor and its corresponding ending time
                factors.append(factor)
                times.append(time)

            # Increment index
            i += 1

        # Rearrange and store factors to have starting times instead of ending
        # times
        for i in range(len(factors)):
            self.response["Times"].append(times[i - 1])
            self.response["Factors"].append(factors[i])



class ReadPumpBasalProfile(PumpCommand):

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

        # Decode units
        if self.data[0] == 1:
            self.response["Units"] = "g"

            # Define a multiplicator to decode bytes
            m = 0

        elif self.data[0] == 2:
            self.response["Units"] = "exchanges"

            # Define a multiplicator to decode bytes
            m = 1.0

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
                print entry
                time = entry[2] * self.pump.TBR.timeBlock

                # Format time
                time = (str(time / 60).zfill(2) + ":" +
                        str(time % 60).zfill(2))

                # Decode entry
                rate = entry[0] / self.pump.bolus.rate

                # Store decoded rate and its corresponding ending time
                rates.append(rate)
                times.append(time)

            # Increment index
            i += 1

        # Rearrange and store rates to have starting times instead of ending
        # times
        for i in range(len(rates)):
            self.response["Times"].append(times[i])
            self.response["Rates"].append(rates[i])



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
        self.response = {"Today": round(lib.bangInt(self.data[0:2]) *
                                        self.pump.bolus.stroke, 2),
                         "Yesterday": round(lib.bangInt(self.data[2:4]) *
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
        self.packet.parameters = [int(bolus / self.pump.bolus.stroke)]
        
        # Do rest of command
        super(self.__class__, self).do()



class ReadPumpTBR(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump)

        # Define info
        self.info = "Reading current TBR..."

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

        # Decode TBR [U/h]
        if self.data[0] == 0:

            # Decode TBR characteristics
            self.response["Units"] = "U/h"
            self.response["Rate"] = round(lib.bangInt(self.data[2:4]) *
                                          self.pump.TBR.stroke / 2.0, 2)

        # Decode TBR [%]
        elif self.data[0] == 1:

            # Decode TBR characteristics
            self.response["Units"] = "%"
            self.response["Rate"] = round(self.data[1], 2)

        # Decode TBR remaining time
        self.response["Duration"] = round(lib.bangInt(self.data[4:6]), 0)



class SetPumpTBR(PumpCommand):

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



    def do(self, TBR):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define info
        self.info = ("Setting TBR: " + str(TBR["Rate"]) + " " +
                                       TBR["Units"] + " (" +
                                       str(TBR["Duration"]) + "m)")

        # If absolute TBR
        if TBR["Units"] == "U/h":
            self.packet.code = 76
            self.packet.parameters = [0, int(round(TBR["Rate"] /
                                                   self.pump.TBR.stroke * 2.0)),
                                         int(TBR["Duration"] /
                                             self.pump.TBR.timeBlock)]

        # If percentage TBR
        elif TBR["Units"] == "%":
            self.packet.code = 105
            self.packet.parameters = [int(round(TBR["Rate"])),
                                      int(TBR["Duration"] /
                                      self.pump.TBR.timeBlock)]

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
