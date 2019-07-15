#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    profile_test

    Author:   David Leclerc

    Version:  0.1

    Date:     15.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import pytest



# USER LIBRARIES
from profile import Profile



# TESTS
def test_define_start_end():

    """
    Profile start/end times can only be datetime objects. Profiles always start
    one day before start date.
    """

    n = 3
    start = datetime.datetime(1990, 1, 1, 0, 0, 0)
    end = start + datetime.timedelta(days = n - 1)

    dayRange = [i - 1 for i in range(n + 1)]
    days = [(start + datetime.timedelta(days = d)).date() for d in dayRange]

    p = Profile()

    with pytest.raises(TypeError):
        p.define(0, 1)

    with pytest.raises(TypeError):
        p.define(start.date(), end.date())
        
    p.define(start, end)

    assert p.days == days and p.start == start and p.end == end



def test_missing_load():

    """
    Basic implementation of Profile object misses load method.
    """

    n = 3
    start = datetime.datetime(1990, 1, 1, 0, 0, 0)
    end = start + datetime.timedelta(days = n - 1)

    p = Profile()

    with pytest.raises(NotImplementedError):
        p.define(start, end)
        p.load()