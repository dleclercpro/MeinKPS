#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    packets

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



# Instanciate logger
Logger = logger.Logger("CGM.packets")



# Packet statuses
STATUSES = {"NULL": 0,
            "ACK": 1,
            "NAK": 2,
            "INVALID_COMMAND": 3,
            "INVALID_PARAMETER": 4,
            "INCOMPLETE_PACKET_RECEIVED": 5,
            "RECEIVER_ERROR": 6,
            "INVALID_MODE": 7}



class Packet(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize packet
        self.bytes = None

        # Initialize packet characteristics
        self.size = None
        self.code = None
        self.database = None
        self.page = None



    def build(self, code, database, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            The format of a packet is:

            [0]:   ACK/NAK
            [1]:   PACKET SIZE
            [2]:   ???
            [3]:   OP CODE (COMMAND)
            [4]:   DATABASE INDEX
            [5]:   DATABASE PAGE
            [6-7]: CRC
        """

        # Build database byte
        if database is not None:
            database = [database]

        else:
            database = []

        # Build page bytes
        if page is not None:
            page = lib.pack(page, "<") + [0] * 4
            page = page[:4]
            page.append(1)

        else:
            page = []

        # Build packet
        self.bytes = [STATUSES["ACK"], 0, 0]
        self.bytes.append(code)
        self.bytes.extend(database)
        self.bytes.extend(page)

        # Build size byte
        size = len(self.bytes) + 2

        # Update packet
        self.bytes[1] = size

        # Build CRC bytes
        CRC = crc.compute(self.bytes)
        CRC = lib.pack(CRC, "<") + [0] * 2
        CRC = CRC[:2]

        # Finish packet
        self.bytes.extend(CRC)

        # Store packet characteristics
        self.size = size
        self.code = code
        self.database = database
        self.page = page



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return packet
        return self.bytes