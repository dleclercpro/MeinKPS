#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    stick

    Author:   David Leclerc

    Version:  0.1

    Date:     27.03.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This script defines a Stick object, which can be used to
              communicate with a Medtronic MiniMed insulin pump, using a Texas
              Instruments CC1111 USB radio stick. It is based on the PyUSB
              library as well as the reverse-engineering of the Carelink USB
              stick from Medtronic.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import usb
import os
import time
import datetime
import numpy as np



# USER LIBRARIES
import lib
import fmt
import logger
import errors
import path
import reporter
import commands
from Pump import packets



# Define instances
Logger = logger.Logger("Stick.stick")



# CONSTANTS
N_WARNINGS = 10



# CLASSES
class Stick(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Initialize stick properties.
        """

        # Define USB IDs
        self.vendor = 0x0451
        self.product = 0x16A7

        # Initialize USB interface
        self.usb = None

        # Initialize USB configuration
        self.config = None

        # Initialize data endpoints
        self.EPs = {"OUT": None,
                    "IN": None}

        # Define frequencies (MHz)
        self.f = {"Reference": 24.0,
                  "Regions": {"NA": {"Default": 916.665,
                                     "Range":  [916.500, 916.800]},
                              "WW": {"Default": 868.330,
                                     "Range":  [868.150, 868.750]}}}

        # Define radio errors
        self.errors = {0xAA: "Timeout",
                       0xBB: "No data",
                       0xCC: "Interrupted"}

        # Define commands
        self.commands = {"Name RX": commands.ReadName(self),
                         "Author RX": commands.ReadAuthor(self),
                         "Radio Register RX": commands.ReadRadioRegister(self),
                         "Radio Register TX": commands.WriteRadioRegister(self),
                         "Radio RX": commands.ReadRadio(self),
                         "Radio TX": commands.WriteRadio(self),
                         "Radio TX/RX": commands.WriteReadRadio(self),
                         "LED Toggle": commands.ToggleLED(self),
                         "LED On": commands.TurnOnLED(self),
                         "LED Off": commands.TurnOffLED(self)}

        # Define radio registers
        self.registers = ["SYNC1", "SYNC0",
                          "PKTLEN", "PKTCTRL1", "PKTCTRL0",
                          "ADDR",
                          "FSCTRL1", "FSCTRL0",
                          "MDMCFG4", "MDMCFG3", "MDMCFG2", "MDMCFG1", "MDMCFG0",
                          "DEVIATN",
                          "MCSM2", "MCSM1", "MCSM0",
                          "BSCFG",
                          "FOCCFG",
                          "FREND1", "FREND0",
                          "FSCAL3", "FSCAL2", "FSCAL1", "FSCAL0",
                          "TEST1", "TEST0",
                          "PA_TABLE1", "PA_TABLE0",
                          "AGCCTRL2", "AGCCTRL1", "AGCCTRL0",
                          "FREQ2", "FREQ1", "FREQ0",
                          "CHANNR"]

        # Define report
        self.report = reporter.REPORTS["stick"]



    def start(self, ping = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Starting procedure for stick.
        """

        # Find it
        self.find()

        # Configure it
        self.configure()

        # If ping required
        if ping:
            self.ping()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        pass



    def switchLED(self, mode):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SWITCHLED
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Shortcut to private command method turning LED on/off.
        """

        # Turn on LED
        if mode == "ON":
            self.commands["LED On"].run()

        # Turn off LED
        elif mode == "OFF":
            self.commands["LED Off"].run()

        # Otherwise
        else:
            raise ValueError("Incorrect LED mode.")



    def flash(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FLASH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Flash LED.
        """

        # Switch LED
        self.commands["LED Toggle"].run()

        # Wait
        time.sleep(1)

        # Re-switch LED
        self.commands["LED Toggle"].run()

        # Wait
        time.sleep(1)



    def warn(self, n = N_WARNINGS):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WARN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Warn user with the stick's LED.
        """

        # Turn LED off first
        self.commands["LED Off"].run()

        # Warn 10 times
        for i in range(n):

            # Info
            Logger.debug("Stick LED warning: " + str(i + 1) + "/" + str(n))
            
            # Flash LED
            self.flash()



    def find(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Find the stick on the USB bus and link it.
        """

        # Find stick
        self.usb = usb.core.find(idVendor = self.vendor,
                                 idProduct = self.product)

        # No stick found
        if self.usb is None:
            raise errors.NoStick

        # Info
        Logger.debug("Stick found.")



    def configure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CONFIGURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Configure the USB interface and assign EPs.
        """

        # Reset USB interface
        self.usb.reset()

        # Set configuration
        self.usb.set_configuration()

        # Get configuration
        self.config = self.usb.get_active_configuration()

        # Get EPs
        self.EPs["OUT"] = lib.getEP(self.config, "OUT")
        self.EPs["IN"] = lib.getEP(self.config, "IN")



    def ping(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PING
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Ping stick to see if ready to receive commands.
        """

        # Try getting stick name
        try:

            # Do it
            self.commands["Name RX"].run()

        # Radio error
        except errors.RadioError:

            # Retry (last try should have brought the radio out of the reading
            # loop)
            self.commands["Name RX"].run()

        # Otherwise
        except:

            # Info
            Logger.warning("Resetting USB interface...")

            # Reset USB ports
            os.system("sudo sh " + path.SRC + "reset.sh")

            # Wait until devices are back
            time.sleep(5)

            # Restart stick
            self.start(False)



    def write(self, bytes = 0):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            WRITE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Write single byte to EP OUT. Tells the stick it is done writing when
            not inputed a byte.
        """

        # List
        if type(bytes) is not list:

            # Convert to list
            bytes = [bytes]

        # Write bytes to EP OUT
        self.EPs["OUT"].write(bytearray(bytes))



    def read(self, n = 64, timeout = 1000, radio = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Read from EP IN until it says it is done transmitting data using a
            zero byte. Timeout must be given in ms.
        """

        # Initialize bytes
        bytes = []

        # Read bytes
        while True:

            # Read, decode, and append new bytes
            bytes += self.EPs["IN"].read(n, timeout = timeout)

            # Exit condition
            if bytes[-1] == 0:

                # Remove end byte
                bytes.pop(-1)

                # Exit
                break

        # If bytes coming from radio are an error code
        if radio and len(bytes) == 1 and bytes[-1] in self.errors:

            # Raise error
            raise errors.RadioError(self.errors[bytes[-1]])

        # Return them
        return bytes



    def tune(self, f):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TUNE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Tune radio to given frequency in MHz.
        """

        # Info
        Logger.debug("Tuning radio to: " + fmt.frequency(f))

        # Convert frequency to corresponding value (according to datasheet)
        f = int(round(f * (2 ** 16) / self.f["Reference"]))

        # Convert to set of 3 bytes
        bytes = [lib.getByte(f, x) for x in [2, 1, 0]]

        # Update registers
        for reg, byte in zip(["FREQ2", "FREQ1", "FREQ0"], bytes):

            # Write to register
            self.commands["Radio Register TX"].run(reg, byte)

            # If mismatch
            if self.commands["Radio Register RX"].run(reg) != byte:
                raise errors.RadioRegisterTXFail

        # Info
        Logger.debug("Radio tuned.")



    def tuneOptimizedFrequency(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            TUNEOPTIMIZEDFREQUENCY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Check if frequency optimizing required.
        """

        # Get current formatted time
        now = datetime.datetime.now()

        # Get last frequency optimization
        entry = self.report.get(["Frequency"])

        # Entry exists
        if entry:

            # Destructure frequency entry
            [f, t] = entry

            # Convert time to datetime object
            t = lib.formatTime(t)

        # No frequency stored or stick not tuned today
        if entry is None or now.day != t.day:

            # Scan for best frequency
            f = self.scan(pump)

        # Tune radio
        self.tune(f)



    def checkFrequencyRange(self, f1, f2):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CHECKFREQUENCYRANGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Test if given frequency range fits within region frequencies
            definition.
        """

        # Check if frequencies are numbers
        if not (lib.isRealNumber(f1) and lib.isRealNumber(f2)):
            raise TypeError("Frequencies have to be numbers: [" + str(f1) +
                ", " + str(f2) + "]")

        # Check if frequency range value is valid
        if not f1 < f2:
            raise ValueError("Invalid radio frequency range: " +
                fmt.frequencyRange(f1, f2))

        # Go through regions and corresponding frequency ranges
        for f in self.f["Regions"].values():

            # Check if frequency matches a specific region
            if f1 >= min(f["Range"]) and f2 <= max(f["Range"]):
                return

        # No region found
        raise errors.UnknownFrequencyRange(f1, f2)



    def scan(self, pump, F1 = None, F2 = None, n = 25, sample = 5):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Scan the air for frequency with best signal strength (best sample
            average RSSI) to tune radio in order to communicate with pump.
        """

        # No frequencies given: default to NA region
        if F1 is None and F2 is None:
            [F1, F2] = self.f["Regions"]["NA"]["Range"]

        # Otherwise: test frequency range
        else:
            self.checkFrequencyRange(F1, F2)

        # Info
        Logger.info("Scanning for best RF to communicate with pump between: " +
            fmt.frequencyRange(F1, F2))

        # Initialize RSSI readings
        RSSIs = {}

        # Go through frequency range
        for f in np.linspace(F1, F2, n, True):

            # Round frequency
            f = round(f, 3)

            # Initialize RSSI value
            RSSIs[f] = []

            # Tune frequency
            self.tune(f)

            # Sample
            for _ in range(sample):

                # Try
                try:

                    # Run pump command
                    pump.model.read()

                    # Get last packet
                    pkt = pump.model.command.packets["RX"][-1]

                    # Get RSSI reading and add it
                    RSSIs[f].append(pkt.RSSI["dBm"])

                # On invalid packet or radio error
                except (errors.RadioError, errors.BadPumpPacket):

                    # Add fake low RSSI reading
                    RSSIs[f].append(-99)

            # Average readings
            RSSIs[f] = np.mean(RSSIs[f])

        # Show readings
        Logger.debug(lib.JSONize(RSSIs))

        # Check if pump was detected
        if not all(f == -99 for f in RSSIs.values()):

            # Optimize frequency
            f = self.getOptimizedFrequency(RSSIs)

            # Store it
            self.storeOptimizedFrequency(f)

        # Otherwise
        else:

            # Pump does not respond
            raise errors.NoPump

        # Return it
        return f



    def getOptimizedFrequency(self, RSSIs):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETOPTIMIZEDFREQUENCY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Find out which frequency corresponds to best sample average RSSI.
        """

        # Destructure RSSIs
        x, y = np.array(RSSIs.keys()), np.array(RSSIs.values())

        # Get sorted indices
        indices = x.argsort()

        # Sort
        x = x[indices]
        y = y[indices]

        # Get frequency with max signal power (5 dBm threshold, 3 digits)
        f = round(lib.getMaxMiddle(x, y, 5), 3)

        # Info
        Logger.info("Optimized frequency: " + fmt.frequency(f))

        # Return best frequency
        return f



    def storeOptimizedFrequency(self, f):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOREOPTIMIZEDFREQUENCY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Store optimized frequency.
        """

        # Info
        Logger.debug("Adding pump's last optimized frequency to: " +
            repr(self.report))

        # Get current formatted time
        now = lib.formatTime(datetime.datetime.now())

        # Add entry to report and store it
        self.report.set([f, now], ["Frequency"], True)
        self.report.store()



    def listen(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LISTEN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Listen to incoming packets on radio.
        """

        # Read from radio indefinitely
        while True:

            # Try reading
            try:

                # Get data
                data = self.commands["Radio RX"].run()

                # Turn it into a pump packet
                pkt = packets.FromPumpPacket(data)

                # Show it
                pkt.show()

            # Error
            except errors.RadioError:

                # Ignore
                pass



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a stick
    stick = Stick()

    # Start it
    stick.start()

    # Tune in to  default NA pump frequency
    stick.tune(stick.f["Regions"]["NA"]["Default"])

    # Warn user with LED
    stick.warn(3)

    # Listen to radio
    #stick.listen()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()