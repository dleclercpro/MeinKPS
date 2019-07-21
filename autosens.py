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

# LIBRARIES
import datetime
import numpy as np
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import fmt
import calculator
from Profiles import (bg, basal, tb, bolus, net, isf, csf, iob, cob, targets,
    suspend, resume, idc)



def autosens(self, now, DIA, t = 24):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            AUTOSENS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define past reference time
        past = now - datetime.timedelta(hours = t)

        # Define DIA as a datetime timedelta object
        dia = datetime.timedelta(hours = DIA)

        # Instanciate profiles
        profiles = {"IDC": idc.WalshIDC(DIA),
                    "Suspend": None,
                    "Resume": None,
                    "Basal": None,
                    "TB": None,
                    "Bolus": None,
                    "Net": None,
                    "PastISF": isf.PastISF(),
                    "PastBG": bg.PastBG()}

        # Build past BG profile
        profiles["PastBG"].build(past, now)
        
        # Build past ISF profile
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

            # Reset necessary profiles
            profiles["Suspend"] = suspend.Suspend()
            profiles["Resume"] = resume.Resume()
            profiles["Basal"] = basal.Basal()
            profiles["TB"] = tb.TB()
            profiles["Bolus"] = bolus.Bolus()
            profiles["Net"] = net.Net()

            # Build net insulin profile
            profiles["Net"].build(T[i] - dia, T[i], profiles["Suspend"],
                                                    profiles["Resume"],
                                                    profiles["Basal"], 
                                                    profiles["TB"],
                                                    profiles["Bolus"])

            # Do it
            IOBs.append(calculator.computeIOB(profiles["Net"], profiles["IDC"]))

            # Show IOB
            print "IOB(" + lib.formatTime(T[i]) + ") = " + fmt.IOB(IOBs[-1])

        # Initialize dBG deviations
        ddBGs = []

        # Go through IOB and find difference between expected dBG and actual one
        for i in range(n - 1):

            # Compute dIOB
            dIOB = IOBs[i + 1] - IOBs[i]

            # Compute dBG
            dBG = profiles["PastBG"].y[i + 1] - profiles["PastBG"].y[i]
            expecteddBG = dIOB * profiles["PastISF"].f(t[i])

            # Compute delta dBG
            ddBGs.append(dBG - expecteddBG)

            # Avoid division by zero
            if not expecteddBG == 0:

                # Compute dBG ratio
                r = round(dBG / float(expecteddBG), 2)

            # Otherwise
            else:

                # No ratio available
                r = None

            # Info
            print "dIOB: " + fmt.IOB(dIOB)
            print "dBG: " + fmt.BG(dBG)
            print "Expected dBG: " + fmt.BG(expecteddBG)
            print "ddBG: " + fmt.BG(ddBGs[i])
            print "r: " + str(r)
            print

        # Plot
        print "Mean ddBG: " + fmt.BG(np.mean(ddBGs))
        lib.initPlot()
        ax = plt.subplot(1, 1, 1)

        # Define axis labels
        x = "(h)"
        y = "(mmol/L)"

        # Set title
        ax.set_title("dBG Deviations", fontweight = "semibold")

        # Set axis labels
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.plot(t[:-1], ddBGs, marker = "o", ms = 3.5, lw = 0, c = "red")
        plt.show()