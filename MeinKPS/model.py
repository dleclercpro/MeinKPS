#! /usr/bin/python



"""
================================================================================
Title:    model

Author:   David Leclerc

Version:  0.1

Date:     02.06.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: ...

Notes:    ...
================================================================================
"""



# TERMINOLOGY
#   - IAC: insulin action curve
#   - IOB: insulin-on-board
#   - PIA: peak of insulin action
#   - DIA: duration of insulin action



# LIBRARIES
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import scipy.special



def integrateSimpson(f, p, t, a, b, N):

    """
    ============================================================================
    INTEGRATESIMPSON
    ============================================================================

    This is a module that approximates the integral i of a given function f from
    a to b. In order to do that, it uses the Simpson method, with N intervals.
    """

    h = (b - a) / float(N)
    i = np.sum((f(t, p) + 4 * f(t + h/2, p) + f(t + h, p)) * h/6)

    return i



def IAC(t, p):

    """
    ============================================================================
    IAC
    ============================================================================
    """

    a = p[0]
    b = p[1]
    c = p[2]

    IAC = a * t**b * np.exp(-c * t)

    return IAC



def IOB(t, p):

    """
    ============================================================================
    IOB
    ============================================================================
    """

    a = p[0]
    b = p[1]
    c = p[2]

    t[0] = 0.000001

    IOB = -a * t**b * (c * t)**(-b) * scipy.special.gammainc(1 + b, c * t) / c
    IOB = 1 - IOB / IOB[-1]

    t[0] = 0
    IOB[0] = 1

    return IOB



def optimizeIAC(t, N, PIA, DIA):

    """
    ============================================================================
    OPTIMIZEIAC
    ============================================================================
    """

    load = lambda x:(
            abs(t[np.argmax(IAC(t = t, p = [x[0], x[1], x[2]]))] - PIA) +
            abs(IAC(t = t, p = [x[0], x[1], x[2]])[DIA]) +
            abs(1.0 - integrateSimpson(f = IAC,
                                       t = t,
                                       p = [x[0], x[1], x[2]],
                                       a = 0,
                                       b = DIA,
                                       N = N)) +
            abs(0.5 - integrateSimpson(f = IAC,
                                       t = t,
                                       p = [x[0], x[1], x[2]],
                                       a = 0,
                                       b = 0.5 * DIA,
                                       N = N)))

    return scipy.optimize.fmin(func = load,
                               x0 = [15.0, 2.0, 2.0],
                               maxiter = 5000,
                               maxfun = 5000)



def plotIAC(t, IAC, IOB, PIA, DIA):

    """
    ============================================================================
    PLOTIAC
    ============================================================================
    """

    # Initialize plot
    mpl.rc("font", size = 11, family = "Ubuntu")
    fig = plt.figure(0, figsize = (10, 8))
    sub = plt.subplot(111)

    # Define plot title
    plt.title("Insulin action curve for PIA = " + str(PIA) + " and DIA = " +
              str(DIA), weight = "semibold")

    # Define plot axis
    plt.xlabel("Time (h)", weight = "semibold")
    plt.ylabel("Insulin Action Curve (-)", weight = "semibold")

    # Add IAC and its integral to plot
    plt.plot(t, IAC, ls = "-", lw = 1.5, c = "grey",
        label = r"$\int_{" + str(0) + "}^{" + str(int(DIA)) + "}" +
        "a \cdot x^b \cdot e^{-c * x} \cdot dt = 1$")
    plt.plot(t, IOB, ls = "-", lw = 1.5, c = "red")

    # Define plot legend
    legend = plt.legend(title = "Optimization conditions", loc = 1,
        borderaxespad = 1.5, numpoints = 1, markerscale = 2)

    plt.setp(legend.get_title(), fontweight = "semibold")

    # Tighten up
    plt.tight_layout()

    # Show plot
    plt.show()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    PIA = 1.25
    DIA = 6.0
    N = 500
    t = np.linspace(0, DIA, N, endpoint = False)

    p = optimizeIAC(t = t,
                    N = N,
                    PIA = PIA,
                    DIA = DIA)

    plotIAC(t = t,
            IAC = IAC(t, p),
            IOB = IOB(t, p),
            PIA = PIA,
            DIA = DIA)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
