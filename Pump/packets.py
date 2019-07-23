#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    packets

    Author:   David Leclerc

    Version:  0.1

    Date:     27.03.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that deals with the assembly, decoding and
              encoding of packets aimed at Medtronic MiniMed insulin pumps.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import math



# USER LIBRARIES
import lib
import logger
import errors



# CONSTANTS
# Packet conversion table
TABLE = ["010101", "110001", "110010", "100011", # 0 1 2 3
         "110100", "100101", "100110", "010110", # 4 5 6 7
         "011010", "011001", "101010", "001011", # 8 9 A B
         "101100", "001101", "001110", "011100"] # C D E F



# Instanciate logger
Logger = logger.Logger("Pump.packets")



# CLASSES
class Packet(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Initialize packet.
        """

        # Initialize characteristics
        self.type = None
        self.recipient = None
        self.payload = []
        self.CRC = None



class ToPacket(Packet):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(ToPacket, self).__init__()

        # Define packet type
        self.type = "TX"



class FromPacket(Packet):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(FromPacket, self).__init__()

        # Define packet type
        self.type = "RX"

        # Initialize characteristics due to CC1111 firmware
        self.index = None
        self.RSSI = None



    def rssi(self, offset = 73):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RSSI
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Convert hexadecimal RSSI reading to dBm.
        """

        # Get RSSI
        RSSI = self.RSSI["Hex"]

        # Info
        Logger.debug("RSSI (Byte): " + str(RSSI))

        # Bigger than
        if RSSI >= 128:

            # Value
            RSSI = (RSSI - 256) / 2.0

        # Otherwise
        else:

            # Value
            RSSI = RSSI / 2.0

        # Remove offset
        RSSI -= offset

        # Round value
        RSSI = round(RSSI)

        # Reassign it
        self.RSSI["dBm"] = RSSI

        # Info
        Logger.debug("RSSI (dBm): " + str(RSSI))



    def parse(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Parse incoming packet.
        """

        # Get packet index
        self.index = bytes[0]

        # Info
        Logger.debug("#: " + str(self.index))

        # Get RSSI reading
        self.RSSI = {"Hex": bytes[1], "dBm": None}

        # Compute RSSI
        self.rssi()



class PumpPacket(Packet):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(PumpPacket, self).__init__()

        # Initialize characteristics
        self.serial = []
        self.code = None
        self.size = None
        self.part = None

        # Initialize minimum size
        self.min = None

        # Initialize bytes in their various formats
        self.bytes = {"Encoded": [],
                      "Decoded": {"Hex": [],
                                  "Chr": [],
                                  "Int": []}}



    def format(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FORMAT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Convert decoded packet to various formats.
        """

        # Dehexify
        self.dehexify()

        # Charify
        self.charify()



    def dehexify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DEHEXIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Interpret decoded bytes in string format as hexadecimal values and
            store them.
        """

        # Convert string
        self.bytes["Decoded"]["Int"] = lib.dehexify(
            self.bytes["Decoded"]["Hex"])



    def charify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CHARIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Convert decoded bytes in string format to their ASCII values and
            store them.
        """

        # Convert string
        self.bytes["Decoded"]["Chr"] = lib.charify(
            self.bytes["Decoded"]["Int"])



    def showEncoded(self, n = 8):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWENCODED
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Show encoded bytes.
        """

        # Get size of packet
        size = len(self.bytes["Encoded"])

        # Compute number of exceeding bytes
        N = size % n

        # Define number of rows to print
        R = size / n + int(N != 0)

        # Info
        Logger.debug("Encoded bytes:")

        # Print formatted response
        for r in range(R):

            # Define range
            a, b = r * n, (r + 1) * n

            # Define row
            row = str(self.bytes["Encoded"][a:b])

            # Show response
            Logger.debug(row)



    def showDecoded(self, n = 8):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWDECODED
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Show decoded bytes in all formats.
        """

        # Get size of packet
        size = len(self.bytes["Decoded"]["Hex"])

        # Compute number of exceeding bytes
        N = size % n

        # Define number of rows to print
        R = size / n + int(N != 0)

        # Info
        Logger.debug("Decoded bytes:")

        # Print formatted response
        for r in range(R):

            # Define range
            a, b = r * n, (r + 1) * n

            # Define row in all formats
            rowHex = " ".join(self.bytes["Decoded"]["Hex"][a:b])
            rowChr = "".join(self.bytes["Decoded"]["Chr"][a:b])
            rowInt = str(self.bytes["Decoded"]["Int"][a:b])

            # On last row, some extra space may be needed for some formats
            if r == R - 1 and N != 0:

                # Define row
                rowHex += (n - N) * 3 * " "
                rowChr += (n - N) * " "

            # Build row
            row = rowHex + 3 * " " + rowChr + 3 * " " + rowInt

            # Show response
            Logger.debug(row)



    def show(self, encoded = False, decoded = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show characteristics
        Logger.debug("Type: " + str(self.type))
        Logger.debug("Recipient: " + str(self.recipient))
        Logger.debug("Serial: " + " ".join(self.serial))
        Logger.debug("Code: " + str(self.code))
        Logger.debug("Size: " + str(self.size))
        Logger.debug("Part: " + str(self.part))
        Logger.debug("Payload: " + " ".join(self.payload))
        Logger.debug("CRC: " + str(self.CRC))

        # Show its encoded version
        if encoded:
            self.showEncoded()

        # Show its decoded version
        if decoded:
            self.showDecoded()



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            This decodes a raw packet received by the CC1111. It converts
            received bytes to a long bit-string, then uses a given table and
            decodes every 6-bit word in said string, starting from the
            beginning.
        """

        # Convert bytes to long bit-string
        bits = "".join(["{:08b}".format(x) for x in self.bytes["Encoded"]])

        # Initialize string
        string = ""

        # Scan bits
        while bits:

            # Get 6-bits word and shorten rest of bits
            word, bits = bits[:6], bits[6:]

            # End-of-packet
            if word == "000000":

                # Exit
                break

            # Try converting
            try:

                # Decode word using conversion table (as hexadecimal value)
                word = TABLE.index(word)

                # Format it
                word = "{0:01X}".format(word)

                # Store word
                string += word

            # If error
            except ValueError:

                # If bits within packet
                if bits != "":
                    raise errors.CorruptedPumpPacket(word)

                # If last bits do not fit
                elif word != "0101":
                    raise errors.BadPumpPacketEnding(word)

        # Split string in groups of 2 characters
        self.bytes["Decoded"]["Hex"] = lib.split(string, 2)

        # Generate other formats as well
        self.format()



    def encode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ENCODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            This encodes a string packet to be sent using the CC1111. It uses
            the same encoding/decoding logic described in the decode function,
            only the other way around this time.
        """

        # Initialize bits
        bits = ""

        # Convert every character to its series of bits
        for x in "".join(self.bytes["Decoded"]["Hex"]):

            # Use table to convert it into bits and add them
            bits += TABLE[int(x, 16)]

        # Add mysterious last bits
        bits += "0101"

        # Get number of bits
        n = len(bits)

        # If number of bits not multiple of 8, encoding fails
        if n % 8 != 0:
            raise errors.MissingPumpPacketBits(n)

        # Initialize bytes
        bytes = []

        # Convert bits to bytes
        while bits:

            # Get byte and shorten rest of bits
            byte, bits = bits[:8], bits[8:]

            # Convert byte from binary to decimal value
            byte = int(byte, 2)

            # Store byte
            bytes.append(byte)

        # Store encoded packet
        self.bytes["Encoded"] = bytes

        # Generate other formats as well
        self.format()



class DecodedPumpPacket(PumpPacket):

    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(DecodedPumpPacket, self).__init__()

        # Store bytes
        self.bytes["Decoded"]["Hex"] = bytes

        # Encode them
        self.encode()



class EncodedPumpPacket(PumpPacket):

    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(EncodedPumpPacket, self).__init__()

        # Store bytes
        self.bytes["Encoded"] = bytes

        # Decode them
        self.decode()



class ToPumpPacket(ToPacket, PumpPacket):

    def __init__(self, code, payload):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(ToPumpPacket, self).__init__()

        # Define pump as packet recipient
        self.recipient = "A7"

        # Define pump serial number
        self.serial = ["79", "91", "63"]

        # Store code
        self.code = code

        # Store payload
        self.payload = payload

        # Assemble packet bytes
        self.assemble()



    def crc(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CRC
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Compute CRC of partial packet.
        """

        # Initialize pre-packet
        pkt = PumpPacket()

        # Define its bytes
        pkt.bytes["Decoded"]["Hex"] = bytes

        # Format it
        pkt.format()

        # Get its bytes in their decimal representation
        bytes = pkt.bytes["Decoded"]["Int"]

        # Compute corresponding CRC
        CRC = lib.computeCRC8(bytes)

        # Store its hexadecimal representation
        self.CRC = "{0:02X}".format(CRC)



    def assemble(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ASSEMBLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Assemble packet to send to pump.
        """

        # Initialize bytes
        bytes = []

        # Add recipient
        bytes.append(self.recipient)

        # Add serial
        bytes.extend(self.serial)

        # Add code
        bytes.append(self.code)

        # Add payload
        bytes.extend(self.payload)

        # Compute CRC
        self.crc(bytes)

        # Add it
        bytes.append(self.CRC)

        # Assign them
        self.bytes["Decoded"]["Hex"] = bytes

        # Encode them
        self.encode()



class FromPumpPacket(FromPacket, PumpPacket):

    def __init__(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        super(FromPumpPacket, self).__init__()

        # Define minimum number of bytes per packet
        self.min = 7

        # Parse decoded bytes
        self.parse(bytes)

        # Extract payload
        self.extract()



    def extract(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting byte
        a = self.min - 1

        # Define ending byte
        b = a + self.size

        # Get payload
        self.payload = self.bytes["Decoded"]["Hex"][a:b]



    def crc(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CRC
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify if computed CRC8 matches with the one received.
        """

        # Last byte should be CRC
        computedCRC = self.bytes["Decoded"]["Int"][-1]

        # Compute expected CRC using the rest
        expectedCRC = lib.computeCRC8(self.bytes["Decoded"]["Int"][:-1])

        # Verify CRC
        if computedCRC != expectedCRC:
            raise ValueError("Bad CRC (corrupted packet). Expected: " +
                str(expectedCRC) + ". Computed: " + str(computedCRC) + ".")

        # Return CRC
        return computedCRC



    def parse(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Parse packet coming in from pump.
        """

        # Initialize parsing
        super(FromPumpPacket, self).parse(bytes[:2])

        # Assign encoded bytes
        self.bytes["Encoded"] = bytes[2:]

        # Decode them
        self.decode()

        # Get number of bytes to parse
        n = len(self.bytes["Decoded"]["Hex"])

        # Not enough bytes
        if n < self.min:
            raise errors.NotEnoughPumpPacketBytes(self.min, n)

        # Get recipient
        self.recipient = self.bytes["Decoded"]["Hex"][0]

        # Packet not from pump
        if self.recipient != "A7":
            raise errors.UnknownPacketRecipient

        # Get serial
        self.serial = self.bytes["Decoded"]["Hex"][1:4]

        # Get op code
        self.code = self.bytes["Decoded"]["Hex"][4]

        # Get payload size
        self.size = self.bytes["Decoded"]["Int"][5]

        # Check and get CRC
        self.CRC = self.crc()



class FromPumpBigPacket(FromPumpPacket):

    def parse(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PARSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Parse packet coming in from pump.
        """

        # Initialize parsing
        super(FromPumpBigPacket, self).parse(bytes)

        # Get part
        self.part = self.bytes["Decoded"]["Int"][5]

        # Define payload size (without CRC and intro)
        self.size = 64



class FromPumpStatusPacket(FromPumpPacket):

    def extract(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXTRACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get payload in various formats
        self.payload = [self.bytes["Decoded"]["Hex"][5]]



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()