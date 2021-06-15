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
import copy
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



def computeObservedBGDeltas(BGs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEOBSERVEDBGDELTAS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes an array of observed BG variations.
    """

    BGs = np.array(BGs)

    return BGs[1:] - BGs[:-1]



def computeExpectedBGDeltas(t, T, Net, IDC, ISFs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEEXPECTEDBGDELTAS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes an array of expected BG variations, given an IDC
        and a net insulin profile. The latter is expected to cover the following
        time range:

            [T[0] - IDC.DIA, T[-1] - IDC.DIA]
    """

    # Ensure time axis is defined
    if not t or not T:
        raise ValueError("No time axis given for which to compute IOBs.")

    # Initialize expected BG deltas
    expectedDeltaBGs = []

    # Make a copy of net insulin profile to work on, and shift it to match first
    # time point of given BG time axis
    Net = copy.deepcopy(Net)
    Net.shift(Net.norm - T[0])

    # Compute BG deltas to expect for each time point
    for (T0, T1) in lib.pair(T):

        # Compute corresponding IOB
        IOB0 = calculator.computeIOB(Net, IDC)
        
        # Move net insulin profile into the past by the time that passes until
        # next BG value
        dT = T1 - T0
        Net.shift(-dT)

        # Compute new IOB, and the difference with the last one
        IOB1 = calculator.computeIOB(Net, IDC)
        dIOB = IOB1 - IOB0

        # Get current ISF and compute dBG using dIOB
        # NOTE: there might be some error slipping in here if ISF changes
        # between the two IOBs
        ISF = ISFs.f(T0)
        dBG = dIOB * ISF

        # Store and show expected BG delta
        expectedDeltaBGs += [dBG]

    return expectedDeltaBGs



def computeIOBs(t, T, Net, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEIOBS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes the IOB at a given time, using a net insulin
        profile. The latter is expected to cover the following time range:

            [T[0] - IDC.DIA, T[-1] - IDC.DIA]
    """

    # Ensure time axis is defined
    if not t or not T:
        raise ValueError("No time axis given for which to compute IOBs.")

    # Initialize IOBs
    IOBs = []

    # Make a copy of net insulin profile to work on, and shift it to match first
    # time point of given BG time axis
    Net = copy.deepcopy(Net)
    Net.shift(Net.norm - T[0])

    # Compute IOB for each time point
    for (T0, T1) in lib.pair(T) + [(T[-1], T[-1])]:

        # Compute corresponding IOB, store, and show it
        IOB = calculator.computeIOB(Net, IDC)
        IOBs += [IOB]

        # Shift net insulin profile accordingly for next IOB computation
        dT = T1 - T0
        Net.shift(-dT)

    return IOBs



def compareExpectedVsObservedBGDeltas(now, t, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPAREEXPECTEDVSOBSERVEDBGDELTAS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ...
    """

    # Define reference times
    past = now - datetime.timedelta(hours = t)

    # Instanciate profiles
    BGs = bg.PastBG()
    ISFs = isf.PastISF()
    Net = net.Net()

    # Build them
    BGs.build(past, now)
    ISFs.build(past, now)
    Net.build(past - datetime.timedelta(hours = IDC.DIA), now)

    # Compute IOBs
    IOBs = computeIOBs(BGs.t, BGs.T, Net, IDC)

    # Compute expected and observed BGs
    expectedBGDeltas = computeExpectedBGDeltas(BGs.t, BGs.T, Net, IDC, ISFs)
    observedBGDeltas = computeObservedBGDeltas(BGs.y)

    # Compute difference between expectations and observations
    ddBGs = np.array(observedBGDeltas) - np.array(expectedBGDeltas)
    print "AVG ddBG: " + fmt.BG(np.mean(ddBGs))
    print "STD ddBG: " + fmt.BG(np.std(ddBGs))

    # Plot results
    plot(BGs.t[:-1], expectedBGDeltas, observedBGDeltas, ddBGs, BGs.y[:-1], IOBs[:-1])



def plot(t, expectedBGDeltas, observedBGDeltas, ddBGs, BGs, IOBs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PLOT
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Plot results of analysis.
    """

    # Initialize plot
    lib.initPlot()
    axes = {"ddBGs": plt.subplot(3, 1, 1),
            "BGs": plt.subplot(3, 1, 2),
            "IOBs": plt.subplot(3, 1, 3)}

    # Define default BG limits in plot
    minBG = 2
    maxBG = 22

    # Define axis labels
    x = "(h)"
    y = "(mmol/L)"

    # Define axis limits
    xlim = [min(t), 0]
    ylim = [min(minBG, min(BGs)), max(maxBG, max(BGs))]

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

    # Set x-axis limits
    axes["ddBGs"].set_xlim(xlim)
    axes["BGs"].set_xlim(xlim)
    axes["IOBs"].set_xlim(xlim)

    # Set y-axis limits
    axes["BGs"].set_ylim(ylim)

    # Plot horizontal lines
    axes["BGs"].axhline(y = 4, color = "red", linestyle = "-")
    axes["BGs"].axhline(y = 8, color = "orange", linestyle = "-")
    axes["ddBGs"].axhline(y = 0, color = "black", linestyle = "--")
    axes["IOBs"].axhline(y = 0, color = "black", linestyle = "--")

    # Plot axes
    axes["ddBGs"].plot(t, ddBGs,
        marker = "o", ms = 2, lw = 0, c = "purple")
    axes["BGs"].plot(t, BGs,
        marker = "o", ms = 2, lw = 0, c = "black")
    axes["IOBs"].plot(t, IOBs,
        marker = "o", ms = 2, lw = 0, c = "grey")
    
    # Show plot
    plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Get IDC
    DIA = reporter.getPumpReport().get(["Settings", "DIA"])
    PIA = 1.25
    IDC = idc.ExponentialIDC(DIA, PIA)

    # Define timespan for autotune (h)
    t = 24

    # Run analyze and plot results
    compareExpectedVsObservedBGDeltas(now, t, IDC)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()