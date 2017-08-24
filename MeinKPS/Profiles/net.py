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
import base



class NetProfile(base.PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(NetProfile, self).__init__()

        # Define units
        self.u = "U/h"



    def build(self, start, end, basal, TB, suspend, resume, bolus = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

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
        self = resume.subtract(suspend)

        # Give user info
        print "Net insulin profile:"

        # Show it
        self.show()