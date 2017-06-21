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
import logging



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
        self.calc = calculator.Calculator()



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Q: is reading time/model necessary at beginning of loop?
        """

        # Define current time
        self.now = datetime.datetime.now()

        # Give user info
        print "Start: " + lib.formatTime(self.now)

        # Load pump report
        Reporter.load("loop.json")
        Reporter.increment([], "Attempts")

        # Dump CGM readings
        #self.cgm.dumpLastBG()

        # Start dialogue with pump
        self.pump.start()

        # Read pump time
        self.pump.time.read()
        Reporter.increment([], "Time")

        # Read pump model
        self.pump.model.read()
        Reporter.increment([], "Model")

        # Read pump battery level
        self.pump.battery.read()
        Reporter.increment([], "Battery")

        # Read remaining amount of insulin in pump
        self.pump.reservoir.read()
        Reporter.increment([], "Reservoir")

        # Read BG targets stored in pump
        self.pump.BGTargets.read()
        Reporter.increment([], "BG Targets")

        # Read insulin sensitivity factors stored in pump
        self.pump.ISF.read()
        Reporter.increment([], "ISF")

        # Read carb sensitivity factors stored in pump
        self.pump.CSF.read()
        Reporter.increment([], "CSF")

        # Read basal profile stored in pump
        self.pump.basalProfile.read("Standard")
        Reporter.increment([], "Basal Profile")



    def finish(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FINISH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stop dialogue with pump
        self.pump.stop()

        # Give user info
        print "End: " + lib.formatTime(datetime.datetime.now())



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare loop
        self.prepare()

        # Run calculator and get TB recommendation
        #TB = self.calc.run(self.now)

        # Show loop
        #self.show(self.calc.net, self.calc.BG, self.calc.IOB, self.calc.IDC.DIA)

        # React to TB recommendation
        #if TB is None:
        if False:

            # Cancel TB
            self.pump.TB.cancel()

        else:

            # Enact TB
            #self.pump.TB.set(*TB)
            self.pump.TB.set(0.5, "U/h", 30)
            Reporter.increment([], "TB")

        # Finish loop
        self.finish()



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
        y = ["(" + BG.u + ")",
             "(U/h)",
             "(U)",
             "(g)"]

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
    loop.do()

    # End of script
    print "Looped successfully!"



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
