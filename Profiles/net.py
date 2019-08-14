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



    def build(self, start, end, suspend, resume, basal, TB, bolus = None,
        show = False):

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

        # Build basal profile, as well as TB profile, using the former to fill
        # the latter
        basal.build(start, end)
        TB.build(start, end, basal)

        # Compute net basal by subtracting TBs and basal
        netBasal = TB.subtract(basal)

        # If bolus profile given: build a corresponding step profile and add it
        # to net basal
        if bolus is not None:
            bolus.build(start, end)
            netBasal = netBasal.add(bolus)

        # Build a suspend and resume profiles, filling the former with basals,
        # and the latter with net basals
        suspend.build(start, end, basal)
        resume.build(start, end, netBasal)

        # Build the final net insulin profile
        net = resume.subtract(suspend)

        # Assign components
        self.T = net.T
        self.t = net.t
        self.y = net.y

        # Show it
        if show:
            self.show()