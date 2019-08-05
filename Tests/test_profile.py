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
from Profiles import profile, step, dot, past, future, daily



# TEST MODULES
import test_reporter



# CONSTANTS
DEFAULT_DATE = datetime.datetime(1970, 1, 1)



# FUNCTIONS
def getTime(timeString = "00:00:00", dateString = "1970.01.01"):

    """
    Return a datetime object based on two formatted date and time strings.
    """

    return lib.formatTime(dateString + " - " + timeString)



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
        assert [p.T, p.y] == lib.unzip(expectations[i])



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



class StepProfile(step.StepProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(StepProfile, self).__init__()

        self.src = path.TESTS



class DailyProfile(daily.DailyProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(DailyProfile, self).__init__()

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

    profile = [(getTime("23:30:00", "1970.01.01"), 6.2),
               (getTime("00:00:00", "1970.01.02"), 6),
               (getTime("00:30:00", "1970.01.02"), 5.8),
               (getTime("01:00:00", "1970.01.02"), 5.6)]

    # Create dated entries
    reporter.setDatedEntries(test_reporter.DatedReport, [], dict(profile),
        path.TESTS)

    # Create profile with no loading method implemented
    p = Profile()

    # Try loading
    with pytest.raises(NotImplementedError):
        p.load()

    # Create a past profile (for its existing load method) and define its time
    # references (exclude first and last datetimes)
    p = PastProfile()
    p.define(profile[1][0], profile[-1][0])

    # Load its data using previously generated test dated reports
    p.load()

    # One day before start of profile should have been added to its days
    assert p.data == dict([(lib.formatTime(d), y) for (d, y) in profile])



def test_decouple():

    """
    Create a profile, give it data and decouple it into time and value axes.
    """

    # Create an unsorted profile
    profile = [(getTime("00:30:00", "1970.01.02"), 5.8),
               (getTime("23:30:00", "1970.01.01"), 6.2),
               (getTime("00:00:00", "1970.01.02"), 6),
               (getTime("01:00:00", "1970.01.02"), 5.6)]

    # Create profile
    p = Profile()
    p.data = dict([(lib.formatTime(d), y) for (d, y) in profile])

    # Decouple its data
    p.decouple()

    # Check profile axes (they should be time ordered)
    assert [p.T, p.y] == lib.unzip(sorted(profile))



def test_map():

    """
    Create a daily profile, give it decoupled data and map it over range of days
    covered by said profile.
    """

    profile = [(getTime("00:30:00").time(), 1.30),
               (getTime("01:30:00").time(), 1.45),
               (getTime("02:30:00").time(), 1.60),
               (getTime("03:30:00").time(), 1.70),
               (getTime("04:30:00").time(), 1.80),
               (getTime("05:30:00").time(), 1.90),
               (getTime("06:30:00").time(), 2.00)]

    nDays = 3
    days = [getTime().date() + datetime.timedelta(days = d)
        for d in range(nDays)]

    # Create profile
    p = DailyProfile()
    p.T, p.y = lib.unzip(profile)
    p.days = days

    # Map its data
    p.map()

    assert [p.T, p.y] == lib.unzip(sorted([(datetime.datetime.combine(d, T), y)
        for d in days for (T, y) in profile]))

    # Test before beginning of profile
    with pytest.raises(ValueError):
        p.f(getTime("00:00:00"))

    # Test midnight cross
    assert p.f(getTime("00:00:00") + datetime.timedelta(days = 1)) == 2.00



def test_inject():

    """
    Inject steps in profile according to given step durations. Tests 4 cases:
        - Step ends before start of next one (new step injected)
        - Step ends after start of next one (nothing to do)
        - Step is a canceling one (value is replaced by profile's zero value)
        - Step is at the end of profile (new step injected at the end) 
    """

    profile = [(getTime("00:00:00"), 6.2),
               (getTime("01:00:00"), 6),
               (getTime("01:30:00"), 5.8),
               (getTime("02:00:00"), 5.6),
               (getTime("03:00:00"), 5.4)]

    # Define zero (default y-axis value) for profile
    zero = 1000

    # Define durations for each given step
    durations = [datetime.timedelta(minutes = d) for d in [5, 60, 20, 0, 30]]

    # Define expected axes after injection
    expectations = [(getTime("00:00:00"), 6.2),
                    (getTime("00:05:00"), zero),
                    (getTime("01:00:00"), 6),
                    (getTime("01:30:00"), 5.8),
                    (getTime("01:50:00"), zero),
                    (getTime("02:00:00"), zero),
                    (getTime("03:00:00"), 5.4),
                    (getTime("03:30:00"), zero)]

    # Create step profile
    p = StepProfile()

    # Define it
    p.T, p.y = lib.unzip(profile)
    p.durations = durations
    p.zero = zero

    # Inject it with zeros
    p.inject()

    assert [p.T, p.y] == lib.unzip(expectations)



def test_cut():

    """
    Create a profile and cut off some of its data (outside some given time
    range).
    """

    profile = [(getTime("23:30:00", "1970.01.01"), 6.2),
               (getTime("00:00:00", "1970.01.02"), 6),
               (getTime("00:30:00", "1970.01.02"), 5.8),
               (getTime("00:00:00", "1970.01.03"), 5.6),
               (getTime("00:30:00", "1970.01.03"), 5.4),
               (getTime("00:00:00", "1970.01.04"), 5.2)]

    # Create profile
    p = Profile()
    p.T, p.y = lib.unzip(profile)
    p.start = profile[1][0]
    p.end = profile[-1][0]

    # Cut it
    last = p.cut()

    # First entry should be cut off
    assert last == profile[0][1]
    assert [p.T, p.y] == lib.unzip(profile[1:])

    # Rewrite profile
    p.T, p.y = lib.unzip(profile)

    # Cut with given datetimes
    last = p.cut(profile[2][0], profile[-2][0])

    # First two entries and last one should be cut off
    assert last == profile[1][1]
    assert [p.T, p.y] == lib.unzip(profile[2:-1])



def test_pad():

    """
    Force start/end limits on profile, using (if available) the value of the
    step preceding beginning of profile.
    """

    profile = [(getTime(dateString = "1970.01.02"), 6.2),
               (getTime(dateString = "1970.01.03"), 6)]

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
    p.T, p.y = lib.unzip(profile)

    # Pad it
    p.pad(start, end, last)

    assert p.T[0] == start and p.T[-1] == end
    assert p.y[0] == last and p.y[-1] == profile[-1][1]

    # Create profile with a specific zero value
    p = StepProfile()
    p.T, p.y = lib.unzip(profile)
    p.zero = zero

    # Pad it without last value
    p.pad(start, end)

    assert p.T[0] == start and p.T[-1] == end
    assert p.y[0] == zero and p.y[-1] == profile[-1][1]



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
               (getTime("03:00:00"), None),
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
                     (getTime("03:00:00"), 100),
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

    profile = [(getTime("01:00:00"), 6.2),
               (getTime("02:00:00"), 6.2),
               (getTime("03:00:00"), 6),
               (getTime("04:00:00"), 6),
               (getTime("05:00:00"), 6),
               (getTime("06:00:00"), 5.4),
               (getTime("07:00:00"), 5.2),
               (getTime("08:00:00"), 5.2),
               (getTime("09:00:00"), 5.8),
               (getTime("10:00:00"), 6),
               (getTime("11:00:00"), 6.2),
               (getTime("12:00:00"), 6.2)]

    smoothedProfile = [(getTime("01:00:00"), 6.2),
                       (getTime("03:00:00"), 6),
                       (getTime("06:00:00"), 5.4),
                       (getTime("07:00:00"), 5.2),
                       (getTime("09:00:00"), 5.8),
                       (getTime("10:00:00"), 6),
                       (getTime("11:00:00"), 6.2),
                       (getTime("12:00:00"), 6.2)]

    # Create profile
    p = StepProfile()
    p.T, p.y = lib.unzip(profile)

    # Smooth it
    p.smooth()

    # No redundant steps allowed in smoothed profile
    assert [p.T, p.y] == lib.unzip(smoothedProfile)



def test_normalize():

    """
    Create a profile, then normalize its time axis.
    """

    profile = [(getTime("23:30:00", "1970.01.01"), 6.2),
               (getTime("00:00:00", "1970.01.02"), 6),
               (getTime("00:30:00", "1970.01.02"), 5.8),
               (getTime("00:00:00", "1970.01.03"), 5.6),
               (getTime("00:30:00", "1970.01.03"), 5.4),
               (getTime("00:00:00", "1970.01.04"), 5.2)]

    # Create profile and define its norm
    p = Profile()
    p.T, p.y = lib.unzip(profile)
    p.norm = p.T[-1]

    # Normalize it
    p.normalize()

    # Check normalization
    assert p.t == [lib.normalizeTime(T, p.norm) for T in p.T]