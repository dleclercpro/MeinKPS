#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    fmt

    Author:   David Leclerc

    Version:  0.1

    Date:     27.10.2018

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains functions that return a given
              quantity as a string with the correct number of digits to display
              as well as corresponding units.

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

def BG(x):
    return str(round(x, 1)) + " mmol/L"

def BGI(x):
    return str(round(x, 1)) + " mmol/L/h"

def basal(x):
    return str(round(x, 1)) + " U/h"

def ISF(x):
    return str(round(x, 1)) + " mmol/L/U"

def CSF(x):
    return str(int(round(x))) + " g/U"

def IOB(x):
    return str(round(x, 1)) + " U"

def COB(x):
    return str(int(round(x))) + " g"