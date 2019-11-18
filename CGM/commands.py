#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    commands

    Author:   David Leclerc

    Version:  0.1

    Date:     31.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import lib
import logger
import crc
import packets



# Instanciate logger
Logger = logger.Logger("CGM.commands")



class Command(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command code byte
        self.code = None

        # Initialize command database byte
        self.database = None

        # Initialize command page byte
        self.page = None

        # Initialize command response
        self.response = None

        # Give the command a packet
        self.packet = packets.Packet()

        # Link with CGM
        self.cgm = cgm



    def execute(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXECUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Command response packet format:

            [0-3]:     HEAD
            [4-531]:   PAYLOAD
            [532-533]: CRC
        """

        # Reset response
        self.response = {"Head": None,
                         "Payload": None,
                         "CRC": None}

        # Prepare packet
        self.packet.build(self.code, self.database, self.page)

        # Send packet
        self.cgm.write(self.packet.bytes)

        # Get response data
        data = self.cgm.read()

        # Check packet status
        status = data[0]

        # Packet OK
        if packets.STATUSES["ACK"] == status:

            # Compute size of packet to receive
            size = lib.unpack(data[1:3], "<")

            # Until whole data collected
            while len(data) != size:

                # Read more data
                data.extend(self.cgm.read())

            # Head
            self.response["Head"] = data[0:4]

            # Payload
            self.response["Payload"] = data[4:(size - 2)]

            # CRC
            self.response["CRC"] = data[-2:]

            # Verify response
            self.verifyCRC()

        # Otherwise
        else:
            raise IOError("Packet does not have an ACK status.")



    def verifyCRC(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFYCRC
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get and compute response CRCs
        expectedCRC = lib.unpack(self.response["CRC"], "<")
        computedCRC = crc.compute(self.response["Head"] +
            self.response["Payload"])

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:
            raise ValueError("Bad packet CRC. Expected: " + str(expectedCRC) +
                ". Computed: " + str(computedCRC) + ".")






class ReadDatabaseRange(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadDatabaseRange, self).__init__(cgm)
        self.code = 16



class ReadDatabase(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadDatabase, self).__init__(cgm)
        self.code = 17



class ReadFirmwareHeader(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadFirmwareHeader, self).__init__(cgm)
        self.code = 11



class ReadTransmitterID(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadTransmitterID, self).__init__(cgm)
        self.code = 25



class ReadFirmwareSettings(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadFirmwareSettings, self).__init__(cgm)
        self.code = 54



class ReadBatteryLevel(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadBatteryLevel, self).__init__(cgm)
        self.code = 33



class ReadBatteryState(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadBatteryState, self).__init__(cgm)
        self.code = 48



class ReadLanguage(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadLanguage, self).__init__(cgm)
        self.code = 27



class ReadSystemTime(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadSystemTime, self).__init__(cgm)
        self.code = 34



class ReadClockMode(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadClockMode, self).__init__(cgm)
        self.code = 41



class ReadUnits(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command
        super(ReadUnits, self).__init__(cgm)
        self.code = 37