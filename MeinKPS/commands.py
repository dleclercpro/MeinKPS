#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    commands

    Author:   David Leclerc

    Version:  0.1

    Date:     21.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a collection of commands available for the Carelink stick
              as well as the Medtronic MiniMed pumps.

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

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store pump
        self.pump = pump

        # Store target of command response
        self.target = target

        # Initialize request info and bytes
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

        # Update decoder's device
        Decoder.device = self.pump

        # Update decoder's target
        Decoder.target = self.target



    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decode pump's data
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



    def get(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Return data stored on requester
        return Requester.data



class PowerPump(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Powering pump's radio transmitter..."

        # Define request bytes
        self.sleep = target.powerTime
        self.power = 85
        self.attempts = 0
        self.size = 0
        self.code = 93
        self.parameters = [1, target.sessionTime]



class ReadPumpTime(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's time..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 112



class ReadPumpModel(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's model..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 141



class ReadPumpFirmware(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's firmware..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 116



class PushPumpButton(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

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

        # Define rest of request bytes
        self.parameters = [int(self.target.values[button])]
        
        # Prepare rest of command
        super(self.__class__, self).prepare()



class ReadPumpBattery(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's battery..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 114



class ReadPumpReservoir(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's reservoir..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 115



class ReadPumpStatus(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's status..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 206



class SuspendPump(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Suspending pump..."

        # Define request bytes
        self.sleep = pump.executionDelay
        self.attempts = 2
        self.size = 1
        self.code = 77
        self.parameters = [1]



class ResumePump(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Resuming pump..."

        # Define request bytes
        self.sleep = pump.executionDelay
        self.attempts = 2
        self.size = 1
        self.code = 77
        self.parameters = [0]



class ReadPumpSettings(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's settings..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 192



class ReadPumpBGUnits(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's BG units..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 137



class ReadPumpBGUnits(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's BG units..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 137



class ReadPumpCUnits(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's C units..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 136



class SetPumpTBRUnits(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Setting pump's TBR units..."

        # Define request bytes
        self.sleep = pump.executionDelay
        self.attempts = 0
        self.size = 1
        self.code = 104



    def prepare(self, units):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If request is for absolute TBR
        if units == "U/h":
            self.parameters = [0]

        # If request is for TBR in percentage
        elif units == "%":
            self.parameters = [1]
        
        # Prepare rest of command
        super(self.__class__, self).prepare()



class ReadPumpBGTargets(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's BG targets..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 159



class ReadPumpISF(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's ISF..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 139



class ReadPumpCSF(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's CSF..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 138



class ReadPumpDailyTotals(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading pump's daily totals..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 121



class EvaluatePumpHistory(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading number of pump history pages..."

        # Define request bytes
        self.attempts = 2
        self.size = 1
        self.code = 157



class ReadPumpHistory(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request info
        self.info = "Reading number of pump history pages..."

        # Define request bytes
        self.attempts = 2
        self.size = 2
        self.code = 128



    def prepare(self, page):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        self.info = "Reading pump history page: " + str(page)

        # Define rest of bytes
        self.parameters = [page]
        
        # Prepare rest of command
        super(self.__class__, self).prepare()



class DeliverPumpBolus(PumpCommand):

    def __init__(self, pump, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(pump, target)

        # Define request bytes
        self.attempts = 0
        self.size = 1
        self.code = 66



    def prepare(self, bolus, stroke, time):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request info
        self.info = "Sending bolus: " + str(bolus) + " U"

        # Define rest of bytes
        self.sleep = time
        self.parameters = [int(bolus / stroke)]
        
        # Prepare rest of command
        super(self.__class__, self).prepare()





# STICK COMMANDS
class StickCommand(object):

    def __init__(self, stick, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store stick
        self.stick = stick

        # Store target of command response
        self.target = target

        # Initialize request info and bytes
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

        # Update decoder's device
        Decoder.device = self.stick

        # Update decoder's target
        Decoder.target = self.target



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

    def __init__(self, stick, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, target)

        # Define request info
        self.info = "Reading stick signal strength..."

        # Define request packet
        self.packet = [6, 0, 0]



class ReadStickUSBState(StickCommand):

    def __init__(self, stick, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, target)

        # Define request info
        self.info = "Reading stick's radio state..."

        # Define request packet
        self.packet = [5, 0, 0]



class ReadStickRadioState(StickCommand):

    def __init__(self, stick, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, target)

        # Define request info
        self.info = "Reading stick's USB state..."

        # Define request packet
        self.packet = [5, 1, 0]



class ReadStickInfos(StickCommand):

    def __init__(self, stick, target):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize command
        super(self.__class__, self).__init__(stick, target)

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
