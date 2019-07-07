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
import base



# Instanciate logger
Logger = logger.Logger("Profiles/net.py")



class Net(base.PastProfile, base.StepProfile):

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



    def build(self, start, end, suspend, resume, basal, TB, bolus = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Building 'Net'...")

        # Reset components
        self.reset()

        # Define time references of profile
        self.define(start, end)

        # Build basal profile
        basal.build(start, end)

        # Build TB profile and fill holes with basal
        TB.build(start, end, basal)

        # Compute net basal by subtracting TBs and basal
        netBasal = TB.subtract(basal)

        # If bolus profile given
        if bolus is not None:

            # Build bolus profile
            bolus.build(start, end)

            # Add it to net basal
            netBasal = netBasal.add(bolus)

        # Build suspend profile and fill with basal
        # Negative IOB impact due to suspending pump
        suspend.build(start, end, basal)

        # Build resume profile and fill with net basal 
        resume.build(start, end, netBasal)

        # Build net insulin profile
        net = resume.subtract(suspend)

        # Assign components
        self.T = net.T
        self.t = net.t
        self.y = net.y
        
        # Give user info
        Logger.debug("Net insulin profile:")

        # Show it
        self.show()