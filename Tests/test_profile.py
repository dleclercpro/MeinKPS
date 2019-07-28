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
import lib
import path
import reporter
from Profiles import profile, step, dot, past, future



# TEST MODULES
import test_reporter



# CLASSES
class Profile(profile.Profile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(Profile, self).__init__()

        self.src = path.TESTS



class PastProfile(past.PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(PastProfile, self).__init__()

        self.src = path.TESTS
        self.reportType = test_reporter.DatedReport
        self.branch = []



class StepProfile(step.StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(StepProfile, self).__init__()

        self.src = path.TESTS



# FIXTURES
@pytest.fixture
def setup_and_teardown():

    """
    Setup and teardown for tests which store reports.
    """

    reporter.resetReports()
    path.TESTS.touch()
    yield
    path.TESTS.delete()



# TESTS
def test_define(setup_and_teardown):

    """
    Create a profile and define its time references.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0),
                 datetime.datetime(1970, 1, 4, 0, 0, 0),
                 datetime.datetime(1970, 1, 5, 0, 0, 0)]

    # Create profile
    p = Profile()

    # Try defining its time references with numbers
    with pytest.raises(TypeError):
        p.define(0, 1)

    # Try with dates
    with pytest.raises(TypeError):
        p.define(datetimes[0].date(), datetimes[-1].date())

    # Try defining with wrong ordered datetimes
    with pytest.raises(ValueError):
        p.define(datetimes[-1], datetimes[0])

    # Try defining point-like profile
    with pytest.raises(ValueError):
        p.define(datetimes[0], datetimes[0])
    
    # Define correct time references
    p.define(datetimes[1], datetimes[-1])

    # Check profile's start/end times
    assert p.start == datetimes[1] and p.end == datetimes[-1]

    # Check day range: it should start one day before the given start datetime
    assert p.days == [d.date() for d in datetimes]



def test_load(setup_and_teardown):

    """
    Create a profile and load its data.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 23, 30, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 30, 0),
                 datetime.datetime(1970, 1, 2, 1, 0, 0)]

    values = [6.2, 6.0, 5.8, 5.6]

    # Create dated entries
    reporter.setDatedEntries(test_reporter.DatedReport, [],
        dict(zip(datetimes, values)), path.TESTS)

    # Create profile with no loading method implemented
    p = Profile()

    # Try loading
    with pytest.raises(NotImplementedError):
        p.load()

    # Create a past profile (for its existing load method) and define its time
    # references (exclude first and last datetimes)
    p = PastProfile()
    p.define(datetimes[1], datetimes[-1])

    # Load its data using previously generated test dated reports
    p.load()

    # One day before start of profile should have been added to its days
    assert p.data == dict(zip([lib.formatTime(d) for d in datetimes], values))



def test_decouple(setup_and_teardown):

    """
    Create a profile, give it loaded data and decouple it into time and value
    axes.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 23, 30, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 30, 0),
                 datetime.datetime(1970, 1, 2, 1, 0, 0)]

    values = [6.2, 6.0, 5.8, 5.6]

    # Create profile
    p = Profile()
    p.data = dict(zip([lib.formatTime(d) for d in datetimes], values))

    # Decouple its data
    p.decouple()

    # Check profile axes
    assert p.T == datetimes and p.y == values



def test_inject(setup_and_teardown):

    """
    ...
    """

    # TODO
    assert True



def test_cut(setup_and_teardown):

    """
    Create a profile and cut off some of its data (outside some given time
    range).
    """

    datetimes = [datetime.datetime(1970, 1, 1, 23, 30, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 30, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 30, 0),
                 datetime.datetime(1970, 1, 4, 0, 0, 0)]

    values = [6.2, 6.0, 5.8, 5.6, 5.4, 5.2]

    # Create profile
    p = Profile()
    p.T = datetimes
    p.y = values
    p.start = datetimes[1]
    p.end = datetimes[-1]

    # Cut it
    [_, _, last] = p.cut()

    # First entry should be cut off
    assert last == values[0]
    assert p.T == datetimes[1:] and p.y == values[1:]

    # Rewrite profile
    p.T = datetimes
    p.y = values

    # Cut with given datetimes
    [_, _, last] = p.cut(datetimes[2], datetimes[-2])

    # First two entries and last one should be cut off
    assert last == values[1]
    assert p.T == datetimes[2:-1] and p.y == values[2:-1]



def test_pad(setup_and_teardown):

    """
    ...
    """

    # TODO
    assert True



def test_fill(setup_and_teardown):

    """
    ...
    """

    # TODO
    assert True



def test_smooth(setup_and_teardown):

    """
    Create a step profile with redundant steps, then smooth it.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 1, 0, 0),
                 datetime.datetime(1970, 1, 1, 2, 0, 0),
                 datetime.datetime(1970, 1, 1, 3, 0, 0),
                 datetime.datetime(1970, 1, 1, 4, 0, 0),
                 datetime.datetime(1970, 1, 1, 5, 0, 0),
                 datetime.datetime(1970, 1, 1, 6, 0, 0),
                 datetime.datetime(1970, 1, 1, 7, 0, 0),
                 datetime.datetime(1970, 1, 1, 8, 0, 0),
                 datetime.datetime(1970, 1, 1, 9, 0, 0),
                 datetime.datetime(1970, 1, 1, 10, 0, 0),
                 datetime.datetime(1970, 1, 1, 11, 0, 0),
                 datetime.datetime(1970, 1, 1, 12, 0, 0)]

    values = [6.2, 6.2, 6.0, 6.0, 6.0, 5.4, 5.2, 5.2, 5.8, 6.0, 6.2, 6.2]

    smoothedDatetimes = [datetime.datetime(1970, 1, 1, 1, 0, 0),
                         datetime.datetime(1970, 1, 1, 3, 0, 0),
                         datetime.datetime(1970, 1, 1, 6, 0, 0),
                         datetime.datetime(1970, 1, 1, 7, 0, 0),
                         datetime.datetime(1970, 1, 1, 9, 0, 0),
                         datetime.datetime(1970, 1, 1, 10, 0, 0),
                         datetime.datetime(1970, 1, 1, 11, 0, 0),
                         datetime.datetime(1970, 1, 1, 12, 0, 0)]

    smoothedValues = [6.2, 6.0, 5.4, 5.2, 5.8, 6.0, 6.2, 6.2]

    # Create profile
    p = StepProfile()
    p.T = datetimes
    p.y = values

    # Smooth it
    p.smooth()

    # No redundant steps allowed in smoothed profile
    assert p.T == smoothedDatetimes and p.y == smoothedValues



def test_normalize(setup_and_teardown):

    """
    Create a profile, then normalize its time axis.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 23, 30, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 30, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 30, 0),
                 datetime.datetime(1970, 1, 4, 0, 0, 0)]

    values = [6.2, 6.0, 5.8, 5.6, 5.4, 5.2]

    # Create profile and define its norm
    p = Profile()
    p.T = datetimes
    p.y = values
    p.norm = p.T[-1]

    # Normalize it
    p.normalize()

    # Check normalization
    assert p.t == [lib.normalizeTime(T, p.norm) for T in p.T]