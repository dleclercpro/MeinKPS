#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    loop

    Author:   David Leclerc

    Version:  0.1

    Date:     24.05.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np



# USER LIBRARIES
import lib
import calculator
import reporter
from CGM import cgm
from Pump import pump



# Define a reporter
Reporter = reporter.Reporter()



class Loop(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.now = None

        # Give the loop a CGM
        self.cgm = cgm.CGM()

        # Give the loop a pump
        self.pump = pump.Pump()

        # Give the loop a calculator
        self.calculator = calculator.Calculator()



    def prepareCGM(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARECGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If not a quick run
        if not quick:

            # Read clock
            self.do(self.cgm.clock.read, ["CGM"], "Clock")

            # Read battery
            self.do(self.cgm.battery.read, ["CGM"], "Battery")

            # Read units
            self.do(self.cgm.units.read, ["CGM"], "Units")

            # Read language
            self.do(self.cgm.language.read, ["CGM"], "Language")

            # Read firmware
            self.do(self.cgm.firmware.read, ["CGM"], "Firmware")

            # Read transmitter
            self.do(self.cgm.transmitter.read, ["CGM"], "Transmitter")

            # Read BG
            self.do(self.cgm.dumpBG, ["CGM"], "BG")

        # Otherwise
        else:

            # Read CGM
            self.do(self.cgm.dumpNewBG, ["CGM"], "BG")



    def doCGM(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOCGM
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Establish connection with CGM
        self.cgm.connect()

        # Prepare CGM
        self.prepareCGM()

        # End connection with CGM
        self.cgm.disconnect()



    def preparePump(self, quick = True):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPAREPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If not a quick run
        if not quick:

            # Read pump time
            self.do(self.pump.time.read, ["Pump"], "Time")

            # Read pump model
            self.do(self.pump.model.read, ["Pump"], "Model")

            # Read pump battery level
            self.do(self.pump.battery.read, ["Pump"], "Battery")

            # Read remaining amount of insulin in pump
            self.do(self.pump.reservoir.read, ["Pump"], "Reservoir")

        # Read insulin sensitivity factors stored in pump
        self.do(self.pump.ISF.read, ["Pump"], "ISF")

        # Read carb sensitivity factors stored in pump
        self.do(self.pump.CSF.read, ["Pump"], "CSF")

        # Read BG targets stored in pump
        self.do(self.pump.BGTargets.read, ["Pump"], "BG Targets")

        # Read basal profile stored in pump
        self.do(self.pump.basalProfile.read, ["Pump"], "Basal", "Standard")



    def doPump(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOPUMP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start dialogue with pump
        self.pump.start()

        # Prepare pump
        self.preparePump()

        # Run calculator and get TB recommendation
        #TB = self.calculator.run(self.now)
        TB = [round(self.now.minute / 60.0 * 3.0, 2), "U/h", 30]

        # React to TB recommendation
        if TB is None:

            # Cancel TB
            self.pump.TB.cancel()

        # Otherwise
        else:

            # Enact TB
            self.do(self.pump.TB.set, ["Pump"], "TB", *TB)

        # Stop dialogue with pump
        self.pump.stop()



    def do(self, task, path, key, *args):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Trying doing given task
        try:

            # Do task
            task(*args)

            # Update loop log
            Reporter.increment(path, key)

        # Otherwise, skip
        except:

            # Give user info
            print "Could not execute task '" + key + "'."



    def run(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define starting time
        start = datetime.datetime.now()

        # Give user info
        print "Start: " + lib.formatTime(start)

        # Store it
        self.now = start

        # Load loop report
        Reporter.load("loop.json")

        # Update loop infos
        Reporter.addEntries(["Status"], "Time", lib.formatTime(start), True)
        Reporter.increment(["Status"], "N")

        # Do CGM stuff
        self.doCGM()

        # Do pump stuff
        self.doPump()

        # Define ending time
        end = datetime.datetime.now()

        # Get duration of loop
        d = end - start

        # Update loop infos
        Reporter.addEntries(["Status"], "Duration", d.seconds, True)

        # Give user info
        print "End: " + lib.formatTime(end)

        # Show loop
        #self.show(self.calculator.net,
        #          self.calculator.BG,
        #          self.calculator.IOB,
        #          self.calculator.IDC.DIA)



    def show(self, net, BG, IOB, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize plot
        mpl.rc("font", size = 10, family = "Ubuntu")
        fig = plt.figure(0, figsize = (10, 8))
        axes = [plt.subplot(221),
                plt.subplot(222),
                plt.subplot(223),
                plt.subplot(224)]

        # Define titles
        titles = ["BG", "Net Insulin Profile", "IOB", "COB"]

        # Define axis labels
        x = ["(h)"] * 4
        y = ["(" + BG.u + ")", "(U/h)", "(U)", "(g)"]

        # Define axis limits
        xlim = [[-DIA, DIA]] * 4
        ylim = [[2, 20], None, None, None]

        # Define subplots
        for i in range(4):

            # Set titles
            axes[i].set_title(titles[i], fontweight = "semibold")

            # Set x-axis labels
            axes[i].set_xlabel(x[i])

            # Set y-axis labels
            axes[i].set_ylabel(y[i])

            # Set x-axis limits
            axes[i].set_xlim(xlim[i])

        # Set y-axis limits
        axes[0].set_ylim(ylim[0])

        # Add BGs to plot
        axes[0].plot(BG.past.t, BG.past.y, marker = "o", ms = 3.5, lw = 0,
                                           c = "red")

        # Add BG predictions to plot
        axes[0].plot(BG.t, BG.y, marker = "o", ms = 3.5, lw = 0, c = "black")

        # Add net insulin profile to plot
        axes[1].step(net.t, np.append(0, net.y[:-1]), lw = 2, ls = "-",
                                                      c = "#ff7500")

        # Add past IOB to plot
        axes[2].plot(IOB.past.t, IOB.past.y, marker = "o", ms = 3.5, lw = 0,
                                             c = "purple")

        # Add IOB predictions to plot
        axes[2].plot(IOB.t, IOB.y, lw = 2, ls = "-", c = "black")

        # Add COB to plot
        axes[3].plot([-DIA, 0], [0, 0], lw = 2, ls = "-", c = "#99e500")

        # Add COB predictions to plot
        axes[3].plot([0, DIA], [0, 0], lw = 2, ls = "-", c = "black")

        # Tighten up
        plt.tight_layout()

        # Show plot
        plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~­
    """

    # Instanciate a loop
    loop = Loop()

    # Loop
    loop.run()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
