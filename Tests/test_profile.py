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

        super(Profile, self).__init__()
        
        self.src = path.TESTS



class PastProfile(past.PastProfile):

    def __init__(self):

        super(PastProfile, self).__init__()

        self.src = path.TESTS
        self.reportType = test_reporter.DatedReport



class StepProfile(step.StepProfile):

    def __init__(self):

        super(StepProfile, self).__init__()

        self.src = path.TESTS



# FIXTURES
@pytest.fixture
def setup_and_teardown():

    """
    Setup and teardown for tests which store reports.
    """

    reporter.reset()
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
    Inject steps in profile according to given step durations. Tests 4 cases:
        - Step ends before start of next one (new step injected)
        - Step ends after start of next one (nothing to do)
        - Step is a canceling one (value is replaced by profile's zero value)
        - Step is at the end of profile (new step injected at the end) 
    """

    def date(h = 0, m = 0, s = 0):
        d = datetime.datetime(1970, 1, 1)
        return d.replace(hour = h, minute = m, second = s)

    datetimes = [date(0, 0),
                 date(1, 0),
                 date(1, 30),
                 date(2, 0),
                 date(3, 0)]

    values = [6.2, 6.0, 5.8, 5.6, 5.4]

    # Define zero (default y-axis value) for profile
    zero = 1000

    # Define durations for each given step
    durations = [datetime.timedelta(minutes = d) for d in [5, 60, 20, 0, 30]]

    # Define expected axes after injection
    expectedDatetimes = [date(0, 0),
                         date(0, 5),
                         date(1, 0),
                         date(1, 30),
                         date(1, 50),
                         date(2, 0),
                         date(3, 0),
                         date(3, 30)]

    expectedValues = [6.2, zero, 6.0, 5.8, zero, zero, 5.4, zero]

    # Create step profile
    p = StepProfile()

    # Define it
    p.T = datetimes
    p.y = values
    p.durations = durations
    p.zero = zero

    # Inject it with zeros
    p.inject()

    assert p.T == expectedDatetimes and p.y == expectedValues



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
    last = p.cut()

    # First entry should be cut off
    assert last == values[0]
    assert p.T == datetimes[1:] and p.y == values[1:]

    # Rewrite profile
    p.T = datetimes
    p.y = values

    # Cut with given datetimes
    last = p.cut(datetimes[2], datetimes[-2])

    # First two entries and last one should be cut off
    assert last == values[1]
    assert p.T == datetimes[2:-1] and p.y == values[2:-1]



def test_pad(setup_and_teardown):

    """
    Force start/end limits on profile, using (if available) the value of the
    step preceding beginning of profile.
    """

    datetimes = [datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0)]

    values = [6.2, 6.0]

    start = datetime.datetime(1970, 1, 1, 0, 0, 0)
    end = datetime.datetime(1970, 1, 4, 0, 0, 0)
    last = 0
    zero = 1000

    # Create empty profile
    p = StepProfile()

    # Pad it
    p.pad(start, end, last)

    assert p.T[0] == start and p.T[-1] == end
    assert p.y[0] == last and p.y[-1] == last

    # Create profile
    p = StepProfile()
    p.T = datetimes
    p.y = values

    # Pad it
    p.pad(start, end, last)

    assert p.T[0] == start and p.T[-1] == end
    assert p.y[0] == last and p.y[-1] == values[-1]

    # Create profile with a specific zero value
    p = StepProfile()
    p.T = datetimes
    p.y = values
    p.zero = zero

    # Pad it without last value
    p.pad(start, end)

    assert p.T[0] == start and p.T[-1] == end
    assert p.y[0] == zero and p.y[-1] == values[-1]



def test_fill(setup_and_teardown):

    """
    Create a step profile with holes and fill them using a filler profile.
    """

    def date(h = 0, m = 0, s = 0):
        d = datetime.datetime(1970, 1, 1)
        return d.replace(hour = h, minute = m, second = s)

    fillerDatetimes = [[date(1, 30),
                        date(2, 30),
                        date(3, 30),
                        date(4, 30)],
                       [date(1, 0),
                        date(2, 0),
                        date(3, 0),
                        date(4, 0)]]

    fillerValues = [[150.0, 100.0, 50.0, 75.0],
                    [100.0, 50.0, 50.0, 100.0]]

    expectedDatetimes = [[date(1, 0),
                          date(2, 0),
                          date(2, 30),
                          date(3, 30),
                          date(4, 0),
                          date(5, 0)],
                         [date(1, 0),
                          date(2, 0),
                          date(3, 0),
                          date(4, 0),
                          date(5, 0)]]

    expectedValues = [[6.0, 150.0, 100.0, 50.0, 5.8, 5.8],
                      [6.0, 50.0, 50.0, 5.8, 5.8]]

    # Test data on profile with a hole in the middle
    for i in range(len(expectedValues)):

        # Create profile
        p = StepProfile()
        p.T = [date(1, 0), date(2, 0), date(4, 0), date(5, 0)]
        p.y = [6.0, None, 5.8, 5.8]

        # Create filler
        filler = StepProfile()
        filler.T = fillerDatetimes[i]
        filler.y = fillerValues[i]

        # Fill profile
        p.fill(filler)

        # Every value on the y-axis should be defined, and expectations should
        # be met
        assert all([y is not None for y in p.y])
        assert p.T == expectedDatetimes[i] and p.y == expectedValues[i]



def test_smooth(setup_and_teardown):

    """
    Create a step profile with redundant steps, then smooth it.
    """

    def date(h = 0, m = 0, s = 0):
        d = datetime.datetime(1970, 1, 1)
        return d.replace(hour = h, minute = m, second = s)

    datetimes = [date(1, 0),
                 date(2, 0),
                 date(3, 0),
                 date(4, 0),
                 date(5, 0),
                 date(6, 0),
                 date(7, 0),
                 date(8, 0),
                 date(9, 0),
                 date(10, 0),
                 date(11, 0),
                 date(12, 0)]

    values = [6.2, 6.2, 6.0, 6.0, 6.0, 5.4, 5.2, 5.2, 5.8, 6.0, 6.2, 6.2]

    smoothedDatetimes = [date(1, 0),
                         date(3, 0),
                         date(6, 0),
                         date(7, 0),
                         date(9, 0),
                         date(10, 0),
                         date(11, 0),
                         date(12, 0)]

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