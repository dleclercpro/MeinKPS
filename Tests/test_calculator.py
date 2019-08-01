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
import pytest



# USER LIBRARIES
import calculator
from Profiles import idc, net



# TESTS
def test_compute_iob():

    """
    Test IOB computing.
    """

    # Define a DIA
    dia = 3.0

    # Get an IDC
    walsh = idc.WalshIDC(dia)

    # Create net insulin profile
    insulin = net.Net()
    insulin.t = [-4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0]
    insulin.y = [10.0, -2.0, -1.5, -1.0, 0.25, 0.005, 5.55, 45.0, 0]

    # Compute IOB
    iob = calculator.computeIOB(insulin, walsh)

    # TODO
    assert True