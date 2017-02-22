#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    commands

    Author:   David Leclerc

    Version:  0.1

    Date:     21.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is the entirety of commands available for the Carelink stick
              as well as the Medtronic MiniMed pump.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import lib
import requester
import decoder



# Instanciate a requester
Requester = requester.Requester()

# Instanciate a decoder
Decoder = decoder.Decoder()



# PUMP COMMANDS
class PumpCommand(object):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store pump
        self.pump = pump

        # Store recipient of command response
        self.recipient = recipient

        # Initialize request infos
        self.info = None
        self.packet = None
        self.remote = True
        self.sleep = 0
        self.power = 0
        self.attempts = None
        self.size = None
        self.code = None
        self.parameters = []



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare requester
        Requester.prepare(self.pump)

        # Define request
        Requester.define(info = self.info,
                         sleep = self.sleep,
                         power = self.power,
                         attempts = self.attempts,
                         size = self.size,
                         code = self.code,
                         parameters = self.parameters)

        # Update decoder's target
        Decoder.target = self.recipient



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump's response
        Decoder.decode(self.__class__.__name__, Requester.data)



    def do(self, decode = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make request
        Requester.make()

        # If decoding needed
        if decode:
            self.decode()



class PowerPump(PumpCommand):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, recipient)

        # Define request info
        self.info = ("Powering pump's radio transmitter for: " +
                     str(recipient.sessionTime) + "m")

        # Define request bytes
        self.sleep = recipient.powerTime
        self.power = 85
        self.attempts = 0
        self.size = 0
        self.code = 93
        self.parameters = [1, recipient.sessionTime]



class ReadPumpTime(PumpCommand):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, recipient)

        # Define request info
        self.info = "Reading pump time..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 112



class ReadPumpModel(PumpCommand):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, recipient)

        # Define request info
        self.info = "Reading pump model..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 141



class ReadPumpFirmware(PumpCommand):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, recipient)

        # Define request info
        self.info = "Reading pump firmware..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 116



class PushPumpButton(PumpCommand):

    def __init__(self, pump, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, recipient)

        # Define request info
        self.info = "Pushing button..."

        # Define request bytes
        self.attempts = 1
        self.size = 0
        self.code = 91



    def prepare(self, button):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request bytes
        self.parameters = [int(self.recipient.values[button])]
        
        # Prepare rest of command
        super(self.__class__, self).prepare()






# STICK COMMANDS
class StickCommand(object):

    def __init__(self, stick, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store stick
        self.stick = stick

        # Store recipient of command response
        self.recipient = recipient

        # Initialize request infos
        self.info = None
        self.packet = None
        self.remote = False
        self.sleep = 0
        self.power = None
        self.attempts = None
        self.size = None
        self.code = None
        self.parameters = None



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare requester
        Requester.prepare(self.stick)

        # Define request
        Requester.define(info = self.info,
                         packet = self.packet,
                         remote = self.remote)

        # Update decoder's target
        Decoder.target = self.recipient



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode stick's response
        Decoder.decode(self.__class__.__name__, Requester.response)



    def do(self, decode = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make request
        Requester.make()

        # If decoding needed
        if decode:
            self.decode()



class ReadStickSignalStrength(StickCommand):

    def __init__(self, stick, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, recipient)

        # Define request info
        self.info = "Reading stick signal strength..."

        # Define request packet
        self.packet = [6, 0, 0]



class ReadStickUSBState(StickCommand):

    def __init__(self, stick, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, recipient)

        # Define request info
        self.info = "Reading stick's radio state..."

        # Define request packet
        self.packet = [5, 0, 0]



class ReadStickRadioState(StickCommand):

    def __init__(self, stick, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, recipient)

        # Define request info
        self.info = "Reading stick's USB state..."

        # Define request packet
        self.packet = [5, 1, 0]



class ReadStickInfos(StickCommand):

    def __init__(self, stick, recipient):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, recipient)

        # Define request info
        self.info = "Reading stick's infos..."

        # Define request packet
        self.packet = [4, 0, 0]



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
