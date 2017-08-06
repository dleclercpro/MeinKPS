#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    cgm

    Author:   David Leclerc

    Version:  0.1

    Date:     08.03.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO: - reading BGs gets slow with time?



# LIBRARIES
import os
import sys
import datetime
import serial



# USER LIBRARIES
import lib
import commands
import databases
import reporter
import errors



# Define a reporter
Reporter = reporter.Reporter()



class CGM(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define CGM characteristics
        self.vendor = 0x22a3
        self.product = 0x0047

        # Define source path
        self.src = os.path.dirname(os.path.realpath(__file__)) + os.sep

        # Give CGM a handle
        self.handle = serial.Serial()

        # Give CGM a battery
        self.battery = Battery(self)

        # Give CGM a language
        self.language = Language(self)

        # Give CGM a clock
        self.clock = Clock(self)

        # Give CGM units
        self.units = Units(self)

        # Give CGM a firmware
        self.firmware = Firmware(self)

        # Give CGM a transmitter
        self.transmitter = Transmitter(self)

        # Give CGM databases
        self.databases = {"Manufacture": databases.ManufactureDatabase(self),
                          "Firmware": databases.FirmwareDatabase(self),
                          "PC": databases.PCDatabase(self),
                          "BG": databases.BGDatabase(self),
                          "Sensor": databases.SensorDatabase(self),
                          "Receiver": databases.ReceiverDatabase(self),
                          "Calibration": databases.CalibrationDatabase(self),
                          "Events": databases.EventsDatabase(self),
                          "Settings": databases.SettingsDatabase(self)}



    def connect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Plug CGM
        os.system("sudo sh " + self.src + "plug.sh")

        # Try opening port and define a handle
        try:

            # Define handle
            self.handle.port = "/dev/ttyACM0"
            self.handle.baudrate = 115200

            # Open handle
            self.handle.open()

        # Otherwise
        except serial.SerialException as e:

            # If CGM is missing
            if e.errno == 2:

                # Raise error
                raise errors.NoCGM

            # Otherwise
            else:

                # Everything should be fine
                pass



    def disconnect(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DISCONNECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Close handle
        self.handle.close()



    def ping(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PING
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Try reading battery
        try:

            # Read battery
            self.battery.read()

        # If failed, CGM is most probably in error/dead state
        except:

            # Give user info
            print "CGM seems to be dead. Resetting it..."

            # Power-cycle USB ports
            os.system("sudo sh " + self.src + "../reset.sh")

            # Reconnect
            self.connect()



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Connect CGM
        self.connect()

        # Ping CGM
        self.ping()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Disconnect CGM
        self.disconnect()



    def write(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Sending packet: " + str(bytes)

        # Send packet
        self.handle.write(bytearray(bytes))



    def read(self, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read raw bytes
        rawBytes = self.handle.read(n)

        # Convert raw bytes
        bytes = [ord(x) for x in rawBytes]

        # Give user info
        print "Received bytes: " + str(bytes)

        # Return response
        return bytes



    def dump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read battery
        self.battery.read()

        # Read language
        self.language.read()

        # Read clock
        self.clock.read()

        # Read units
        self.units.read()

        # Read firmware
        self.firmware.read()

        # Read transmitter
        self.transmitter.read()

        # Read databases
        self.databases["Manufacture"].read()
        self.databases["Firmware"].read()
        self.databases["PC"].read()
        self.databases["Sensor"].read()
        self.databases["Receiver"].read()
        self.databases["Calibration"].read()
        self.databases["Events"].read()
        self.databases["Settings"].read()

        # Read BGs
        self.databases["BG"].read()



    def dumpBG(self, n = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DUMPBG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read BGs
        self.databases["BG"].read(n)



    def dumpNewBG(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DUMPNEWBG
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Dump about 24 h of CGM readings (38 records per page separated by 5 m
        intervals)
        """

        # Read BGs
        self.dumpBG(8)



class Battery(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.t = None

        # Initialize battery level
        self.level = None

        # Initialize battery state
        self.state = None

        # Define battery states
        self.states = {1: "Charging",
                       2: "NotCharging",
                       3: "NTCFault",
                       4: "BadBattery"}

        # Define command(s)
        self.commands = {"ReadLevel": commands.ReadBatteryLevel(cgm),
                         "ReadState": commands.ReadBatteryState(cgm)}

        # Define report
        self.report = "history.json"



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current time
        self.t = datetime.datetime.now()

        # Link to command
        command = self.commands["ReadLevel"]

        # Execute command
        command.execute()

        # Assign response
        self.level = str(lib.unpack(command.response["Body"])) + "%"

        # Give user info
        print "Battery level: " + self.level

        # Link to battery state command
        command = self.commands["ReadState"]

        # Execute command
        command.execute()

        # Assign response
        self.state = self.states[lib.unpack(command.response["Body"])]

        # Give user info
        print "Battery state: " + self.state

        # Store battery level
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing BG units to report: '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, ["CGM", "Battery Levels"],
                     {self.t: self.level})



class Language(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Define languages
        self.values = {1029: "Czech",
                       1030: "Danish",
                       1031: "German",
                       1033: "English",
                       1034: "Spanish",
                       1035: "Finnish",
                       1036: "French (FR)",
                       1038: "Hungarian",
                       1040: "Italian",
                       1043: "Dutch",
                       1044: "Norwegian",
                       1045: "Polish",
                       1046: "Portuguese",
                       1053: "Swedish",
                       1055: "Turkish",
                       3084: "French (CA)"}

        # Define command(s)
        self.command = commands.ReadLanguage(cgm)

        # Define report
        self.report = "CGM.json"



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to command
        command = self.command

        # Execute command
        command.execute()

        # Assign response
        self.value = self.values[lib.unpack(command.response["Body"])]

        # Give user info
        print "Language: " + self.value

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing language to report: '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Language": self.value}, True)



class Clock(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize system time
        self.systemTime = None

        # Initialize mode
        self.mode = None

        # Define modes
        self.modes = {0: "24h", 1: "AM/PM"}

        # Define epoch
        self.epoch = datetime.datetime(2009, 1, 1)

        # Define command(s)
        self.commands = {"ReadSystemTime": commands.ReadSystemTime(cgm),
                         "ReadMode": commands.ReadClockMode(cgm)}

        # Define report
        self.report = "CGM.json"



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to command
        command = self.commands["ReadSystemTime"]

        # Execute command
        command.execute()

        # Compute time delta since epoch
        delta = datetime.timedelta(seconds = lib.unpack(command.response["Body"]))

        # Assign response
        self.systemTime = self.epoch + delta

        # Give user info
        print "System time: " + str(self.systemTime)

        # Link to command
        command = self.commands["ReadMode"]

        # Execute command
        command.execute()

        # Assign response
        self.mode = self.modes[lib.unpack(command.response["Body"])]

        # Give user info
        print "Clock mode: " + self.mode

        # Store clock mode
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing clock mode to report: '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Clock Mode": self.mode}, True)



class Units(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value to default
        self.value = "mmol/L"

        # Define values
        self.values = {1: "mg/dL", 2: "mmol/L"}

        # Define command(s)
        self.command = commands.ReadUnits(cgm)

        # Define report
        self.report = "CGM.json"



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to command
        command = self.command

        # Execute command
        command.execute()

        # Assign response
        self.value = self.values[lib.unpack(command.response["Body"])]

        # Give user info
        print "Units: " + self.value

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing BG units to report: '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Units": self.value}, True)



class Firmware(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define command(s)
        self.commands = {"ReadHeader": commands.ReadFirmwareHeader(cgm),
                         "ReadSettings": commands.ReadFirmwareSettings(cgm)}



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to command
        command = self.commands["ReadHeader"]

        # Execute command
        command.execute()

        # Link to command
        command = self.commands["ReadSettings"]

        # Execute command
        command.execute()



class Transmitter(object):

    def __init__(self, cgm):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize ID
        self.id = None

        # Define command(s)
        self.command = commands.ReadTransmitterID(cgm)

        # Define report
        self.report = "CGM.json"



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Link to command
        command = self.command

        # Execute command
        command.execute()

        # Assign response
        self.id = lib.translate(command.response["Body"])

        # Give user info
        print "Transmitter ID: " + str(self.id)

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Storing current transmitter ID to report: '" + self.report + "'..."

        # Add entry
        Reporter.add(self.report, [], {"Transmitter ID": self.id}, True)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate CGM
    cgm = CGM()

    # Start CGM
    cgm.start()

    # Dump data from CGM
    cgm.dump()

    # Stop CGM
    cgm.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
