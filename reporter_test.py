#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    reporter_test

    Author:   David Leclerc

    Version:  0.1

    Date:     07.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import datetime
import pytest



# USER LIBRARIES
import lib
import reporter



# FUNCTIONS



# TESTS
def test_merge():

    """
    Merge dicts.
    """

    a = { "A": 0 }
    b = { "B": 1 }
    c = { "A": 0, "B": 1 }

    assert lib.merge(a, b) == c



def test_merge_recursive():

    """
    Merge dicts recursively.
    """

    a = {
        "A": 0,
        "B": {
            "C": 1
        }
    }
    b = {
        "B": {
            "D": 2
        }
    }
    c = {
        "A": 0,
        "B": {
            "C": 1,
            "D": 2
        }
    }

    assert lib.merge(a, b) == c



def test_merge_value_conflit():

    """
    Merge dicts with value conflict.
    """

    a = {
        "A": 0,
        "B": 1
    }
    b = {
        "A": 1,
        "C": 2
    }

    with pytest.raises(ValueError):
        lib.merge(a, b)



def test_merge_type_conflit():

    """
    Merge dicts with type conflict.
    """

    a = {
        "A": 0,
        "B": 1
    }
    b = {
        "A": 0,
        "B": {
            "C": 2
        }
    }
    c = {
        "A": 0,
        "B": [
            "C"
        ]
    }

    with pytest.raises(TypeError):
        lib.merge(a, b)

    with pytest.raises(TypeError):
        lib.merge(a, c)



def test_merge_bad_types():

    """
    Merge non dicts.
    """

    with pytest.raises(TypeError):
        lib.merge({}, [])

    with pytest.raises(TypeError):
        lib.merge([], {})

    with pytest.raises(TypeError):
        lib.merge([], [])

    with pytest.raises(TypeError):
        lib.merge({}, "Test")

    with pytest.raises(TypeError):
        lib.merge("Test", {})

    with pytest.raises(TypeError):
        lib.merge("Test", "Test")