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

# LIBRARIES
import usb
import os
import time
import datetime



# USER LIBRARIES
import lib
import path
import logger
import errors
import commands
import databases
import reporter



# Define instances
Logger = logger.Logger("CGM/cgm.py")



class CGM(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define CGM characteristics
        self.vendor = 0x22A3
        self.product = 0x0047

        # Give CGM a USB interface
        self.usb = None

        # Initialize USB configuration
        self.config = None

        # Initialize data endpoints
        self.EPs = {"OUT": None,
                    "IN": None}

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

        # Define report
        self.report = reporter.REPORTS["cgm"]



    def start(self, ping = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Find it
        self.find()

        # Make sure kernel is not still active
        self.reset()

        # Configure it and get EPs
        self.configure()

        # If ping required
        if ping:

            # Ping it
            self.ping()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset CGM
        self.reset()



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Info
        Logger.info("Resetting CGM...")

        # Reset USB interface
        self.usb.reset()

        # If kernel still active
        if self.usb.is_kernel_driver_active(0):

            # Info
            Logger.warning("Detaching CGM kernel...")

            # Disconnect
            self.usb.detach_kernel_driver(0)



    def find(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Find and get USB interface of CGM.
        """

        # Find CGM
        self.usb = usb.core.find(idVendor = self.vendor,
                                 idProduct = self.product)

        # No CGM found
        if self.usb is None:

            # Raise error
            raise errors.NoCGM

        # Otherwise
        else:

            # Show it
            Logger.debug( "CGM found.")



    def configure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONFIGURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Configure the USB interface and assign EPs.
        """

        # Set configuration
        self.usb.set_configuration()

        # Get configuration
        self.config = self.usb.get_active_configuration()

        # Get EPs
        self.EPs["OUT"] = lib.getEP(self.config, "OUT", 1)
        self.EPs["IN"] = lib.getEP(self.config, "IN", 1)



    def ping(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PING
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Ping CGM to see if ready to receive commands.
        """

        # Try reading clock
        try:

            # Do it
            self.clock.read()

        # Otherwise
        except:

            # Reset USB ports
            os.system("sudo sh " + path.SRC + "reset.sh")

            # Wait until devices are back
            time.sleep(5)

            # Restart CGM (without ping)
            self.start(False)



    def write(self, bytes):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Sending packet: " + str(bytes))

        # Send packet
        self.EPs["OUT"].write(bytearray(bytes))



    def read(self, n = 64):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read raw bytes
        raw = self.EPs["IN"].read(n)

        # Convert raw bytes
        bytes = list(raw)

        # Give user info
        Logger.debug("Received bytes: " + str(bytes))

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
            To dump about 24 h of CGM readings: 8 pages (38 records per page,
            separated by 5 m intervals)
        """

        # Read BGs
        self.databases["BG"].read(n)



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

        # Define report type
        self.reportType = reporter.HistoryReport



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get current time
        self.t = datetime.datetime.now()

        # Execute command
        self.commands["ReadLevel"].execute()

        # Assign response
        self.level = lib.unpack(
            self.commands["ReadLevel"].response["Payload"], "<")

        # Give user info
        Logger.info("Battery level: " + str(self.level))

        # Execute command
        self.commands["ReadState"].execute()

        # Assign response
        self.state = self.states[lib.unpack(
            self.commands["ReadState"].response["Payload"], "<")]

        # Give user info
        Logger.info("Battery state: " + self.state)

        # Store battery level
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing battery level to: " + repr(self.reportType))

        # Add entry
        reporter.addDatedEntries(self.reportType, ["CGM", "Battery Levels"],
            { self.t: self.level })



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
        self.report = reporter.REPORTS["cgm"]



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute command
        self.command.execute()

        # Assign response
        self.value = self.values[lib.unpack(
            self.command.response["Payload"], "<")]

        # Give user info
        Logger.info("Language: " + self.value)

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing language to: " + repr(self.report))

        # Add entry
        self.report.add(self.value, ["Language"], True)



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
        self.report = reporter.REPORTS["cgm"]



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute command
        self.commands["ReadSystemTime"].execute()

        # Compute time delta since epoch
        delta = datetime.timedelta(seconds = lib.unpack(
            self.commands["ReadSystemTime"].response["Payload"], "<"))

        # Assign response
        self.systemTime = self.epoch + delta

        # Give user info
        Logger.info("System time: " + lib.formatTime(self.systemTime))

        # Execute command
        self.commands["ReadMode"].execute()

        # Assign response
        self.mode = self.modes[lib.unpack(
            self.commands["ReadMode"].response["Payload"], "<")]

        # Give user info
        Logger.info("Clock mode: " + self.mode)

        # Store clock mode
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing clock mode to: " + repr(self.report))

        # Add entry
        self.report.add(self.mode, ["Clock Mode"], True)



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
        self.report = reporter.REPORTS["cgm"]



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute command
        self.command.execute()

        # Assign response
        self.value = self.values[lib.unpack(
            self.command.response["Payload"], "<")]

        # Give user info
        Logger.info("Units: " + self.value)

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing BG units to: " + repr(self.report))

        # Add entry
        self.report.add(self.value, ["Units"], True)



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

        # Execute command
        self.commands["ReadHeader"].execute()

        # Execute command
        self.commands["ReadSettings"].execute()



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
        self.report = reporter.REPORTS["cgm"]



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Execute command
        self.command.execute()

        # Assign response
        self.id = lib.translate(self.command.response["Payload"])

        # Give user info
        Logger.info("Transmitter ID: " + str(self.id))

        # Store it
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Storing transmitter ID to: " + repr(self.report))

        # Add entry
        self.report.add(self.id, ["Transmitter ID"], True)



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