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
import copy
import pytest



# USER LIBRARIES
import lib
import path
import reporter
from Profiles import profile, step, dot, past, future



# TEST MODULES
import test_reporter



# CONSTANTS
DEFAULT_DATE = datetime.datetime(1970, 1, 1)



# FUNCTIONS
def getTime(timeString = "00:00:00", dateString = "1970.01.01"):
    return lib.formatTime(dateString + " - " + timeString)



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
def test_define():

    """
    Create a profile and define its time references.
    """

    datetimes = [getTime(dateString = "1970.01.01"),
                 getTime(dateString = "1970.01.02"),
                 getTime(dateString = "1970.01.03"),
                 getTime(dateString = "1970.01.04"),
                 getTime(dateString = "1970.01.05")]

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

    datetimes = [getTime("23:30:00", "1970.01.01"),
                 getTime("00:00:00", "1970.01.02"),
                 getTime("00:30:00", "1970.01.02"),
                 getTime("01:00:00", "1970.01.02")]

    values = [6.2, 6, 5.8, 5.6]

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



def test_decouple():

    """
    Create a profile, give it loaded data and decouple it into time and value
    axes.
    """

    datetimes = [getTime("23:30:00", "1970.01.01"),
                 getTime("00:00:00", "1970.01.02"),
                 getTime("00:30:00", "1970.01.02"),
                 getTime("01:00:00", "1970.01.02")]

    values = [6.2, 6, 5.8, 5.6]

    # Create profile
    p = Profile()
    p.data = dict(zip([lib.formatTime(d) for d in datetimes], values))

    # Decouple its data
    p.decouple()

    # Check profile axes
    assert p.T == datetimes and p.y == values



def test_inject():

    """
    Inject steps in profile according to given step durations. Tests 4 cases:
        - Step ends before start of next one (new step injected)
        - Step ends after start of next one (nothing to do)
        - Step is a canceling one (value is replaced by profile's zero value)
        - Step is at the end of profile (new step injected at the end) 
    """

    datetimes = [getTime("00:00:00"),
                 getTime("01:00:00"),
                 getTime("01:30:00"),
                 getTime("02:00:00"),
                 getTime("03:00:00")]

    values = [6.2, 6, 5.8, 5.6, 5.4]

    # Define zero (default y-axis value) for profile
    zero = 1000

    # Define durations for each given step
    durations = [datetime.timedelta(minutes = d) for d in [5, 60, 20, 0, 30]]

    # Define expected axes after injection
    expectedDatetimes = [getTime("00:00:00"),
                         getTime("00:05:00"),
                         getTime("01:00:00"),
                         getTime("01:30:00"),
                         getTime("01:50:00"),
                         getTime("02:00:00"),
                         getTime("03:00:00"),
                         getTime("03:30:00")]

    expectedValues = [6.2, zero, 6, 5.8, zero, zero, 5.4, zero]

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



def test_cut():

    """
    Create a profile and cut off some of its data (outside some given time
    range).
    """

    datetimes = [getTime("23:30:00", "1970.01.01"),
                 getTime("00:00:00", "1970.01.02"),
                 getTime("00:30:00", "1970.01.02"),
                 getTime("00:00:00", "1970.01.03"),
                 getTime("00:30:00", "1970.01.03"),
                 getTime("00:00:00", "1970.01.04")]

    values = [6.2, 6, 5.8, 5.6, 5.4, 5.2]

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



def test_pad():

    """
    Force start/end limits on profile, using (if available) the value of the
    step preceding beginning of profile.
    """

    datetimes = [getTime(dateString = "1970.01.02"),
                 getTime(dateString = "1970.01.03")]

    values = [6.2, 6]

    start = getTime(dateString = "1970.01.01")
    end = getTime(dateString = "1970.01.04")
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



def do_test_fill(profile, fillers, expectations):

    """
    Helper function to test filling of profile.
    """

    # Test expectations
    for i in range(len(expectations)):

        # Create step profile with a hole in the middle
        p = StepProfile()
        p.T, p.y = lib.unzip(profile)

        # Create filler
        f = StepProfile()
        f.T, f.y = lib.unzip(fillers[i])

        # Fill profile
        p.fill(f)

        # Every value on the y-axis should be defined
        # Expectations should be met
        assert all([y is not None for y in p.y])
        assert p.T, p.y == lib.unzip(expectations[i])



def test_fill_empty():

    """
    Create a an empty step profile and try filling it with a filler.
    """

    # Create empty profile
    p = StepProfile()

    filler = [(getTime("01:00:00"), 6),
              (getTime("02:00:00"), 5.8),
              (getTime("04:00:00"), 5.6),
              (getTime("05:00:00"), 5.4)]

    # Create filler
    f = StepProfile()
    f.T, f.y = lib.unzip(filler)

    # Fill it
    p.fill(f)

    # Empty profile should be left empty after fill
    assert p.T == [] and p.y == []



