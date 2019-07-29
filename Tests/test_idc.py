#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    test_idc

    Author:   David Leclerc

    Version:  0.1

    Date:     29.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import pytest



# USER LIBRARIES
import lib
from Profiles import idc



# CONSTANTS
IDC_PRECISION = 0.01



# FUNCTIONS
def isEqual(x, y):

    """
    Custom equality testing function with acceptable precision for IDC values.
    """

    return lib.isEqual(x, y, IDC_PRECISION)



def isValid(idc):

    """
    Check if insulin decay curve (IDC) is valid.
    """

    # Make sure DIA is defined
    assert type(idc.DIA) is float

    # Test at beginning and end
    assert isEqual(idc.f(0), 1) and isEqual(idc.f(-idc.DIA), 0)

    # Test before insulin was given (wrong time)
    with pytest.raises(ValueError):
        idc.f(1)

    # Test after end of insulin action
    assert isEqual(idc.f(-(idc.DIA + 1)), 0)



# TESTS
def test_walsh():

    """
    Specific tests for Walsh IDC.
    """

    # Define DIAs
    DIAs = [3, 4, 5, 6]
    badDIAs = [1, 2, 2.5, 3.5, 4.5, 5.5, 6.5, 7, 8]

    # Define theoretical remaining active insulin after 1h for all valid DIAs
    remainingInsulin = [0.67282, 0.79694, 0.866427, 0.916375]

    # Test bad DIAs
    for dia in badDIAs:
        with pytest.raises(ValueError):
            idc.WalshIDC(dia)

    # Test fractions of active insulin remaining
    for dia, ri in dict(zip(DIAs, remainingInsulin)).items():
        walsh = idc.WalshIDC(dia)

        # Test Walsh IDC
        isValid(walsh)

        # Test after one hour
        assert isEqual(walsh.f(-1), ri)



def test_fiasp():

    """
    Specific tests for Fiasp IDC.
    """

    # Define DIAs
    DIAs = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8]

    # Test fractions of active insulin remaining
    for dia in DIAs:
        fiasp = idc.FiaspIDC(dia)

        # Test Fiasp IDC
        isValid(fiasp)