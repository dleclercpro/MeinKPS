#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    model

    Author:   David Leclerc

    Version:  0.1

    Date:     03.06.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TERMINOLOGY
#   - IAC: insulin action curve
#   - IDC: insulin decay curve
#   - IOB: insulin-on-board
#   - PIA: peak of insulin action
#   - DIA: duration of insulin action
#   - MID: time after which IDC should have 50% dropped



# LIBRARIES
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import scipy.special



# USER LIBRARIES
import lib



def IAC(t, args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        IAC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    a = args[0]
    b = args[1]
    c = args[2]

    IAC = a * t**b * np.exp(-c * t)

    return IAC



def IDC(t, args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        IDC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The equation of IDC is found using the indefinite integral I of the IAC in
    the following way:

    IDC = 1 - I

    """

    a = args[0]
    b = args[1]
    c = args[2]

    # Initialize indefinite integral I with I(t = 0)
    I = np.array([0])

    # Evaluate indefinite integral I
    for m in range(1, len(t)):

        # Add new I(t) to I
        I = np.append(I, lib.integrate(t = t[0:(m + 1)],
                                       f = IAC,
                                       args = [a, b, c]))

    # Tweak indefinite integral I to obtain IDC
    IDC = 1 - I

    return IDC



def optimizeIAC(t, PIA, DIA, MID):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        OPTIMIZEIAC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define importance of right peak time
    weightmax = 1000

    # Define importance of getting the right integral values
    weightI = 1000

    load = lambda x:(
           abs(t[np.argmax(IAC(t = t, args = [x[0], x[1], x[2]]))] - PIA) +
           abs(IAC(t = t, args = [x[0], x[1], x[2]])[DIA]) +
           abs(1.0 - lib.integrate(t = t, f = IAC, args = [x[0], x[1], x[2]])) +
           abs(0.5 - lib.integrate(t = t[0:(MID * len(t) / DIA)], f = IAC,
           args = [x[0], x[1], x[2]])))

    optimizedArgs = scipy.optimize.fmin(func = load,
                                         x0 = [15.0, 4.0, 4.0],
                                         maxiter = 5000,
                                         maxfun = 5000)

    print "Optimized function parameters: " + str(optimizedArgs)

    return optimizedArgs



def plotInsulinActivity(t, args, PIA, DIA, MID):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PLOTINSULINACTIVITY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define IDC of Animas
    x0 = 1.0104
    x1 = -0.02203
    x2 = -0.2479
    x3 = 0.07493
    x4 = -0.006623

    tAnimas = t[0:(4.5 * len(t) / DIA)]
    IDCAnimas = (x0 + x1 * tAnimas + x2 * tAnimas**2 + x3 * tAnimas**3 +
                  x4 * tAnimas**4)

    # Extract optimized parameters
    a = args[0]
    b = args[1]
    c = args[2]

    # Initialize plot
    mpl.rc("font", size = 11, family = "Ubuntu")
    fig = plt.figure(0, figsize = (10, 8))
    sub = plt.subplot(111)

    # Define plot title
    plt.title("Insulin activity and decay over time for " +
              "PIA = " + str(PIA) + ", DIA = " + str(DIA) + ", and MID = " +
              str(MID),
              weight = "semibold")

    # Define plot axis
    plt.xlabel("Time (h)", weight = "semibold")
    plt.ylabel("Insulin Activity (-)", weight = "semibold")

    # Add IAC and its integral to plot
    plt.plot(t, IAC(t = t, args = args),
             ls = "-", lw = 1.5, c = "grey",
             label = "IAC: " + r"$f(t) = a \cdot x^b \cdot e^{-c \cdot t}$, " +
                     "with $[a, b, c]$ = [" + str(round(a, 1)) + ", " +
                     str(round(b, 1)) + ", " + str(round(c, 1)) + "]")

    plt.plot(t, IDC(t = t, args = args),
             ls = "-", lw = 1.5, c = "blue",
             label = "IDC: " + r"$F(t) = \int$" + " " + r"$f(t) \cdot dt$")

    plt.plot(tAnimas, IDCAnimas,
             ls = "-", lw = 1.5, c = "purple",
             label = "Animas IDC")

    # Define plot legend
    legend = plt.legend(title = "Insulin activity and decay curves", loc = 1,
                        borderaxespad = 1.5, numpoints = 1, markerscale = 2)

    plt.setp(legend.gettitle(), fontweight = "semibold")

    # Tighten up
    plt.tightlayout()

    # Show plot
    plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    PIA = 1.25
    DIA = 6.0
    MID = 2.0
    N = 1000

    t = np.linspace(0, DIA, N)

    args = optimizeIAC(t = t, PIA = PIA, DIA = DIA, MID = MID)

    plotInsulinActivity(t = t, args = args, PIA = PIA, DIA = DIA, MID = MID)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
