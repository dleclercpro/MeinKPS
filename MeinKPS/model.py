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
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import scipy.special



# USER LIBRARIES
import lib
import calculator
import reporter



# Instanciate a reporter
Reporter = reporter.Reporter()



def IAC(t, args):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        IAC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    [a, b, c] = args

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

    # Initialize indefinite integral I with I(t = 0)
    I = np.array([0])

    # Evaluate indefinite integral I
    for m in range(1, len(t)):

        # Add new I(t) to I
        I = np.append(I, lib.integrate(t = t[0:(m + 1)],
                                       f = IAC,
                                       args = args))

    # Tweak indefinite integral I to obtain IDC
    IDC = 1 - I

    return IDC



def walshIDC(t):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        WALSHIDC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    IDC = (-3.203e-7 * (60.0 * t) ** 4 +
            1.354e-4 * (60.0 * t) ** 3 +
           -1.759e-2 * (60.0 * t) ** 2 +
            9.255e-2 * (60.0 * t) ** 1 +
            99.951) / 100.0

    return IDC



def optimizeIAC(t, PIA, DIA, MID):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        OPTIMIZEIAC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define initial parameters
    x0 = [15.0, 4.0, 4.0]

    load = lambda x:(

           # Deviation from 0 of insulin action at DIA
           abs(IAC(t = t, args = x)[-1]) +

           # Deviation from 1 of integral of insulin action from 0 to DIA
           abs(1.0 - lib.integrate(t = t, f = IAC, args = x)) +

           # Deviation from 0.5 of integral of insulin action from 0 to DIA / 2
           abs(0.5 - lib.integrate(t = t[0:(MID * len(t) / DIA)], f = IAC,
                                   args = x)) +

           # Limit conditions
           abs(lib.derivate(IAC(t = t, args = x), t[1] - t[0])[0]) +
           abs(lib.derivate(IAC(t = t, args = x), t[1] - t[0])[-1]) +

           # Deviation from peak of insulin action
           abs(t[np.argmax(IAC(t = t, args = x))] - PIA))

    optimizedArgs = scipy.optimize.fmin(func = load, x0 = x0,
                                        maxiter = 5000,
                                        maxfun = 5000)

    print "Optimized function parameters: " + str(optimizedArgs)

    return optimizedArgs



def modelInsulinActivity(t, args, PIA, DIA, MID):

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MODELINSULINACTIVITY
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

    walshIDC = calculator.WalshIDC(3)

    plt.plot(t, walshIDC.f(t = t),
             ls = "-", lw = 1.5, c = "red",
             label = "Walsh IDC")

    plt.plot(t, walshIDC.F(t = t),
                 ls = "-", lw = 1.5, c = "orange",
                 label = "Walsh IDC")

    # Define plot legend
    legend = plt.legend(title = "Insulin activity and decay curves", loc = 1,
                        borderaxespad = 1.5, numpoints = 1, markerscale = 2)

    plt.setp(legend.get_title(), fontweight = "semibold")

    # Tighten up
    plt.tight_layout()

    # Show plot
    plt.show()



def plotInsulinActivity():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        PLOTINSULINACTIVITY
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now()

    # Instanciate calculator
    calc = calculator.Calculator()

    # Run calculator
    calc.run()

    # Link with net profile
    profileT = np.array(calc.netProfile.T)
    profileY = np.array(calc.netProfile.y)

    # Load pump report
    Reporter.load("pump.json")

    # Read DIA
    DIA = Reporter.getEntry(["Settings"], "DIA")

    # Define timestep (h)
    dt = 5 / 60.

    # Compute number of steps
    n = int(DIA / dt)

    # Generate time axis for all IOBs
    t = np.linspace(DIA * 3600, 0, 500)
    T = np.linspace(dt, DIA, n)

    # Convert time axis to hours
    t /= 3600.0

    # Initialize plot
    mpl.rc("font", size = 11, family = "Ubuntu")
    fig = plt.figure(0, figsize = (10, 8))
    sub = plt.subplot(111)

    # Define plot title
    plt.title("Insulin Decay Over Time (DIA = " + str(DIA) + ")",
              weight = "semibold")

    # Define plot axis
    plt.xlabel("Time (h)", weight = "semibold")
    plt.ylabel("Insulin Activity (-)", weight = "semibold")

    # Add Walsh IDC to plot
    plt.plot(-t, calc.IDC.f(t),
             ls = "-", lw = 1.5, c = "red", label = "Walsh IDC")

    # Add insulin net profile to plot
    plt.step(-profileT, np.append(0, profileY[:-1]),
             ls = "-", lw = 1.5, c = "purple", label = "Net Profile")

    # Add IOBs to plot
    #plt.plot(-t, IOBs,
    #         ls = "-", lw = 1.5, c = "blue", label = "IOB")

    # Add future IOBs to plot
    plt.plot(T, calc.IOB.y,
             ls = "-", lw = 1.5, c = "orange", label = "Future IOB")

    # Define plot legend
    legend = plt.legend(title = "Legend", loc = 0, borderaxespad = 1.5,
                        numpoints = 1, markerscale = 2)

    # Style legend
    plt.setp(legend.get_title(), fontweight = "semibold")

    # Tighten up
    plt.tight_layout()

    # Show plot
    plt.show()












def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    #PIA = 1.25
    #DIA = 3.0
    #MID = DIA / 2
    #N = 1000

    #t = np.linspace(0, DIA, N)

    #args = optimizeIAC(t = t, PIA = PIA, DIA = DIA, MID = MID)

    #modelInsulinActivity(t = t, args = args, PIA = PIA, DIA = DIA, MID = MID)

    plotInsulinActivity()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
