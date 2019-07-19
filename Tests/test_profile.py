#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    test_profile

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
import path
import reporter
from Profiles import profile, past



# TEST MODULES
import test_reporter



# CLASSES
class Profile(profile.Profile):

    def __init__(self):

        super(Profile, self).__init__()



class PastProfile(past.PastProfile):

    def __init__(self):

        super(PastProfile, self).__init__()

        self.reportType = test_reporter.DatedReport
        self.branch = []



# FIXTURES
@pytest.fixture
def setup_and_teardown():

    """
    Setup and teardown for tests which store reports.
    """

    path.TESTS.touch()

    yield

    path.TESTS.delete()



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

    # Create profile
    p = Profile()

    # Try defining its time references with numbers
    with pytest.raises(TypeError):
        p.define(0, 1)

    # Try with dates
    with pytest.raises(TypeError):
        p.define(start.date(), end.date())

    # Do it with datetimes
    p.define(start, end)

    # Start/end datetimes, as well as days covered, should be the ones expected
    assert p.days == days and p.start == start and p.end == end



def test_missing_load():

    """
    Basic implementation of Profile object misses load method.
    """

    # Create and define profile
    p = Profile()

    # Try loading with unimplemented method
    with pytest.raises(NotImplementedError):
        p.load()



def test_wrong_time_order():

    """
    Start of profile has to be before its end time.
    """

    start = datetime.datetime(1990, 1, 1, 0, 0, 0)
    end = datetime.datetime(1989, 1, 1, 0, 0, 0)

    # Create profile
    p = Profile()

    # Try defining with wrongly ordered datetimes
    with pytest.raises(ValueError):
        p.define(start, end)

    # Try defining point-like profile
    with pytest.raises(ValueError):
        p.define(start, start)



def test_cut(setup_and_teardown):

    """
    ...
    """

    datetimes = [datetime.datetime(1990, 11, 30, 23, 30, 0),
                 datetime.datetime(1990, 12, 1, 0, 0, 0),
                 datetime.datetime(1990, 12, 1, 0, 30, 0),
                 datetime.datetime(1990, 12, 1, 1, 0, 0),
                 datetime.datetime(1990, 12, 1, 1, 30, 0),
                 datetime.datetime(1990, 12, 1, 2, 0, 0),
                 datetime.datetime(1990, 12, 1, 2, 30, 0),
                 datetime.datetime(1990, 12, 1, 3, 0, 0)]

    values = [6.2, 6.0, 5.8, 5.6, 5.4, 5.2, 5.0]

    entries = dict(zip(datetimes, values))

    branch = []

    # Create dated entries
    reporter.setDatedEntries(test_reporter.DatedReport, branch, entries,
        path.TESTS)

    # Create and define profile
    p = PastProfile()
    p.define(datetimes[1], datetimes[-1])

    # Load and decouple entries
    p.load(src = path.TESTS)
    p.decouple()