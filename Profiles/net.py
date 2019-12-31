#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    net

    Author:   David Leclerc

    Version:  0.1

    Date:     24.08.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# USER LIBRARIES
import logger
from step import StepProfile
from past import PastProfile
from basal import Basal
from tb import TB
from bolus import Bolus
from suspend import Suspend
from resume import Resume



# Instanciate logger
Logger = logger.Logger("Profiles.net")



class Net(PastProfile, StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(Net, self).__init__()

        # Define units
        self.units = "U/h"



    def build(self, start, end, useBoluses = True, show = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Build a net insulin profile by subtracting basals to temporary
            basals, then adding boluses (as a step profile). Use the resume and
            suspend profiles to adjust the result:

                - RESUME -> SUSPEND
                  When insulin is being delivered, use the above described net
                  insulin profile.

                - SUSPEND -> RESUME
                  When insulin delivery is suspended, use a negative version of
                  the basal profile as the net insulin profile.
        """

        # Info
        Logger.debug("Building: " + repr(self))

        # Reset components
        self.reset()

        # Define time references of profile
        self.define(start, end)

        # Instanciate needed profiles
        profiles = {"Basal": Basal(),
                    "TB": TB(),
                    "Bolus": Bolus(),
                    "Suspend": Suspend(),
                    "Resume": Resume(),
                    "NetBasal": None}

        # Build basal profile, as well as TB profile, using the former to fill
        # the latter
        profiles["Basal"].build(start, end)
        profiles["TB"].build(start, end, profiles["Basal"])

        # Compute net basal by subtracting TBs and basal
        profiles["NetBasal"] = profiles["TB"].subtract(profiles["Basal"])

        # If bolus need to be considered: build corresponding step profile and
        # add it to net basal one
        if useBoluses:
            profiles["Bolus"].build(start, end)
            profiles["NetBasal"] = profiles["NetBasal"].add(profiles["Bolus"])

        # Build a suspend and resume profiles, filling the former with basals,
        # and the latter with net basals
        profiles["Suspend"].build(start, end, profiles["Basal"])
        profiles["Resume"].build(start, end, profiles["NetBasal"])

        # Build the final net insulin profile
        net = profiles["Resume"].subtract(profiles["Suspend"])

        # Assign components
        self.T = net.T
        self.t = net.t
        self.y = net.y

        # Show it
        if show:
            self.show()