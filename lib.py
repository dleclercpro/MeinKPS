#! /usr/bin/python

"""
================================================================================
TITLE:    lib

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     19.05.2016

LICENSE:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

OVERVIEW: This is a script that contains user-defined functions to make the
          communications with the CareLink stick easier.

NOTES:    ...
================================================================================
"""

# Pad an hexadecimal string with zeros
def padHexadecimal(x):

        """
        ========================================================================
        PADHEXADECIMAL
        ========================================================================

        ...
        """

        x = "0x" + x[2:].zfill(2)

        return x
