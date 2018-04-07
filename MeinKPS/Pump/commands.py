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
import errors
import packets
import reporter



# Define a reporter
Reporter = reporter.Reporter()



# CLASSES
class Command(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize code
        self.code = None

        # Initialize report
        self.report = None

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
        self.data = {"TX": None,
                     "RX": None}



    def encode(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
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



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



    def run(self, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            When command runned, its core is executed, then the received data
            (if any) is decoded, and returned.
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






class StickCommand(Command):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(StickCommand, self).__init__()

        # Store stick instance
        self.stick = stick



class ReadStickName(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadStickName, self).__init__(stick)

        # Define code
        self.code = 0

        # Define report
        self.report = "stick.json"



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get data
        self.data["RX"] = self.stick.read()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode data
        self.response = "".join(lib.charify(self.data["RX"]))

        # Info
        print "Stick name: " + self.response



class ReadStickAuthor(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadStickAuthor, self).__init__(stick)

        # Define code
        self.code = 1

        # Define report
        self.report = "stick.json"



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get data
        self.data["RX"] = self.stick.read()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode data
        self.response = "".join(lib.charify(self.data["RX"]))

        # Info
        print "Stick author: " + self.response



class ReadStickRadioRegister(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadStickRadioRegister, self).__init__(stick)

        # Define code
        self.code = 10



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(ReadStickRadioRegister, self).reset()

        # Reset register
        self.register = None

        # Reset register address
        self.address = None



    def encode(self, register):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store register
        self.register = register

        # Get register address
        self.address = self.stick.registers.index(register)



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)

        # Send register address
        self.stick.write(self.address)



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get data
        self.data["RX"] = self.stick.read()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode data
        self.response = self.data["RX"][0]

        # Info
        print self.register + ": " + str(self.response)



class WriteStickRadioRegister(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(WriteStickRadioRegister, self).__init__(stick)

        # Define code
        self.code = 11



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(WriteStickRadioRegister, self).reset()

        # Reset register
        self.register = None

        # Reset register address
        self.address = None

        # Reset register value
        self.value = None



    def encode(self, register, value):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store register
        self.register = register

        # Get register address
        self.address = self.stick.registers.index(register)

        # Store register value
        self.value = value



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)

        # Send register address
        self.stick.write(self.address)

        # Send value
        self.stick.write(self.value)



class ReadStickRadio(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadStickRadio, self).__init__(stick)

        # Define code
        self.code = 20



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(ReadStickRadio, self).reset()

        # Reset channel
        self.channel = None

        # Reset timeout values
        self.timeout = None        



    def encode(self, channel = 0, timeout = 500, tolerate = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store channel
        self.channel = channel

        # Store timeout values
        self.timeout = {"Stick": timeout + 500,
                        "Radio": lib.pack(timeout, n = 4)}

        # Store error tolerance
        self.tolerate = tolerate



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)

        # Send channel
        self.stick.write(self.channel)

        # Send radio timeout
        self.stick.write(self.timeout["Radio"])



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try
        try:

            # Get data (remove EOP byte)
            self.data["RX"] = self.stick.read(timeout = self.timeout["Stick"],
                                              radio = True)[:-1]

        # If radio error
        except errors.RadioError:

            # Errors not tolerated
            if not self.tolerate:

                # Stop
                raise



class WriteStickRadio(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(WriteStickRadio, self).__init__(stick)

        # Define code
        self.code = 21



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(WriteStickRadio, self).reset()

        # Reset channel
        self.channel = None

        # Reset repeat count
        self.repeat = None

        # Reset repeat delay
        self.delay = None



    def encode(self, data, channel = 0, repeat = 0, delay = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store data
        self.data["TX"] = data

        # Store channel
        self.channel = channel

        # Store repeat count
        self.repeat = repeat

        # Store repeat delay
        self.delay = lib.pack(delay, n = 4)



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)

        # Send channel
        self.stick.write(self.channel)

        # Send delay
        self.stick.write(self.delay)

        # Send data
        self.stick.write(self.data["TX"])

        # Send last byte
        self.stick.write(0)



class WriteReadStickRadio(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(WriteReadStickRadio, self).__init__(stick)

        # Define code
        self.code = 22



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(WriteReadStickRadio, self).reset()

        # Reset channel values
        self.channel = None

        # Reset write repeat count
        self.repeat = None

        # Reset write repeat delay
        self.delay = None

        # Reset retry count
        self.retry = None

        # Reset timeout values
        self.timeout = None

        # Reset error tolerance
        self.tolerate = None



    def encode(self, data, channelTX = 0, channelRX = 0, repeat = 1, delay = 0,
                     retry = 1, timeout = 500, tolerate = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store data
        self.data["TX"] = data

        # Store channel values
        self.channel = {"TX": channelTX,
                        "RX": channelRX}

        # Store write repeat count
        self.repeat = repeat

        # Store write repeat delay
        self.delay = lib.pack(delay, n = 4)

        # Store retry count
        self.retry = retry

        # Store timeout values
        self.timeout = {"Stick": (retry + 1) * timeout + 500,
                        "Radio": lib.pack(timeout, n = 4)}

        # Store error tolerance
        self.tolerate = tolerate



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)

        # Send write channel
        self.stick.write(self.channel["TX"])

        # Send repeat count
        self.stick.write(self.repeat)

        # Send send repeat delay
        self.stick.write(self.delay)

        # Send read channel
        self.stick.write(self.channel["RX"])

        # Send radio timeout
        self.stick.write(self.timeout["Radio"])

        # Send retry count
        self.stick.write(self.retry)

        # Send packet
        self.stick.write(self.data["TX"])

        # Send last byte
        self.stick.write(0)



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try
        try:

            # Get data (remove EOP byte)
            self.data["RX"] = self.stick.read(timeout = self.timeout["Stick"],
                                              radio = True)[:-1]

        # If radio error
        except errors.RadioError:

            # Errors not tolerated
            if not self.tolerate:

                # Stop
                raise



class FlashStickLED(StickCommand):

    def __init__(self, stick):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(FlashStickLED, self).__init__(stick)

        # Define code
        self.code = 30



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Send command code
        self.stick.write(self.code)






class PumpCommand(Command):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PumpCommand, self).__init__()

        # Store pump instance
        self.pump = pump

        # Get its stick instance
        self.stick = pump.stick

        # Define function to generate send packet
        self.toPumpPacket = packets.ToPumpPacket



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize resetting
        super(PumpCommand, self).reset()

        # Reset data
        self.data = {"TX": [],
                     "RX": []}

        # Reset packets
        self.packets = {"TX": [],
                        "RX": []}

        # Reset parameters
        self.parameters = ["00"]



    def send(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Generate packet to send to pump
        pkt = self.toPumpPacket(self.code, self.parameters)

        # Store it
        self.packets["TX"].append(pkt)

        # Send encoded packet
        self.stick.commands["Radio TX/RX"].run(pkt.bytes["Encoded"])



    def receive(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECEIVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store data
        self.data["RX"].append(self.stick.commands["Radio TX/RX"].data["RX"])

        # Parse data into packet
        pkt = self.fromPumpPacket(self.data["RX"][-1])

        # Show it
        pkt.show()

        # Store it
        self.packets["RX"].append(pkt)



class PumpSetCommand(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PumpSetCommand, self).__init__(pump)

        # Define function to generate receive packet
        self.fromPumpPacket = packets.FromPumpACKPacket



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding
        super(PumpSetCommand, self).decode()

        # Get last packet
        pkt = self.packets["RX"][-1]

        # Define command ACK
        ack = [pkt.code] + pkt.payload

        # Unsuccessful
        if ack != ["06", "00"]:

            # Raise error
            raise errors.UnsuccessfulRadioCommand



class PumpGetCommand(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PumpGetCommand, self).__init__(pump)

        # Define function to generate receive packet
        self.fromPumpPacket = packets.FromPumpPacket



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last packet
        pkt = self.packets["RX"][-1]

        # Return payload in integer format for further decoding as well as its
        # size
        return [lib.dehexify(pkt.payload), pkt.size]



class PumpGetBigCommand(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PumpGetBigCommand, self).__init__(pump)

        # Define function to generate receive packet
        self.fromPumpPacket = packets.FromPumpBigPacket



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Warning: This will only work when class instanciated alongside of
                     PumpBigCommand.
        """

        # Get last packets (without prelude)
        pkts = self.packets["RX"][self.repeat["Prelude"]:]

        # Flatten payloads to one larger one
        payload = lib.dehexify(lib.flatten([pkt.payload for pkt in pkts]))

        # Return it for further decoding as well as its size
        return [payload, len(payload)]



class PumpBigCommand(PumpCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PumpBigCommand, self).__init__(pump)

        # Define number of times pre-/postlude commands need to be executed
        self.repeat = {"Prelude": 1,
                       "Postlude": 0}

        # Define pre- and postlude commands
        self.commands = {"Prelude": None,
                         "Postlude": ReadPumpMore(pump)}



    def prelude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PRELUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get prelude command
        cmd = self.commands["Prelude"]

        # Run prelude command given number of times
        for i in range(self.repeat["Prelude"]):

            # Do it
            cmd.run()

            # Store response packet
            self.packets["RX"].append(cmd.packets["RX"][-1])



    def postlude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            POSTLUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get postlude command
        cmd = self.commands["Postlude"]

        # Run postlude command given number of times
        for i in range(self.repeat["Postlude"]):

            # Do it
            cmd.run()

            # Store response packet
            self.packets["RX"].append(cmd.packets["RX"][-1])



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



class PowerPumpPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PowerPumpPrelude, self).__init__(pump)

        # Define code
        self.code = "5D"



class PowerPump(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PowerPump, self).__init__(pump)

        # Define code
        self.code = "5D"

        # Define report
        self.report = "pump.json"

        # Define prelude command
        self.commands["Prelude"] = PowerPumpPrelude(pump)

        # Define prelude command repeat counts
        self.repeat["Prelude"] = 50



    def prelude(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PRELUDE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute a given number of times
        for i in range(self.repeat["Prelude"]):

            # Try
            try:

                # Execute
                self.commands["Prelude"].run()

                # Exit
                return

            # Except
            except (errors.RadioError, errors.InvalidPacket):

                # Ignore
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
        lib.checkIntWithinRange(t, [0, 30], "Invalid RF session length.")

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

        # Give user info
        print "Adding pump's last power up to '" + self.report + "'..."

        # Get current formatted time
        now = lib.formatTime(datetime.datetime.now())

        # Add entry
        Reporter.add(self.report, [], {"Power": now}, True)



class ReadPumpTime(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpTime, self).__init__(pump)

        # Define code
        self.code = "70"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpTime, self).decode()

        # Destructure
        [h, m, s, Y1, Y2, M, D] = payload[0:7]

        # Unpack year
        Y = lib.unpack([Y1, Y2])

        # Store formatted time
        self.response = lib.formatTime(datetime.datetime(Y, M, D, h, m, s))



class ReadPumpModel(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpModel, self).__init__(pump)

        # Define code
        self.code = "8D"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpModel, self).decode()

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

        # Give user info
        print "Adding pump's model to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Properties"],
                                  {"Model": self.response}, True)



class ReadPumpFirmware(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpFirmware, self).__init__(pump)

        # Define code
        self.code = "74"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpFirmware, self).decode()

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

        # Give user info
        print "Adding pump's firmware to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Properties"],
                                  {"Firmware": self.response}, True)



class ReadPumpBattery(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBattery, self).__init__(pump)

        # Define code
        self.code = "72"

        # Define report
        self.report = "history.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpBattery, self).decode()

        # Decode
        self.response = round(lib.unpack(payload[1:3]) / 100.0, 2)



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
        Reporter.add(self.report, ["Pump", "Battery Levels"],
                                  {now: self.response})



class ReadPumpReservoir(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpReservoir, self).__init__(pump)

        # Define code
        self.code = "73"

        # Define report
        self.report = "history.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpReservoir, self).decode()

        # Decode
        self.response = round(lib.unpack(payload[0:2]) * self.pump.bolus.stroke,
                              1)



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
        Reporter.add(self.report, ["Pump", "Reservoir Levels"],
                                  {now: self.response})



class ReadPumpStatus(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpStatus, self).__init__(pump)

        # Define code
        self.code = "CE"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpStatus, self).decode()

        # Decode
        self.response = {"Normal": payload[0] == 3,
                         "Bolusing": payload[1] == 1,
                         "Suspended": payload[2] == 1}



class ReadPumpSettings(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpSettings, self).__init__(pump)

        # Define code
        self.code = "C0"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpSettings, self).decode()

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

        # Give user info
        print "Adding pump's settings to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Settings": self.response}, True)



class ReadPumpBGUnits(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBGUnits, self).__init__(pump)

        # Define code
        self.code = "89"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpBGUnits, self).decode()

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

        # Give user info
        print "Adding pump's BG units to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Units"], {"BG": self.response}, True)



class ReadPumpCarbsUnits(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpCarbsUnits, self).__init__(pump)

        # Define code
        self.code = "88"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpCarbsUnits, self).decode()

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

        # Give user info
        print "Adding pump's carb units to '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["Units"], {"Carbs": self.response}, True)



class ReadPumpBGTargets(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBGTargets, self).__init__(pump)

        # Define code
        self.code = "9F"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpBGTargets, self).decode()

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

        # Give user info
        print "Adding pump's BG targets to '" + self.report + "'..."

        # Store BG units
        Reporter.add(self.report, ["Units"],
                                  {"BG": self.response["Units"]}, True)

        # Zip times and targets
        response = dict(zip(self.response["Times"], self.response["Targets"]))

        # Store targets
        Reporter.add(self.report, [], {"BG Targets": response}, True)



class ReadPumpFactors(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpFactors, self).__init__(pump)

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpFactors, self).decode()

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



class ReadPumpISF(ReadPumpFactors):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpISF, self).__init__(pump)

        # Define code
        self.code = "8B"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpISF, self).decode()

        # Decode units
        # mg/dL
        if payload[0] == 1:

            # Store them
            self.response["Units"] = "mg/dL/U"

        # mmol/L
        elif payload[0] == 2:

            # Store them
            self.response["Units"] = "mmol/L/U"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's ISF(s) to '" + self.report + "'..."

        # Store BG units (without insulin units)
        Reporter.add(self.report, ["Units"],
                                  {"BG": self.response["Units"][:-2]}, True)

        # Zip times and factors
        response = dict(zip(self.response["Times"], self.response["Factors"]))

        # Store factors
        Reporter.add(self.report, [], {"ISF": response}, True)



class ReadPumpCSF(ReadPumpFactors):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpCSF, self).__init__(pump)

        # Define code
        self.code = "8A"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpCSF, self).decode()

        # Decode units
        # mg/dL
        if payload[0] == 1:

            # Store them
            self.response["Units"] = "g/U"

        # mmol/L
        elif payload[0] == 2:

            # Store them
            self.response["Units"] = "U/exchange"



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding pump's CSF(s) to '" + self.report + "'..."

        # Zip times and factors
        response = dict(zip(self.response["Times"], self.response["Factors"]))

        # Store factors
        Reporter.add(self.report, [], {"CSF": response}, True)

        # Update units for carbs (without insulin units)
        # g/U
        if self.response["Units"] == "g/U":

            # Define units
            units = self.response["Units"][0]

        # U/exchange
        elif self.response["Units"] == "U/exchange":

            # Define units
            units = self.response["Units"][2:]

        # Store carb units
        Reporter.add(self.report, ["Units"], {"Carbs": units}, True)



class ReadPumpBasalProfile(PumpBigCommand, PumpGetBigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBasalProfile, self).__init__(pump)

        # Define report
        self.report = "pump.json"

        # Define profile name
        self.name = None

        # Define pre- and postlude command repeat count
        self.repeat["Prelude"] = 0
        self.repeat["Postlude"] = 1



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get whole payload
        [payload, size] = super(ReadPumpBasalProfile, self).decode()

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

                # Exit
                break

            # No more data in payload
            if sum(entry) == 0 or len(entry) != length:

                # Exit
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

        # Give user info
        print ("Adding pump's basal profile '" + self.name + "' to '" + 
               self.report + "'...")

        # Zip times and rates
        response = dict(zip(self.response["Times"], self.response["Rates"]))

        # Store basal
        Reporter.add(self.report, [], {"Basal Profile (" + self.name + ")":
                                       response}, True)



class ReadPumpBasalProfileStandard(ReadPumpBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBasalProfileStandard, self).__init__(pump)

        # Define code
        self.code = "92"

        # Define profile name
        self.name = "Standard"



class ReadPumpBasalProfileA(ReadPumpBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBasalProfileA, self).__init__(pump)

        # Define code
        self.code = "93"

        # Define profile name
        self.name = "A"



class ReadPumpBasalProfileB(ReadPumpBasalProfile):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpBasalProfileB, self).__init__(pump)

        # Define code
        self.code = "94"

        # Define profile name
        self.name = "B"



class ReadPumpDailyTotals(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpDailyTotals, self).__init__(pump)

        # Define code
        self.code = "79"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpDailyTotals, self).decode()

        # Decode
        self.response = {"Today": round(lib.unpack(payload[0:2]) *
                                        self.pump.bolus.stroke, 2),
                         "Yesterday": round(lib.unpack(payload[2:4]) *
                                            self.pump.bolus.stroke, 2)}



class ReadPumpTB(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpTB, self).__init__(pump)

        # Define code
        self.code = "98"

        # Define report
        self.report = "pump.json"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpTB, self).decode()

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

        # Give user info
        print "Adding pump's TB units to '" + self.report + "'..."

        # Store TB units
        Reporter.add(self.report, ["Units"],
                                  {"TB": self.response["Units"]}, True)



class ReadPumpHistorySize(PumpGetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpHistorySize, self).__init__(pump)

        # Define code
        self.code = "9D"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpHistorySize, self).decode()

        # Decode (max 36 pages)
        self.response = min(payload[3] + 1, 36)



class ReadPumpHistoryPagePrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpHistoryPagePrelude, self).__init__(pump)

        # Define code
        self.code = "80"



class ReadPumpHistoryPage(PumpBigCommand, PumpGetBigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpHistoryPage, self).__init__(pump)

        # Define code
        self.code = "80"

        # Define prelude command
        self.commands["Prelude"] = ReadPumpHistoryPagePrelude(pump)

        # Define postlude command repeat count
        self.repeat["Postlude"] = 14



    def encode(self, page = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Test page number
        lib.checkIntWithinRange(page, [0, 35], "Invalid history page number.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define page
        self.parameters[1] = "{0:02X}".format(page)



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize decoding and get payload
        [payload, size] = super(ReadPumpHistoryPage, self).decode()

        # Set response to payload
        self.response = payload



class ReadPumpMore(PumpGetBigCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ReadPumpMore, self).__init__(pump)

        # Define code
        self.code = "06"



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Ignore
        pass



class PushPumpButtonPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PushPumpButtonPrelude, self).__init__(pump)

        # Define code
        self.code = "5B"



class PushPumpButton(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(PushPumpButton, self).__init__(pump)

        # Define code
        self.code = "5B"

        # Define prelude command
        self.commands["Prelude"] = PushPumpButtonPrelude(pump)



    def encode(self, button = "DOWN"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try
        try:

            # Get button corresponding byte
            button = ["EASY", "ESC", "ACT", "UP", "DOWN"].index(button)

        # Except
        except ValueError:

            # Raise error
            raise IOError("Bad button.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define button
        self.parameters[1] = "{0:02X}".format(button)



class ResumePumpPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ResumePumpPrelude, self).__init__(pump)

        # Define code
        self.code = "4D"



class ResumePump(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(ResumePump, self).__init__(pump)

        # Define code
        self.code = "4D"

        # Define prelude command
        self.commands["Prelude"] = ResumePumpPrelude(pump)



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



class SuspendPumpPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SuspendPumpPrelude, self).__init__(pump)

        # Define code
        self.code = "4D"



class SuspendPump(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SuspendPump, self).__init__(pump)

        # Define code
        self.code = "4D"

        # Define prelude command
        self.commands["Prelude"] = SuspendPumpPrelude(pump)



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



class DeliverPumpBolusPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(DeliverPumpBolusPrelude, self).__init__(pump)

        # Define code
        self.code = "42"



class DeliverPumpBolus(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(DeliverPumpBolus, self).__init__(pump)

        # Define code
        self.code = "42"

        # Define prelude command
        self.commands["Prelude"] = DeliverPumpBolusPrelude(pump)



    def encode(self, bolus = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode bolus
        bolus *= 10.0

        # Test bolus
        lib.checkIntWithinRange(bolus, [0, 250], "Invalid bolus.")

        # Convert bolus to integer
        bolus = int(bolus)

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define bolus
        self.parameters[1] = "{0:02X}".format(bolus)



class SetPumpTBUnitsPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpTBUnitsPrelude, self).__init__(pump)

        # Define code
        self.code = "68"



class SetPumpTBUnits(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpTBUnits, self).__init__(pump)

        # Define code
        self.code = "68"

        # Define prelude command
        self.commands["Prelude"] = SetPumpTBUnitsPrelude(pump)



    def encode(self, units = "U/h"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try
        try:

            # Get unit corresponding byte
            units = ["U/h", "%"].index(units)

        # Except
        except ValueError:

            # Raise error
            raise IOError("Bad TB units.")

        # Define number of bytes to read from payload
        self.parameters = ["01"] + 64 * ["00"]

        # Define units
        self.parameters[1] = "{0:02X}".format(units)



class SetPumpAbsoluteTBPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpAbsoluteTBPrelude, self).__init__(pump)

        # Define code
        self.code = "4C"



class SetPumpAbsoluteTB(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpAbsoluteTB, self).__init__(pump)

        # Define code
        self.code = "4C"

        # Define prelude command
        self.commands["Prelude"] = SetPumpAbsoluteTBPrelude(pump)



    def encode(self, rate = 0, duration = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode rate (divide by pump stroke)
        rate = int(round(rate / 0.025))

        # Encode duration (divide by time block)
        duration = int(duration / 30.0)

        # Test rate
        lib.checkIntWithinRange(rate, [0, 1400], "Invalid TB rate.")

        # Test duration
        lib.checkIntWithinRange(duration, [0, 48], "Invalid TB duration.")

        # Define number of bytes to read from payload
        self.parameters = ["03"] + 64 * ["00"]

        # Define rate
        self.parameters[1:3] = ["{0:02X}".format(x) for x
                                                    in lib.pack(rate, n = 2)]

        # Define duration
        self.parameters[3] = "{0:02X}".format(duration)



class SetPumpPercentageTBPrelude(PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpPercentageTBPrelude, self).__init__(pump)

        # Define code
        self.code = "69"



class SetPumpPercentageTB(PumpBigCommand, PumpSetCommand):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(SetPumpPercentageTB, self).__init__(pump)

        # Define code
        self.code = "69"

        # Define prelude command
        self.commands["Prelude"] = SetPumpPercentageTBPrelude(pump)



    def encode(self, rate = 0, duration = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Encode rate
        rate = int(round(rate))

        # Encode duration (divide by time block)
        duration = int(duration / 30.0)

        # Test rate
        lib.checkIntWithinRange(rate, [0, 200], "Invalid TB rate.")

        # Test duration
        lib.checkIntWithinRange(duration, [0, 48], "Invalid TB duration.")

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