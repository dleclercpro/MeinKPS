#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    IDC

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import errors



class FourthOrderIDC(object):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Modelization of IDC as a 4th-order polynomial.
        """

        # Initialize 4th-order parameters
        self.m0 = None
        self.m1 = None
        self.m2 = None
        self.m3 = None
        self.m4 = None

        # Define DIA
        self.DIA = DIA



    def verify(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify that given time is within insulin's range of action.
        """

        # If too old
        if t < -self.DIA:

            # Bring it back up
            t = -self.DIA

        # If too new
        elif t > 0:

            # Bring it back down
            t = 0

        # Return verified time
        return t



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Gives fraction of active insulin remaining in body t hours after
            enacting it. Takes negative input!
        """

        # Verify time
        t = self.verify(t)

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
        """

        # Verify time
        t = self.verify(t)

        # Compute F(t) of IDC
        F = (self.m4 * t ** 5 / 5 +
             self.m3 * t ** 4 / 4 +
             self.m2 * t ** 3 / 3 +
             self.m1 * t ** 2 / 2 +
             self.m0 * t ** 1 / 1)

        # Return it
        return F



class TriangleIDC(object):

    def __init__(self, DIA, PIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Modelization of IDC based on a triangle IAC.
        """

        # Define DIA
        self.DIA = float(DIA)

        # Define PIA
        self.PIA = float(PIA)

        # Define coefficients
        self.y0 = 2 / self.DIA
        self.m0 = self.y0 / (self.DIA - self.PIA)
        self.m1 = -self.y0 / self.PIA
        self.b0 = self.m0 * self.DIA
        self.b1 = 0

        # Define integrals
        self.I = lambda t, m, b: m * t ** 2 / 2 + b * t
        self.II = lambda t, m, b: m * t ** 3 / 6 + b * t ** 2 / 2



    def verify(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify that given time is within insulin's range of action.
        """

        # If too old
        if t < -self.DIA:

            # Bring it back up
            t = -self.DIA

        # If too new
        elif t > 0:

            # Bring it back down
            t = 0

        # Return verified time
        return t



    def f(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Gives fraction of active insulin remaining in body t hours after
            enacting it. Takes negative input!
        """

        # Verify time
        t = self.verify(t)

        # Initialize result
        f = 0

        # From -DIA to PIA
        if -self.DIA <= t <= -self.PIA:

            # Define reference point
            T = -self.DIA

            # Link coefficients
            m = self.m0
            b = self.b0

        # From PIA to 0
        elif -self.PIA < t <= 0:

            # Define reference point
            T = -self.PIA

            # Link coefficients
            m = self.m1
            b = self.b1

            # Add first part of integral
            f += self.f(T)

        # Compute it
        f += self.I(t, m, b) - self.I(T, m, b)

        # Return it
        return f



    def F(self, t):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            F
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Verify time
        t = self.verify(t)

        # Initialize result
        F = 0

        # From -DIA to PIA
        if -self.DIA <= t <= -self.PIA:

            # Define reference point
            T = -self.DIA

            # Link coefficients
            m = self.m0
            b = self.b0

        # From PIA to 0
        elif -self.PIA < t <= 0:

            # Define reference point
            T = -self.PIA

            # Link coefficients
            m = self.m1
            b = self.b1

            # Add first part of integral
            F += self.f(T) * t - self.f(T) * T + self.F(T)

        # Compute it
        F += (self.II(t, m, b) - self.II(T, m, b) -
              (self.I(T, m, b) * t - self.I(T, m, b) * T))

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
        super(self.__class__, self).__init__(DIA)

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

            # Raise error
            raise errors.BadDIA(DIA)



class FiaspIDC(TriangleIDC):

    def __init__(self, DIA):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(self.__class__, self).__init__(DIA, DIA / 6.0)
