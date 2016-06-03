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



def integrate(t, f, f_params):

    """
    ============================================================================
    INTEGRATE
    ============================================================================

    This is a module that approximates the integral i of a given function f from
    a to b, given an equally spaced time vector t. In order to do that, it uses
    the Simpson method, and uses said time vector to evaluate the number N of
    intervals and the integration step h.
    """

    a = t[0]
    b = t[-1]
    N = len(t) - 1
    h = (b - a) / float(N)

    # Delete last t to not add contribution of [b, b + h] to the integral!
    t = t[0:-1]

    # Evaluate definite integral of f from a to b
    i = np.sum(h/6 * (f(t, f_params) +
                      f(t + h/2, f_params) * 4 +
                      f(t + h, f_params)))

    print "i(a = " + str(a) + ", b = " + str(b) + ") = " + str(i)

    return i



def IAC(t, f_params):

    """
    ============================================================================
    IAC
    ============================================================================
    """

    a = f_params[0]
    b = f_params[1]
    c = f_params[2]

    IAC = a * t**b * np.exp(-c * t)

    return IAC



def IDC(t, f_params):

    """
    ============================================================================
    IDC
    ============================================================================

    The equation of IDC is found using the indefinite integral I of the IAC in
    the following way:

    IDC = 1 - I

    """

    a = f_params[0]
    b = f_params[1]
    c = f_params[2]

    # Initialize indefinite integral I with I(t = 0)
    I = np.array([0])

    # Evaluate indefinite integral I
    for m in range(1, len(t)):

        # Add new I(t) to I
        I = np.append(I, integrate(t = t[0:(m + 1)],
                                   f = IAC,
                                   f_params = [a, b, c]))

    # Tweak indefinite integral I to obtain IDC
    IDC = 1 - I

    return IDC



def optimizeIAC(t, PIA, DIA, MID):

    """
    ============================================================================
    OPTIMIZEIAC
    ============================================================================
    """

    # Define importance of getting the right integral values
    weight_I = 100

    load = lambda x:(
            abs(t[np.argmax(IAC(t = t, f_params = [x[0], x[1], x[2]]))] - PIA) +
            abs(IAC(t = t, f_params = [x[0], x[1], x[2]])[DIA]) +
            weight_I * abs(1.0 - integrate(t = t,
                                           f = IAC,
                                           f_params = [x[0], x[1], x[2]])) +
            weight_I * abs(0.5 - integrate(t = t[0:(MID * len(t) / DIA)],
                                           f = IAC,
                                           f_params = [x[0], x[1], x[2]])))

    optimized_f_params = scipy.optimize.fmin(func = load,
                                           x0 = [15.0, 4.0, 4.0],
                                           maxiter = 5000,
                                           maxfun = 5000)

    print "Optimized function parameters: " + str(optimized_f_params)

    return optimized_f_params



def plotIAC(t, f_params, PIA, DIA, MID):

    """
    ============================================================================
    PLOTIAC
    ============================================================================
    """

    # Extract optimized parameters
    a = f_params[0]
    b = f_params[1]
    c = f_params[2]

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
    plt.plot(t, IAC(t = t, f_params = f_params),
             ls = "-", lw = 1.5, c = "grey",
             label = "IAC: " + r"$f(t) = a \cdot x^b \cdot e^{-c \cdot t}$, " +
                     "with $[a, b, c]$ = [" + str(round(a, 1)) + ", " +
                     str(round(b, 1)) + ", " + str(round(c, 1)) + "]")
    plt.plot(t, IDC(t = t, f_params = f_params),
             ls = "-", lw = 1.5, c = "blue",
             label = "IDC: " + r"$\int$" + " " + r"$f(t) \cdot dt$")

    # Define plot legend
    legend = plt.legend(title = "Insulin activity and decay curves", loc = 1,
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
    MID = 2.0
    N = 1000

    t = np.linspace(0, DIA, N)

    f_params = optimizeIAC(t = t,
                           PIA = PIA,
                           DIA = DIA,
                           MID = MID)

    plotIAC(t = t,
            f_params = f_params,
            PIA = PIA,
            DIA = DIA,
            MID = MID)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
