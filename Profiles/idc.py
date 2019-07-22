#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    idc

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib



class IDC(object):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Warning: all IDC curves take NEGATIVE time input! For example, if
                     it has been 2 hours since a bolus has been given, then the
                     corresponding time of said bolus is given by t = -2.
        """

        # Define DIA
        self.DIA = float(DIA)

        # Define plot limits
        self.xlim = [-self.DIA, 0]
        self.ylim = [0, 1]



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Gives fraction of active insulin remaining in body t hours after
            enacting it.
        """

        raise NotImplementedError



    def F(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: implicit integration of IDC. Only makes sense when taking dF.
        """

        raise NotImplementedError



    def correct(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CORRECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Bring back given time within insulin's range of action.
        """

        # If too old
        if t < -self.DIA:

            # Bring it back up
            t = -self.DIA

        # If too new: bring it back down
        elif t > 0:
            raise ValueError("Given insulin age is too new.")

        # Return verified time
        return t



    def plot(self, show = True, color = "black", n = 1, size = [1, 1]):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define subplot
        ax = plt.subplot(size[0], size[1], n)

        # Define title
        title = "IDCs"

        # Define axis labels
        x = "(h)"
        y = "(-)"

        # Define subplot label
        label = self.__class__.__name__

        # Subplots
        if size[0] > 1 or size[1] > 1:

            # Title of each subplot corresponds to its label
            title = label

        # Set title
        ax.set_title(title, fontweight = "semibold")

        # Set axis labels
        ax.set_xlabel(x)
        ax.set_ylabel(y)

        # Set axis limits
        ax.set_xlim(self.xlim)
        ax.set_ylim(self.ylim)

        # Compute axes
        t = np.linspace(-self.DIA, 0, 100)
        y = np.vectorize(self.f)(t)

        # Add data to plot
        ax.plot(t, y, lw = 2, ls = "-", label = label, c = color)

        # Single plot: show legend
        if size == [1, 1]:
            ax.legend()

        # Ready to show?
        if show:
            plt.show()



class FourthOrderIDC(IDC):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Modelization of IDC as a 4th-order polynomial.
        """

        # Start initialization
        super(FourthOrderIDC, self).__init__(DIA)

        # Initialize 4th-order parameters
        self.m0 = None
        self.m1 = None
        self.m2 = None
        self.m3 = None
        self.m4 = None



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Gives fraction of active insulin remaining in body t hours after
            enacting it.
        """

        # Correct time
        t = self.correct(t)

        # Compute f(t) of IDC
        f = (self.m4 * t ** 4 +
             self.m3 * t ** 3 +
             self.m2 * t ** 2 +
             self.m1 * t ** 1 +
             self.m0)

        # Return it
        return f



    def F(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: implicit integration of IDC. Only makes sense when taking dF.
        """

        # Correct time
        t = self.correct(t)

        # Compute F(t) of IDC
        F = (self.m4 * t ** 5 / 5 +
             self.m3 * t ** 4 / 4 +
             self.m2 * t ** 3 / 3 +
             self.m1 * t ** 2 / 2 +
             self.m0 * t ** 1 / 1)

        # Return it
        return F



class TriangleModelIDC(IDC):

    def __init__(self, DIA, PIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Modelization of IDC based on a triangle IAC. The IAC is given by the
            following formula (with negative times since injection):

                IAC(t) = m_0 * t + b_0 for t = [-DIA, -PIA]
                         m_1 * t + b_1 for t = [-PIA, 0]

            where the units of IAC are given by [/h].

            We assume that the IDC is given by the integral of the IAC:

                IDC(t) = S IAC(t) * dt
                       = m_0 * t ** 2 / 2 + b_0 * t + c_0 for t = [-DIA, -PIA]
                         m_1 * t ** 2 / 2 + b_1 * t + c_1 for t = [-PIA, 0]

            where S represents an integral on time t.
        """

        # Start initialization
        super(TriangleModelIDC, self).__init__(DIA)

        # Define PIA
        self.PIA = float(PIA)

        # Compute value of IAC at peak of action [y0 = IAC(PIA)] using
        # normalization: S IAC(t) * dt = 1
        self.y0 = 2 / self.DIA

        # Define coefficients for t = [-DIA, -PIA]
        self.m0 = self.y0 / (self.DIA - self.PIA)
        self.b0 = self.m0 * self.DIA
        self.c0 = self.DIA * (self.b0 - self.m0 * self.DIA / 2)

        # Define coefficients for t = [-PIA, 0]
        self.m1 = -self.y0 / self.PIA
        self.b1 = 0
        self.c1 = 1



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Gives fraction of active insulin remaining in body t hours after
            enacting it.
        """

        # Correct time
        t = self.correct(t)

        # From -DIA to PIA
        if -self.DIA <= t <= -self.PIA:

            # Link coefficients
            m = self.m0
            b = self.b0
            c = self.c0

        # From PIA to 0
        elif -self.PIA < t <= 0:

            # Link coefficients
            m = self.m1
            b = self.b1
            c = self.c1

        # Compute IDC(t)
        f = m * t ** 2 / 2 + b * t + c

        # Return it
        return f



    def F(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: implicit integration of IDC. Only makes sense when taking dF.

            The integration of the piecewise IDC is based on the following rule:

                S_a^b f(t) * dt = S_u^b f(t) * dt - S_u^a f(t) * dt

            where S_a^b represents the integral on time of f(t) from a to b.
        """

        # Define integral
        def I(t, m, b, c):
            return m * t ** 3 / 6 + b * t ** 2 / 2 + c * t

        # Correct time
        t = self.correct(t)

        # Initialize result
        F = 0

        # From -DIA to PIA
        if -self.DIA <= t <= -self.PIA:

            # Define reference point
            T = -self.DIA

            # Link coefficients
            m = self.m0
            b = self.b0
            c = self.c0

        # From PIA to 0
        elif -self.PIA < t <= 0:

            # Define reference point
            T = -self.PIA

            # Link coefficients
            m = self.m1
            b = self.b1
            c = self.c1

            # Add first part of integral
            F += self.F(T)

        # Compute it
        F += I(t, m, b, c) - I(T, m, b, c)

        # Return it
        return F



class WalshIDC(FourthOrderIDC):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(WalshIDC, self).__init__(DIA)

        # Define parameters of IDC for various DIA
        if DIA == 3:

            self.m4 = -4.151e-2
            self.m3 = -2.925e-1
            self.m2 = -6.332e-1
            self.m1 = -5.553e-2
            self.m0 = 9.995e-1

        elif DIA == 4:

            self.m4 = -4.290e-3
            self.m3 = -5.465e-2
            self.m2 = -1.984e-1
            self.m1 = 5.452e-2
            self.m0 = 9.995e-1

        elif DIA == 5:

            self.m4 = -3.823e-3
            self.m3 = -5.011e-2
            self.m2 = -1.998e-1
            self.m1 = -2.694e-2
            self.m0 = 9.930e-1

        elif DIA == 6:

            self.m4 = -1.935e-3
            self.m3 = -3.052e-2
            self.m2 = -1.474e-1
            self.m1 = -3.819e-2
            self.m0 = 9.970e-1

        # Bad DIA
        else:
            raise ValueError("Bad DIA: " + str(DIA))



class FiaspIDC(TriangleModelIDC):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Set peak of insulin action at a 6th of the DIA by default. For
            example, if the insulin action lasts 6 hours, then the peak of
            action would be presumed to be at 1 hour after injection.
        """

        # Start initialization
        super(FiaspIDC, self).__init__(DIA, DIA / 6.0)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Define time references
    DIA = 5.0

    # Instanciate IDC
    NovoRapid = WalshIDC(DIA)
    Fiasp = FiaspIDC(DIA)

    # Show it
    lib.initPlot()
    NovoRapid.plot(False, "orange")
    Fiasp.plot(True, "#99e500")
    #NovoRapid.plot(False, "orange", 1, [2, 1])
    #Fiasp.plot(True, "#99e500", 2, [2, 1])



# Run this when script is called from terminal
if __name__ == "__main__":
    main()