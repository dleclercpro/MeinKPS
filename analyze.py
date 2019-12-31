#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    analyze

    Author:   David Leclerc

    Version:  0.1

    Date:     25.12.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import fmt
import reporter
import calculator
import idc
from Profiles import bg, net, isf, csf, iob, cob, targets



def analyze(now, DIA, PIA, t = 24):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ANALYZE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Analyze differences between observations and expectations associated
        with treatments
    """

    # Define reference times
    past = now - datetime.timedelta(hours = t)

    # Instanciate profiles
    profiles = {"IDC": idc.ExponentialIDC(DIA, PIA),
                "Net": net.Net(),
                "PastBG": bg.PastBG(),
                "PastISF": isf.PastISF()}

    # Build past profiles
    profiles["PastBG"].build(past, now)
    profiles["PastISF"].build(past, now)

    # Reference to BG time axes
    T = profiles["PastBG"].T
    t = profiles["PastBG"].t

    # Initialize IOB arrays
    IOBs = []

    # Get number of BGs
    n = len(T)

    # Compute IOB for each BG
    for i in range(n):

        # Define start/end times of current net profile
        [start, end] = [T[i] - datetime.timedelta(hours = DIA), T[i]]

        # Build net insulin profile
        profiles["Net"].build(start, end)

        # Do it
        IOBs.append(calculator.computeIOB(profiles["Net"], profiles["IDC"]))

        # Show IOB
        print "IOB(" + lib.formatTime(end) + ") = " + fmt.IOB(IOBs[-1])

    # Initialize dBG deviations
    ddBGs = []

    # Go through IOBs and find difference between expected dBG and actual
    # one
    for i in range(n - 1):

        # Compute dIOB
        dIOB = IOBs[i + 1] - IOBs[i]

        # Get associated ISF
        # NOTE: there might be some error slipping in here if ISF changes
        # between two IOBs
        ISF = profiles["PastISF"].f(t[i])

        # Compute dBGs
        dBG = profiles["PastBG"].y[i + 1] - profiles["PastBG"].y[i]
        expecteddBG = dIOB * ISF

        # Compute difference between observed and expected dBG associated
        # with dIOB
        ddBGs.append(dBG - expecteddBG)

        # Info
        print "dIOB: " + fmt.IOB(dIOB)
        print "dBG: " + fmt.BG(dBG)
        print "Expected dBG: " + fmt.BG(expecteddBG)
        print "ddBG: " + fmt.BG(ddBGs[i])
        print

    # Info
    print "AVG ddBG: " + fmt.BG(np.mean(ddBGs))
    print "STD ddBG: " + fmt.BG(np.std(ddBGs))

    # Plot results
    plot(t, ddBGs, profiles["PastBG"].y, IOBs)



def plot(t, ddBGs, BGs, IOBs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PLOT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Plot results of analysis
    """

    # Initialize plot
    lib.initPlot()
    axes = {"ddBGs": plt.subplot(3, 1, 1),
            "BGs": plt.subplot(3, 1, 2),
            "IOBs": plt.subplot(3, 1, 3)}

    # Define axis labels
    x = "(h)"
    y = "(mmol/L)"

    # Set title
    axes["ddBGs"].set_title("ddBGs", fontweight = "semibold")
    axes["BGs"].set_title("BGs", fontweight = "semibold")
    axes["IOBs"].set_title("IOBs", fontweight = "semibold")

    # Set axis labels
    axes["ddBGs"].set_xlabel(x)
    axes["ddBGs"].set_ylabel(y)
    axes["BGs"].set_xlabel(x)
    axes["BGs"].set_ylabel(y)
    axes["IOBs"].set_xlabel(x)
    axes["IOBs"].set_ylabel("U")

    # Plot axes
    axes["ddBGs"].plot(t[:-1], ddBGs, marker = "o", ms = 3.5, lw = 0, c = "black")
    axes["BGs"].plot(t[:-1], BGs[:-1], marker = "o", ms = 3.5, lw = 0, c = "red")
    axes["IOBs"].plot(t[:-1], IOBs[:-1], marker = "o", ms = 3.5, lw = 0, c = "orange")
    plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Get IDC related quantities
    DIA = reporter.getPumpReport().get(["Settings", "DIA"])
    PIA = 1.25

    # Define timespan for autotune
    t = 24 # h

    # Run analyze and plot results
    analyze(now, DIA, PIA, t)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()