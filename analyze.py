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



def computeObservedBGDeltas(BGs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEOBSERVEDBGDELTAS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes an array of observed BG variations.
    """

    BGs = np.array(BGs)

    return BGs[1:] - BGs[:-1]



def computeExpectedBGDeltas(t, T, IDC, ISFs):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEEXPECTEDBGDELTAS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes an array of expected BG variations, given an IDC
        and a net insulin profile.
    """

    # Initialize expected BG deltas
    expectedDeltaBGs = []

    # Instanciate net insulin profile
    net_ = net.Net()

    # Compute expected BG deltas
    for i in range(len(T) - 1):

        # Define start/end times of net profile, and build the latter
        start = T[i] - datetime.timedelta(hours = IDC.DIA)
        end = T[i]
        net_.build(start, end)

        # Compute corresponding IOB
        IOB0 = calculator.computeIOB(net_, IDC)
        
        # Move net insulin profile into the past by the time that passes until
        # next BG value
        dt = t[i + 1] - t[i]
        net_.shift(-dt)

        # Compute new IOB, and the difference with the last one
        IOB1 = calculator.computeIOB(net_, IDC)
        dIOB = IOB1 - IOB0

        # Get current ISF and compute dBG using dIOB
        # NOTE: there might be some error slipping in here if ISF changes
        # between the two IOBs
        ISF = ISFs.f(t[i])
        dBG = dIOB * ISF

        # Store and show expected BG delta
        expectedDeltaBGs += [dBG]
        print "dBG(" + lib.formatTime(start) + ") = " + fmt.BG(dBG)

    return expectedDeltaBGs



def computeIOBs(t, T, IDC):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        COMPUTEIOBS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        This function computes the IOB at a given time.
    """

    # Initialize IOBs
    IOBs = []

    # Instanciate net insulin profile
    net_ = net.Net()

    # Compute IOB for each BG
    for i in range(len(T)):

        # Define start/end times of current net profile
        start = T[i] - datetime.timedelta(hours = IDC.DIA)
        end = T[i]

        # Build net insulin profile
        net_.build(start, end)

        # Compute corresponding IOB, store, and show it
        IOB = calculator.computeIOB(net_, IDC)
        IOBs += [IOB]
        print "IOB(" + lib.formatTime(end) + ") = " + fmt.IOB(IOB)

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

    # Build past profiles
    BGs.build(past, now)
    ISFs.build(past, now)

    # Compute expected and observed BGs
    expectedBGDeltas = computeExpectedBGDeltas(BGs.t, BGs.T, IDC, ISFs)
    observedBGDeltas = computeObservedBGDeltas(BGs.y)

    # Compute difference between expectations and observations
    ddBGs = np.array(observedBGDeltas) - np.array(expectedBGDeltas)
    print "AVG ddBG: " + fmt.BG(np.mean(ddBGs))
    print "STD ddBG: " + fmt.BG(np.std(ddBGs))

    # Compute IOBs
    IOBs = computeIOBs(BGs.t, BGs.T, IDC)

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
    axes = {#"expected": plt.subplot(5, 1, 1),
            #"observed": plt.subplot(5, 1, 2),
            "ddBGs": plt.subplot(3, 1, 1),
            "BGs": plt.subplot(3, 1, 2),
            "IOBs": plt.subplot(3, 1, 3)}

    # Define axis labels
    x = "(h)"
    y = "(mmol/L)"

    # Set title
    #axes["expected"].set_title("Expected dBGs", fontweight = "semibold")
    #axes["observed"].set_title("Observed dBGs", fontweight = "semibold")
    axes["ddBGs"].set_title("ddBGs", fontweight = "semibold")
    axes["BGs"].set_title("BGs", fontweight = "semibold")
    axes["IOBs"].set_title("IOBs", fontweight = "semibold")

    # Set axis labels
    #axes["expected"].set_xlabel(x)
    #axes["expected"].set_ylabel(y)
    #axes["observed"].set_xlabel(x)
    #axes["observed"].set_ylabel(y)
    axes["ddBGs"].set_xlabel(x)
    axes["ddBGs"].set_ylabel(y)
    axes["BGs"].set_xlabel(x)
    axes["BGs"].set_ylabel(y)
    axes["IOBs"].set_xlabel(x)
    axes["IOBs"].set_ylabel("U")

    # Plot axes
    #axes["expected"].plot(t, expectedBGDeltas,
    #    marker = "o", ms = 3.5, lw = 0, c = "black")
    #axes["observed"].plot(t, observedBGDeltas,
    #    marker = "o", ms = 3.5, lw = 0, c = "black")
    axes["ddBGs"].plot(t, ddBGs,
        marker = "o", ms = 3.5, lw = 0, c = "black")
    axes["BGs"].plot(t, BGs,
        marker = "o", ms = 3.5, lw = 0, c = "red")
    axes["IOBs"].plot(t, IOBs,
        marker = "o", ms = 3.5, lw = 0, c = "orange")
    axes["ddBGs"].axhline(y = 0, color = "black", linestyle = "-")
    
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