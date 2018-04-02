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

# LIBRARIES
import sys



# USER LIBRARIES
import lib
import packets



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
        """

        # Reset response
        self.response = {"Head": None,
                         "Payload": None,
                         "CRC": None}

        # Prepare packet
        self.packet.build(self.code, self.database, self.page)

        # Send packet
        self.cgm.write(self.packet.bytes)

        # Get data
        data = self.cgm.read()

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

        # Try and find XML structure in response
        print "XML: " + str(lib.XMLify(self.response["Payload"]))

        # Verify response
        self.verify()



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get and compute response CRCs
        expectedCRC = lib.unpack(self.response["CRC"], "<")
        computedCRC = lib.computeCRC16(self.response["Head"] +
                                       self.response["Payload"])

        # Give user info
        print "Expected CRC: " + str(expectedCRC)
        print "Computed CRC: " + str(computedCRC)

        # Exit if CRCs mismatch
        if computedCRC != expectedCRC:

            # Give user info
            sys.exit("Expected and computed CRCs do not match. Exiting...")



class ReadDatabaseRange(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 16



class ReadDatabase(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 17



class ReadFirmwareHeader(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 11



class ReadTransmitterID(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 25



class ReadFirmwareSettings(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 54



class ReadBatteryLevel(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 33



class ReadBatteryState(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 48



class ReadLanguage(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 27



class ReadSystemTime(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 34



class ReadClockMode(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 41



class ReadUnits(Command):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(cgm)

        # Initialize command code
        self.code = 37