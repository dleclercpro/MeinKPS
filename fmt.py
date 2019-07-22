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
    return "{:.1f}".format(x) + " mmol/L"

def BGI(x):
    return "{:.1f}".format(x) + " mmol/L/h"

def basal(x):
    return "{:.3f}".format(x) + " U/h"

def bolus(x):
    return "{:.3f}".format(x) + " U"

def ISF(x):
    return "{:.1f}".format(x) + " mmol/L/U"

def CSF(x):
    return "{:.0f}".format(x) + " g/U"

def IOB(x):
    return "{:.1f}".format(x) + " U"

def COB(x):
    return "{:.0f}".format(x) + " g"

def TB(TB):
    return ("{:.3f}".format(TB["Rate"]) + " " + TB["Units"] + " " +
        "(" + "{:.0f}".format(TB["Duration"]) + " m)")

def frequency(f):
    return "{:.3f}".format(f) + " MHz"

def frequencyRange(f1, f2):
    return "[" + "{:.3f}".format(f1) + ", " + "{:.3f}".format(f2) + "] MHz"