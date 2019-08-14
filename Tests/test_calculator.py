#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    test_calculator

    Author:   David Leclerc

    Version:  0.1

    Date:     29.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import pytest



# USER LIBRARIES
import lib
import calculator
import idc
from Profiles import net, isf



# CONSTANTS
IOB_PRECISION = 0.01



# FUNCTIONS
def isEqual(x, y):

    """
    Custom equality testing function with acceptable precision for IOB values.
    """

    return lib.isEqual(x, y, IOB_PRECISION)



# TESTS
def test_compute_iob_single_step_net():

    """
    Test IOB computing for a net insulin profile with a single step.
    """

    # Define a DIA
    DIA = 3.0

    # Get an IDC
    walsh = idc.WalshIDC(DIA)

    # Create net insulin profile
    netInsulin = net.Net()
    netInsulin.t = np.array([-DIA, 0])
    netInsulin.y = np.array([1, 1])

    # Define integral over single step
    walshIntegrals = np.array([1.45532, 0])

    expectedIOB = np.sum(netInsulin.y * walshIntegrals)
    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)

    # Redefine net insulin profile that corresponds to only scheduled basals
    # (there should be no insulin on board)
    netInsulin.t = np.array([-DIA, 0])
    netInsulin.y = [0, 0]

    expectedIOB = 0
    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)



def test_compute_iob_multiple_steps_net():

    """
    Test IOB computing for a net insulin profile with multiple steps.
    """

    # Define a DIA
    DIA = 3.0

    # Get an IDC
    walsh = idc.WalshIDC(DIA)

    # Create net insulin profile
    netInsulin = net.Net()
    netInsulin.t = np.array([-DIA, -2, -1, 0])
    netInsulin.y = np.array([2, -0.5, 3, 1])

    # Define part integrals (one for each step)
    walshIntegrals = np.array([0.129461, 0.444841, 0.881021, 0])

    expectedIOB = np.sum(netInsulin.y * walshIntegrals)
    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)



def test_compute_dose():

    """
    Test the computing of an insulin dose necessary to bring back BG to a given
    target using an IDC and an ISF profile.
    """

    # Define a DIA
    DIA = 5.0

    # Define time references
    now = datetime.datetime(1970, 1, 1, )
    future = now + datetime.timedelta(hours = DIA)

    # Define an ISF profile for the next DIA hours
    ISF = isf.FutureISF()
    ISF.t = [0, DIA]
    ISF.y = [1.5, 1.5]