def test_fill_start():

    """
    Create a step profile with a hole at the beginning and fill it using a
    filler.

    Filler 1:
        - has 1 step change during profile's first step

    Filler 2:
        - has a step that coincides with profile's unknown step
    """

    profile = [(getTime("01:00:00"), None),
               (getTime("02:00:00"), 6),
               (getTime("04:00:00"), 5.8),
               (getTime("05:00:00"), 5.8)]

    fillers = [[(getTime("00:30:00"), 100),
                (getTime("01:30:00"), 150),
                (getTime("02:30:00"), 200)],
               [(getTime("00:00:00"), 100),
                (getTime("01:00:00"), 150),
                (getTime("02:00:00"), 200)]]

    expectations = [[(getTime("01:00:00"), 100),
                     (getTime("01:30:00"), 150),
                     (getTime("02:00:00"), 6),
                     (getTime("04:00:00"), 5.8),
                     (getTime("05:00:00"), 5.8)],
                    [(getTime("01:00:00"), 150),
                     (getTime("02:00:00"), 6),
                     (getTime("04:00:00"), 5.8),
                     (getTime("05:00:00"), 5.8)]]

    do_test_fill(profile, fillers, expectations)



def test_fill_middle():

    """
    Create a step profile with a hole in the middle and fill it using different
    fillers.

    Filler 1:
        - has 2 step changes in the middle of the hole

    Filler 2:
        - has 1 step change in the middle of the hole
        - has steps that coincide with beginning and ending of hole
    """

    profile = [(getTime("01:00:00"), 6),
               (getTime("02:00:00"), None),
               (getTime("04:00:00"), 5.8),
               (getTime("05:00:00"), 5.8)]

    fillers = [[(getTime("01:30:00"), 150),
                (getTime("02:30:00"), 100),
                (getTime("03:30:00"), 50),
                (getTime("04:30:00"), 75)],
               [(getTime("01:00:00"), 100),
                (getTime("02:00:00"), 50),
                (getTime("03:00:00"), 50),
                (getTime("04:00:00"), 100)]]

    expectations = [[(getTime("01:00:00"), 6),
                     (getTime("02:00:00"), 150),
                     (getTime("02:30:00"), 100),
                     (getTime("03:30:00"), 50),
                     (getTime("04:00:00"), 5.8),
                     (getTime("05:00:00"), 5.8)],
                    [(getTime("01:00:00"), 6),
                     (getTime("02:00:00"), 50),
                     (getTime("03:00:00"), 50),
                     (getTime("04:00:00"), 5.8),
                     (getTime("05:00:00"), 5.8)]]

    do_test_fill(profile, fillers, expectations)



def test_fill_end():

    """
    Create a step profile with a hole at the end and fill it using a filler.

    Filler 1:
        - has 1 step that overlaps profile's ending

    Filler 2:
        - has a step that coincides with profile's ending
    """

    profile = [(getTime("01:00:00"), 6),
               (getTime("02:00:00"), 5.8),
               (getTime("04:00:00"), 5.6),
               (getTime("05:00:00"), None)]

    fillers = [[(getTime("04:30:00"), 100),
                (getTime("05:30:00"), 100)],
               [(getTime("04:00:00"), 100),
                (getTime("05:00:00"), 150),
                (getTime("06:00:00"), 50)]]

    expectations = [[(getTime("01:00:00"), 6),
                     (getTime("02:00:00"), 5.8),
                     (getTime("04:00:00"), 5.6),
                     (getTime("05:00:00"), 100)],
                    [(getTime("01:00:00"), 6),
                     (getTime("02:00:00"), 5.8),
                     (getTime("04:00:00"), 5.6),
                     (getTime("05:00:00"), 150)]]

    do_test_fill(profile, fillers, expectations)



def test_smooth():

    """
    Create a step profile with redundant steps, then smooth it.
    """

    datetimes = [getTime("01:00:00"),
                 getTime("02:00:00"),
                 getTime("03:00:00"),
                 getTime("04:00:00"),
                 getTime("05:00:00"),
                 getTime("06:00:00"),
                 getTime("07:00:00"),
                 getTime("08:00:00"),
                 getTime("09:00:00"),
                 getTime("10:00:00"),
                 getTime("11:00:00"),
                 getTime("12:00:00")]

    values = [6.2, 6.2, 6, 6, 6, 5.4, 5.2, 5.2, 5.8, 6, 6.2, 6.2]

    smoothedDatetimes = [getTime("01:00:00"),
                         getTime("03:00:00"),
                         getTime("06:00:00"),
                         getTime("07:00:00"),
                         getTime("09:00:00"),
                         getTime("10:00:00"),
                         getTime("11:00:00"),
                         getTime("12:00:00")]

    smoothedValues = [6.2, 6, 5.4, 5.2, 5.8, 6, 6.2, 6.2]

    # Create profile
    p = StepProfile()
    p.T = datetimes
    p.y = values

    # Smooth it
    p.smooth()

    # No redundant steps allowed in smoothed profile
    assert p.T == smoothedDatetimes and p.y == smoothedValues



def test_normalize():

    """
    Create a profile, then normalize its time axis.
    """

    datetimes = [getTime("23:30:00", "1970.01.01"),
                 getTime("00:00:00", "1970.01.02"),
                 getTime("00:30:00", "1970.01.02"),
                 getTime("00:00:00", "1970.01.03"),
                 getTime("00:30:00", "1970.01.03"),
                 getTime("00:00:00", "1970.01.04")]

    values = [6.2, 6, 5.8, 5.6, 5.4, 5.2]

    # Create profile and define its norm
    p = Profile()
    p.T = datetimes
    p.y = values
    p.norm = p.T[-1]

    # Normalize it
    p.normalize()

    # Check normalization
    assert p.t == [lib.normalizeTime(T, p.norm) for T in p.T]