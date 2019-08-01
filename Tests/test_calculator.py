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
import numpy as np
import pytest



# USER LIBRARIES
import lib
import calculator
from Profiles import idc, net



# CONSTANTS
IOB_PRECISION = 0.01



# FUNCTIONS
def isEqual(x, y):

    """
    Custom equality testing function with acceptable precision for IOB values.
    """

    return lib.isEqual(x, y, IOB_PRECISION)



# TESTS
def test_compute_iob_constant_net():

    """
    Test IOB computing for a constant net insulin profile.
    """

    # Define a DIA
    DIA = 3.0

    # Get an IDC
    walsh = idc.WalshIDC(DIA)

    # Create net insulin profile
    netInsulin = net.Net()
    netInsulin.t = [-DIA, 0]
    netInsulin.y = [1, 1]

    expectedIOB = 1.45532

    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)

    # Redefine net insulin profile
    netInsulin.y = [0, 0]

    expectedIOB = 0

    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)



def test_compute_iob_varying_net():

    """
    Test IOB computing for a varying net insulin profile.
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
    walsh3HourDIAIntegrals = np.array([0.129461, 0.444841, 0.881021, 0])

    expectedIOB = np.sum(netInsulin.y * walsh3HourDIAIntegrals)

    IOB = calculator.computeIOB(netInsulin, walsh)

    assert isEqual(IOB, expectedIOB)