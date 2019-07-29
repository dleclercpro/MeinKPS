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



# TESTS
def test_fourth_order_idc():

    # Define DIA
    DIA = 5.0



def test_walsh():

    # Define custom equality testing function with acceptable precision
    def isEqual(x, y):
        return lib.isEqual(x, y, 0.01)

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

        # Test at beginning and end
        assert isEqual(walsh.f(0), 1) and isEqual(walsh.f(-dia), 0)

        # Test after one hour
        assert isEqual(walsh.f(-1), ri)