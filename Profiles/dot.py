#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    dot

    Author:   David Leclerc

    Version:  0.2

    Date:     31.08.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger
from .profile import Profile



# Define instances
Logger = logger.Logger("Profiles.dot")



class DotProfile(Profile):

    def build(self, start, end, show = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start building
        super(DotProfile, self).build(start, end)

        # Cut entries outside of time limits
        self.cut()

        # Normalize profile
        self.normalize()

        # Compute profile derivative
        self.derivate()

        # Show profile
        if show:
            self.show()



    def derivate(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DERIVATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Derivate dot typed profiles using their normalized time axis.
        """

        # Info
        Logger.debug("Derivating: " + repr(self))

        # Derivate
        self.dydt = lib.derivate(self.y, self.t)



    def plot(self, n = 1, size = [1, 1], show = True, title = None,
                   color = "black"):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PLOT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start plotting
        ax = super(DotProfile, self).plot(n, size, title)

        # Add data to plot
        ax.plot(self.t, self.y, label = self.__class__.__name__,
                marker = "o", ms = 3.5, lw = 0, c = color)

        # More than one line: add legend
        if len(ax.lines) > 1:
            ax.legend()

        # Ready to show?
        if show:
            plt.show()