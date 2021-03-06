#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    commands

    Author:   David Leclerc

    Version:  0.1

    Date:     28.03.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains various commands to control a
              Medtronic MiniMed insulin pump over radio frequencies using the
              Texas Instruments CC1111 USB radio stick.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime



# USER LIBRARIES
import lib
import logger
import errors
import reporter
import packets



# Define instances
Logger = logger.Logger("Pump.commands")



# CLASSES
class Command(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store pump instance
        self.pump = pump

        # Initialize code
        self.code = None

        # Initialize report
        self.report = None

        # Define radio timeout
        self.timeout = 250

        # Define classes to generate packets
        self.toPumpPacket = packets.ToPumpPacket
        self.fromPumpPacket = packets.FromPumpPacket

        # Initialize resettable command characteristics
        self.reset()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset response
        self.response = None

        # Reset data
        self.data = {"TX": [], "RX": []}

        # Reset packets
        self.packets = {"TX": [], "RX": []}

        # Reset parameters
        self.parameters = ["00"]



    def encode(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



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



    def execute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXECUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command
        self.send()

        # Receive response
        self.receive()



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Generate packet to send to pump
        pkt = self.toPumpPacket(self.code, self.parameters)

        # Show it
        pkt.show()

        # Store it
        self.packets["TX"].append(pkt)

        # Send encoded packet
        self.pump.stick.commands["Radio TX/RX"].run(pkt.bytes["Encoded"],
            self.timeout)



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store data
        self.data["RX"].append(self.pump.stick.commands["Radio TX/RX"]
            .data["RX"])

        # Parse data into packet
        pkt = self.fromPumpPacket(self.data["RX"][-1])

        # Show it
        pkt.show()

        # Store it
        self.packets["RX"].append(pkt)



    def run(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            When command is run, its core is executed, then the received data
            (if any) is decoded, then returned.
        """

        # Reset command
        self.reset()

        # Encode parameters
        self.encode(*args)

        # Execute command
        self.execute()

        # Decode it
        self.decode()

        # Store response
        self.store()

        # Return it
        return self.response



class Set(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(Set, self).__init__(pump)

        # Define class to generate receive packet
        self.fromPumpPacket = packets.FromPumpStatusPacket



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last packet
        pkt = self.packets["RX"][-1]

        # Define command ACK
        ack = ["06", "00"]

        # Unsuccessful
        if [pkt.code] + pkt.payload != ack:
            raise errors.UnsuccessfulRadioCommand



class Get(Command):

    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last packet
        pkt = self.packets["RX"][-1]

        # Return payload in integer format for further decoding and its size
        return [lib.dehexify(pkt.payload), pkt.size]



class BigCommand(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(BigCommand, self).__init__(pump)

        # Define number of times commands need to be executed
        self.repeat = {"Init": 1,
                       "ACK": 0,
                       "NAK": 0}

        # Define commands
        self.commands = {"Init": None,
                         "ACK": ACK(pump),
                         "NAK": NAK(pump)}



    def prelude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PRELUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Run prelude command given number of times
        for _ in range(self.repeat["Init"]):

            # Do it
            self.commands["Init"].run()

            # Store response packet
            self.packets["RX"].append(self.commands["Init"].packets["RX"][-1])



    def postlude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            POSTLUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Ask the pump to send the rest of the data a given number of times,
            using ACKs.
        """

        # Run postlude command given number of times
        for _ in range(self.repeat["ACK"]):

            # Try
            try:

                # Do it
                self.commands["ACK"].run()

                # Store response packet
                self.packets["RX"].append(self.commands["ACK"]
                                              .packets["RX"][-1])

            # Radio error: retry (if possible)
            except (errors.RadioError, errors.PacketError):
                self.retry()



    def execute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXECUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute command core
        try:
            super(BigCommand, self).execute()

        # Radio error: retry (if possible)
        except (errors.RadioError, errors.PacketError):
            self.retry()



    def retry(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RETRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Ask the pump to resend the last packet a given number of times
            (number of allowed repetitions), using a NAK.
        """

        # Run NAK command given number of times
        for i in range(self.repeat["NAK"]):

            # Info
            Logger.debug("Retrying (NAK): " + str(i + 1) + "/" +
                str(self.repeat["NAK"]))

            # Try
            try:

                # Re-ask for packet using NAK
                self.commands["NAK"].run()

                # Store response packet
                self.packets["RX"].append(self.commands["NAK"]
                    .packets["RX"][-1])

                # Exit
                return

            # Ignore radio errors/bad packets
            except (errors.RadioError, errors.PacketError):
                pass

        # Unsuccessful command
        raise errors.UnsuccessfulRadioCommand



    def run(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset command
        self.reset()

        # Encode parameters
        self.encode(*args)

        # Execute prelude
        self.prelude()

        # Execute command core
        self.execute()

        # Execute postlude
        self.postlude()

        # Decode it
        self.decode()

        # Store response
        self.store()

        # Return response
        return self.response



class BigGet(BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(BigGet, self).__init__(pump)

        # Define number of NAK retries
        self.repeat["NAK"] = 10

        # Define radio timeout
        self.timeout = 150

        # Overwrite ACK and NAK timeout
        self.commands["ACK"].timeout = self.timeout
        self.commands["NAK"].timeout = self.timeout

        # Define class to generate receive packet
        self.fromPumpPacket = packets.FromPumpBigPacket



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last packets (without prelude)
        pkts = self.packets["RX"][self.repeat["Init"]:]

        # Flatten payloads to one larger one
        payload = lib.dehexify(lib.flatten([pkt.payload for pkt in pkts]))

        # Return it for further decoding as well as its size
        return [payload, len(payload)]









class ACK(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ACK, self).__init__(pump)

        # Define code
        self.code = "06"

        # Define class to generate receive packet
        self.fromPumpPacket = packets.FromPumpBigPacket



class NAK(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(NAK, self).__init__(pump)

        # Define code
        self.code = "15"

        # Define class to generate receive packet
        self.fromPumpPacket = packets.FromPumpBigPacket



class PowerInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PowerInit, self).__init__(pump)

        # Define code
        self.code = "5D"



class Power(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(Power, self).__init__(pump)

        # Define code
        self.code = "5D"

        # Define report
        self.report = reporter.getPumpReport()

        # Define prelude command
        self.commands["Init"] = PowerInit(pump)

        # Define prelude command repeat counts
        self.repeat["Init"] = 50



    def prelude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PRELUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute a given number of times
        for _ in range(self.repeat["Init"]):

            # Execute command
            try:
                self.commands["Init"].run()
                return

            # Ignore specific errors
            except (errors.RadioError, errors.PacketError):
                pass

        # Pump does not respond
        raise errors.NoPump



    def encode(self, t = 10):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Test RF session length
        lib.withinRangeInt(t, [0, 30], "Invalid RF session length.")

        # Define number of bytes to read from payload
        self.parameters = ["02"] + 64 * ["00"]

        # Define arbitrary byte
        self.parameters[1] = "01"

        # Define button
        self.parameters[2] = "{0:02X}".format(t)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump last power up to: " + repr(self.report))

        # Get current formatted time
        now = lib.formatTime(datetime.datetime.now())

        # Add entry
        self.report.set(now, ["Power"], True)
        self.report.store()



class ReadTime(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadTime, self).__init__(pump)

        # Define code
        self.code = "70"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadTime, self).decode()

        # Destructure
        [h, m, s, Y1, Y2, M, D] = payload[0:7]

        # Unpack year
        Y = lib.unpack([Y1, Y2])

        # Store formatted time
        self.response = lib.formatTime(datetime.datetime(Y, M, D, h, m, s))



class ReadModel(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadModel, self).__init__(pump)

        # Define code
        self.code = "8D"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadModel, self).decode()

        # Convert payload to char format
        payload = lib.charify(payload)

        # Decode
        self.response = int("".join(payload[1:4]))



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump model to: " + repr(self.report))

        # Add entry
        self.report.set(self.response, ["Properties", "Model"], True)
        self.report.store()



class ReadFirmware(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadFirmware, self).__init__(pump)

        # Define code
        self.code = "74"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadFirmware, self).decode()

        # Convert payload to char format
        payload = lib.charify(payload)

        # Decode
        self.response = "".join(payload[0:8] + [" "] + payload[8:11])



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump firmware to: " + repr(self.report))

        # Add entry
        self.report.set(self.response, ["Properties", "Firmware"], True)
        self.report.store()



class ReadBattery(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBattery, self).__init__(pump)

        # Define code
        self.code = "72"

        # Define report type
        self.reportType = reporter.HistoryReport



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadBattery, self).decode()

        # Decode
        self.response = round(lib.unpack(payload[1:3]) / 100.0, 2)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump battery level to: " + repr(self.reportType))

        # Get current time
        now = datetime.datetime.now()

        # Add entry
        reporter.setDatedEntries(self.reportType, ["Pump", "Battery Levels"],
            { now: self.response })



class ReadReservoir(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadReservoir, self).__init__(pump)

        # Define code
        self.code = "73"

        # Define report type
        self.reportType = reporter.HistoryReport



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadReservoir, self).decode()

        # Decode
        self.response = round(lib.unpack(payload[0:2]) * self.pump.bolus.stroke,
                              1)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump reservoir level to: " + repr(self.reportType))

        # Get current time
        now = datetime.datetime.now()

        # Add entry
        reporter.setDatedEntries(self.reportType, ["Pump", "Reservoir Levels"],
            { now: self.response })



class ReadStatus(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadStatus, self).__init__(pump)

        # Define code
        self.code = "CE"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadStatus, self).decode()

        # Decode
        self.response = {"Normal": payload[0] == 3,
                         "Bolusing": payload[1] == 1,
                         "Suspended": payload[2] == 1}



class ReadSettings(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadSettings, self).__init__(pump)

        # Define code
        self.code = "C0"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadSettings, self).decode()

        # Decode
        self.response = {"DIA": payload[17],
                         "Max Bolus": payload[5] * self.pump.bolus.stroke,
                         "Max Basal": lib.unpack(payload[6:8]) *
                                      self.pump.basal.stroke}



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump settings to: " + repr(self.report))

        # Add entry
        self.report.set(self.response, ["Settings"], True)
        self.report.store()



class ReadBGUnits(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBGUnits, self).__init__(pump)

        # Define code
        self.code = "89"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadBGUnits, self).decode()

        # Decode
        # mg/dL
        if payload[0] == 1:

            # Store response
            self.response = "mg/dL"

        # mmol/L
        elif payload[0] == 2:

            # Store response
            self.response = "mmol/L"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump BG units to: " + repr(self.report))

        # Add entry
        self.report.set(self.response, ["Units", "BG"], True)
        self.report.store()



class ReadCarbsUnits(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadCarbsUnits, self).__init__(pump)

        # Define code
        self.code = "88"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadCarbsUnits, self).decode()

        # Decode
        # mg/dL
        if payload[0] == 1:

            # Store response
            self.response = "g"

        # mmol/L
        elif payload[0] == 2:

            # Store response
            self.response = "exchange"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump carb units to: " + repr(self.report))

        # Add entry
        self.report.set(self.response, ["Units", "Carbs"], True)
        self.report.store()



class ReadBGTargets(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBGTargets, self).__init__(pump)

        # Define code
        self.code = "9F"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadBGTargets, self).decode()

        # Initialize response
        self.response = {"Times": [],
                         "Targets": [],
                         "Units": None}

        # Define size of entry
        length = 3

        # Decode units
        # mg/dL
        if payload[0] == 1:

            # Store them
            self.response["Units"] = "mg/dL"

            # Define byte multiplicator
            m = 0

        # mmol/L
        elif payload[0] == 2:

            # Store them
            self.response["Units"] = "mmol/L"

            # Define byte multiplicator
            m = 1.0

        # Compute number of targets
        n = (size - 1) / length

        # Decode targets
        for i in range(n):

            # Update index
            i *= length

            # Decode time (m)
            t = payload[i + 1] * self.pump.basal.time

            # Convert it to hours and minutes
            t = "{0:02}".format(t / 60) + ":" + "{0:02}".format(t % 60)

            # Store it
            self.response["Times"].append(t)

            # Decode target
            self.response["Targets"].append([payload[i + 2] / 10 ** m,
                                             payload[i + 3] / 10 ** m])



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump BG targets to: " + repr(self.report))

        # Zip times and targets
        response = dict(zip(self.response["Times"], self.response["Targets"]))

        # Store BG units and targets
        self.report.set(self.response["Units"], ["Units", "BG"], True)
        self.report.set(response, ["BG Targets"], True)
        self.report.store()



class ReadFactors(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadFactors, self).__init__(pump)

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadFactors, self).decode()

        # Initialize response
        self.response = {"Times": [],
                         "Factors": [],
                         "Units": None}

        # Define size of entry
        length = 2

        # Compute number of targets
        n = (size - 1) / length

        # Define decoding factor
        # Integer
        if payload[0] == 1:

            # Do it
            m = 0

        # Float
        elif payload[0] == 2:

            # Do it
            m = 1.0

        # Decode targets
        for i in range(n):

            # Update index
            i *= length

            # Decode time (m)
            t = payload[i + 1] % 64 * self.pump.basal.time

            # Convert it to hours and minutes
            t = "{0:02}".format(t / 60) + ":" + "{0:02}".format(t % 60)

            # Store it
            self.response["Times"].append(t)

            # Decode factor
            f = lib.unpack([payload[i + 1] / 64, payload[i + 2]]) / 10 ** m

            # Store it
            self.response["Factors"].append(f)

        # Return payload for further decoding
        return [payload, size]



class ReadISF(ReadFactors):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadISF, self).__init__(pump)

        # Define code
        self.code = "8B"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadISF, self).decode()

        # Decode units
        # mg/dL
        if payload[0] == 1:
            self.response["Units"] = "mg/dL/U"

        # mmol/L
        elif payload[0] == 2:
            self.response["Units"] = "mmol/L/U"

        # Bad units
        else:
            raise ValueError("Bad ISF units.")



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump ISF(s) to: " + repr(self.report))

        # Zip times and factors
        response = dict(zip(self.response["Times"], self.response["Factors"]))

        # Store BG units and factors
        self.report.set(self.response["Units"][:-2], ["Units", "BG"], True)
        self.report.set(response, ["ISF"], True)
        self.report.store()



class ReadCSF(ReadFactors):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadCSF, self).__init__(pump)

        # Define code
        self.code = "8A"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadCSF, self).decode()

        # Decode units
        # mg/dL
        if payload[0] == 1:
            self.response["Units"] = "g/U"

        # mmol/L
        elif payload[0] == 2:
            self.response["Units"] = "U/exchange"

        # Bad units
        else:
            raise ValueError("Bad CSF units.")



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump CSF(s) to: " + repr(self.report))

        # Zip times and factors
        response = dict(zip(self.response["Times"], self.response["Factors"]))

        # Update units for carbs (without insulin units)
        # g/U
        if self.response["Units"] == "g/U":

            # Define units
            units = self.response["Units"][0]

        # U/exchange
        elif self.response["Units"] == "U/exchange":

            # Define units
            units = self.response["Units"][2:]

        # Store car units and factors
        self.report.set(units, ["Units", "Carbs"], True)
        self.report.set(response, ["CSF"], True)
        self.report.store()



class ReadBasalProfile(BigGet):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBasalProfile, self).__init__(pump)

        # Define report
        self.report = reporter.getPumpReport()

        # Define profile name
        self.name = None

        # Define pre- and postlude command repeat count
        self.repeat["Init"] = 0
        self.repeat["ACK"] = 1



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get whole payload
        [payload, size] = super(ReadBasalProfile, self).decode()

        # Initialize response
        self.response = {"Times": [],
                         "Rates": []}

        # Define size of entry
        length = 3

        # Initialize index
        i = 0

        # Decode targets
        while True:

            # Define start (a) and end (b) indices of current entry based
            # on the latter's size
            a = length * i
            b = a + length

            # Get entry
            entry = payload[a:b]

            # Basal profile not initialized
            if i == 0 and entry == [0, 0, 63]:
                break

            # No more data in payload
            if sum(entry) == 0 or len(entry) != length:
                break

            # Decode time (m)
            t = entry[2] * self.pump.basal.time

            # Convert it to hours and minutes
            t = "{0:02}".format(t / 60) + ":" + "{0:02}".format(t % 60)

            # Store it
            self.response["Times"].append(t)

            # Decode rate
            r = lib.unpack(entry[0:2], "<") / self.pump.bolus.rate

            # Store it
            self.response["Rates"].append(r)

            # Update index
            i += 1



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump basal profile '" + self.name + "' to: " + 
            repr(self.report))

        # Zip times and rates
        response = dict(zip(self.response["Times"], self.response["Rates"]))

        # Store basal
        self.report.set(response, ["Basal Profile (" + self.name + ")"], True)
        self.report.store()



class ReadBasalProfileStandard(ReadBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBasalProfileStandard, self).__init__(pump)

        # Define code
        self.code = "92"

        # Define profile name
        self.name = "Standard"



class ReadBasalProfileA(ReadBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBasalProfileA, self).__init__(pump)

        # Define code
        self.code = "93"

        # Define profile name
        self.name = "A"



class ReadBasalProfileB(ReadBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadBasalProfileB, self).__init__(pump)

        # Define code
        self.code = "94"

        # Define profile name
        self.name = "B"



class ReadDailyTotals(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadDailyTotals, self).__init__(pump)

        # Define code
        self.code = "79"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadDailyTotals, self).decode()

        # Decode
        self.response = {"Today": round(lib.unpack(payload[0:2]) *
                                        self.pump.bolus.stroke, 2),
                         "Yesterday": round(lib.unpack(payload[2:4]) *
                                            self.pump.bolus.stroke, 2)}



class ReadTB(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadTB, self).__init__(pump)

        # Define code
        self.code = "98"

        # Define report
        self.report = reporter.getPumpReport()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadTB, self).decode()

        # Initialize response
        self.response = {"Rate": None,
                         "Units": None,
                         "Duration": None}

        # Decode units
        # U/h
        if payload[0] == 0:

            # Store them
            self.response["Units"] = "U/h"

            # Decode rate
            self.response["Rate"] = round(lib.unpack(payload[2:4]) *
                                          self.pump.basal.stroke, 2)

        # %
        elif payload[0] == 1:

            # Store them
            self.response["Units"] = "%"

            # Decode rate
            self.response["Rate"] = round(payload[1], 2)

        # Decode duration
        self.response["Duration"] = round(lib.unpack(payload[4:6]), 0)



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.debug("Adding pump TB units to: " + repr(self.report))

        # Store TB units
        self.report.set(self.response["Units"], ["Units", "TB"], True)
        self.report.store()



class ReadHistorySize(Get):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadHistorySize, self).__init__(pump)

        # Define code
        self.code = "9D"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadHistorySize, self).decode()

        # Decode (max 36 pages)
        self.response = min(payload[3] + 1, 36)



class ReadHistoryPageInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadHistoryPageInit, self).__init__(pump)

        # Define code
        self.code = "80"



class ReadHistoryPage(BigGet):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadHistoryPage, self).__init__(pump)

        # Define code
        self.code = "80"

        # Define prelude command
        self.commands["Init"] = ReadHistoryPageInit(pump)

        # Define postlude command repeat count
        self.repeat["ACK"] = 15



    def encode(self, page = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Test page number
        lib.withinRangeInt(page, [0, 35], "Invalid history page number.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define page
        self.parameters[1] = "{0:02X}".format(page)



    def crc(self, payload):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CRC
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get expected CRC
        expectedCRC = lib.unpack(payload[-2:])

        # Compute CRC
        computedCRC = lib.computeCRC16(payload[:-2])

        # Compare CRCs
        if computedCRC != expectedCRC:
            raise ValueError("Bad history page CRC. Expected: " +
                str(expectedCRC) + ". Computed: " + str(computedCRC) + ".")



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadHistoryPage, self).decode()

        # Test history page CRC
        self.crc(payload)

        # Set response to payload
        self.response = payload[:-2]



class PushButtonInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PushButtonInit, self).__init__(pump)

        # Define code
        self.code = "5B"



class PushButton(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PushButton, self).__init__(pump)

        # Define code
        self.code = "5B"

        # Define prelude command
        self.commands["Init"] = PushButtonInit(pump)



    def encode(self, button = "DOWN"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get button corresponding byte
        try:
            button = ["EASY", "ESC", "ACT", "UP", "DOWN"].index(button)

        # Bad button
        except ValueError:
            raise IOError("Bad button.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define button
        self.parameters[1] = "{0:02X}".format(button)



class ResumeInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ResumeInit, self).__init__(pump)

        # Define code
        self.code = "4D"



class Resume(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(Resume, self).__init__(pump)

        # Define code
        self.code = "4D"

        # Define prelude command
        self.commands["Init"] = ResumeInit(pump)



    def encode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define button
        self.parameters[1] = "00"



class SuspendInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SuspendInit, self).__init__(pump)

        # Define code
        self.code = "4D"



class Suspend(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(Suspend, self).__init__(pump)

        # Define code
        self.code = "4D"

        # Define prelude command
        self.commands["Init"] = SuspendInit(pump)



    def encode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define button
        self.parameters[1] = "01"



class DeliverBolusInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(DeliverBolusInit, self).__init__(pump)

        # Define code
        self.code = "42"



class DeliverBolus(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(DeliverBolus, self).__init__(pump)

        # Define code
        self.code = "42"

        # Define prelude command
        self.commands["Init"] = DeliverBolusInit(pump)



    def encode(self, bolus = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode bolus
        bolus = int(bolus * 10)

        # Test bolus
        lib.withinRangeInt(bolus, [0, 250], "Invalid bolus.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define bolus
        self.parameters[1] = "{0:02X}".format(bolus)



class SetTBUnitsInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetTBUnitsInit, self).__init__(pump)

        # Define code
        self.code = "68"



class SetTBUnits(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetTBUnits, self).__init__(pump)

        # Define code
        self.code = "68"

        # Define prelude command
        self.commands["Init"] = SetTBUnitsInit(pump)



    def encode(self, units = "U/h"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get unit corresponding byte
        try:
            units = ["U/h", "%"].index(units)

        # Bad units
        except:
            raise ValueError("Bad TB units.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define units
        self.parameters[1] = "{0:02X}".format(units)



class SetAbsoluteTBInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetAbsoluteTBInit, self).__init__(pump)

        # Define code
        self.code = "4C"



class SetAbsoluteTB(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetAbsoluteTB, self).__init__(pump)

        # Define code
        self.code = "4C"

        # Define prelude command
        self.commands["Init"] = SetAbsoluteTBInit(pump)



    def encode(self, rate = 0, duration = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode rate (divide by pump stroke)
        rate = int(round(rate / self.pump.basal.stroke))

        # Encode duration (divide by time block)
        duration = int(round(duration / self.pump.basal.time))

        # Test rate
        lib.withinRangeInt(rate, [0, 1400], "Invalid TB rate.")

        # Test duration
        lib.withinRangeInt(duration, [0, 48], "Invalid TB duration.")

        # Define number of bytes to read from payload
        self.parameters = ["03"] + 64 * ["00"]

        # Define rate
        self.parameters[1:3] = ["{0:02X}".format(x) for x
                                                    in lib.pack(rate, n = 2)]

        # Define duration
        self.parameters[3] = "{0:02X}".format(duration)



class SetPercentageTBInit(Set):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPercentageTBInit, self).__init__(pump)

        # Define code
        self.code = "69"



class SetPercentageTB(Set, BigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPercentageTB, self).__init__(pump)

        # Define code
        self.code = "69"

        # Define prelude command
        self.commands["Init"] = SetPercentageTBInit(pump)



    def encode(self, rate = 0, duration = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode rate
        rate = int(round(rate))

        # Encode duration (divide by time block)
        duration = int(round(duration / self.pump.basal.time))

        # Test rate
        lib.withinRangeInt(rate, [0, 200], "Invalid TB rate.")

        # Test duration
        lib.withinRangeInt(duration, [0, 48], "Invalid TB duration.")

        # Define number of bytes to read from payload
        self.parameters = ["02"] + 64 * ["00"]

        # Define rate
        self.parameters[1] = "{0:02X}".format(rate)

        # Define duration
        self.parameters[2] = "{0:02X}".format(duration)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()