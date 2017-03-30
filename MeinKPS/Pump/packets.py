#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    packets

    Author:   David Leclerc

    Version:  0.1

    Date:     29.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import lib



class Packet(object):

    def __init__(self, command):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet characteristics
        self.bytes = None
        self.code = None

        # Link with command
        self.command = command



    def set(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Set packet
        self.bytes = bytes



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet bytes
        self.bytes = []



class StickPacket(Packet):

    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet
        self.reset()

        # Build packet
        self.bytes.extend(self.code)
        self.bytes.extend([0, 0, 0])

        # Packet length is always 3 bytes
        self.bytes = self.bytes[:3]



class PumpPacket(Packet):

    def __init__(self, command):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(command)

        # Initialize packet type
        self.type = None

        # Initialize packet parameters
        self.parameters = []

        # Define typical packet bytes
        self.serial = 503593 # 799163
        self.power = 0
        self.attempts = 2
        self.size = 1



    def build(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset packet
        self.reset()

        # Poll packet
        if self.type == "Poll":

            # Build packet
            self.bytes.extend([3, 0, 0])

        # Download packet
        elif self.type == "Download":

            # Build packet
            self.bytes.extend([12, 0])
            self.bytes.append(lib.getByte(self.command.nBytesExpected, 1))
            self.bytes.append(lib.getByte(self.command.nBytesExpected, 0))

            # Compute and add packet CRC
            self.bytes.append(lib.computeCRC8(self.bytes))

        # Normal packet
        else:

            # Build packet
            self.bytes.extend([1, 0, 167, 1])
            self.bytes.extend(lib.encode(self.serial))
            self.bytes.append(128 | lib.getByte(len(self.parameters), 1))
            self.bytes.append(lib.getByte(len(self.parameters), 0))
            self.bytes.append(self.power)
            self.bytes.append(self.attempts)
            self.bytes.append(self.size)
            self.bytes.append(0)
            self.bytes.append(self.code)

            # Compute and add packet CRC
            self.bytes.append(lib.computeCRC8(self.bytes))

            # Build packet
            self.bytes.extend(self.parameters)

            # Compute and add parameters CRC
            self.bytes.append(lib.computeCRC8(self.parameters))



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
