#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    test_reporter

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
import errors
import path
import reporter



# CLASSES
class Report(reporter.Report):

    name = "test.json"

    def __init__(self, directory = path.TESTS, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(Report, self).__init__(self.name, directory, json)



class DatedReport(reporter.DatedReport):

    name = "test.json"

    def __init__(self, date, directory = path.TESTS, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        super(DatedReport, self).__init__(self.name, date, directory, json)



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
def test_load_non_existent_report():

    """
    Load a non existent report.
    """
    
    report = Report()
    
    with pytest.raises(IOError):
        report.load()



def test_create_report():

    """
    Create a report.
    """

    report = Report()

    assert (report.name == "test.json" and
            report.directory.path == path.TESTS.path and
            report.json == {})



def test_create_dated_report():

    """
    Create a dated report.
    """

    today = datetime.date.today()

    report = DatedReport(today)
    
    reportPath = path.Path(path.TESTS.path + lib.formatDate(today))

    assert (report.name == "test.json" and
            report.date == today and
            report.json == {} and 
            report.directory.path == reportPath.path)



def test_reset_report():

    """
    Reset a report.
    """

    key = "A"
    value = 0
    branch = [key]

    report = Report()
    report.set(value, branch)

    assert report.get(branch) == value

    report.reset()

    assert report.get() == {}



def test_store_report(setup_and_teardown):

    """
    Store a report.
    """
    
    report = Report()
    report.store()

    assert report.exists()



def test_store_dated_report(setup_and_teardown):

    """
    Store a dated report.
    """

    today = datetime.date.today()

    report = DatedReport(today)
    report.store()

    assert report.exists()



def test_store_overwrite_report(setup_and_teardown):

    """
    Overwrite previous JSON file while storing a report.
    """

    key = "A"
    value = 0
    branch = [key]

    report = Report()
    report.reset()

    report.set(value, branch)

    # Try overwriting report although not allowed to
    with pytest.raises(errors.NoOverwriting):
        report.store(False)

    report.store()
    
    report.erase()
    report.load()

    assert report.exists() and report.get(branch) == value



def test_get():

    """
    Get something from report.
    """

    key = "A"
    value = 0

    branch = [key]

    report = Report(json = { key: value })
    
    # Test getting tip of branch
    assert report.get(branch) == value

    # Test getting whole report
    assert report.get() == { key: value }



def test_set():

    """
    Set something to report.
    """

    key = "A"
    value = 0

    branch = [key]

    report = Report()

    # Missing branch should raise an error
    with pytest.raises(errors.MissingBranch):
        report.get(branch)

    # Set value at tip of branch
    report.set(value, branch)

    # Resetting same value should not cause problems
    report.set(value, branch)
    
    assert report.get(branch) == value



def test_set_overwrite():

    """
    Add something to report while overwriting previous content.
    """

    key = "A"
    value = 0
    newValue = 1

    branch = [key]

    report = Report(json = { key: value })
    
    assert report.get(branch) == value

    # Overwriting forbidden should raise an error
    with pytest.raises(errors.NoOverwriting):
        report.set(newValue, branch)

    # Allow overwriting
    report.set(newValue, branch, overwrite = True)
    
    assert report.get(branch) == newValue



def test_delete():

    """
    Delete something from report at the tip of a given branch.
    """

    keys = ["A", "B"]
    values = [0, 1]

    report = Report(json = dict(zip(keys, values)))

    # Missing branch should raise an error
    with pytest.raises(errors.MissingBranch):
        report.delete(["C"])

    # Delete value at tip of branch
    report.delete(["B"])

    assert report.get([]) == { "A": 0 }

    # Delete the whole report
    report.delete()

    assert report.get([]) == {}



def test_increment():

    """
    Increment a report's field.
    """

    key = "A"
    value = 0
    keyString = "B"
    valueString = "0"
    missingKey = "C"
    missingValue = 0

    branch = [key]
    missingBranch = [missingKey]

    report = Report(json = {
        key: value,
        keyString: valueString
    })
    
    assert report.get(branch) == value

    # Impossible to increment whole report: key needed
    with pytest.raises(errors.InvalidBranch):
        report.increment([])

    # Can only increment branches leading to numbers
    with pytest.raises(TypeError):
        report.increment([keyString])

    report.increment(branch)
    
    assert report.get(branch) == value + 1

    # Increment non-exisiting entry, while not allowed to
    with pytest.raises(errors.MissingBranch):
        report.increment(missingBranch)

    # To it again, but allow it
    report.increment(missingBranch, strict = False)
    
    assert report.get(missingBranch) == missingValue + 1



def test_get_report_dates(setup_and_teardown):

    """
    Get dates for stored dated reports.
    """

    datetimes = [datetime.datetime(1975, 1, 1, 0, 0, 0),
                 datetime.datetime(1980, 2, 2, 0, 0, 0),
                 datetime.datetime(1985, 3, 3, 0, 0, 0)]

    # Instanciate empty reports and store them
    for d in datetimes:
        report = DatedReport(d.date())
        report.store()

    reportDates = reporter.getReportDates(DatedReport, path.TESTS)

    assert (len(datetimes) == len(reportDates) and
            all([d.date() in reportDates for d in datetimes]))



def test_get_recent(setup_and_teardown):

    """
    Get entries in recent reports.
    """

    now = datetime.datetime.now()

    datetimes = [datetime.datetime(1975, 1, 1, 0, 0, 0),
                 datetime.datetime(1980, 2, 2, 0, 0, 0),
                 datetime.datetime(1985, 3, 3, 0, 0, 0)]

    values = [6.2, 6.0, 5.8]

    entries = dict(zip(datetimes, values))

    branch = ["A", "B"]

    # Create reports
    reporter.setDatedEntries(DatedReport, branch, entries,
        path.TESTS)

    # Look for values in last 3 days (strict search)
    emptyResults = reporter.getRecentDatedEntries(DatedReport, now, branch, 3,
        src = path.TESTS, strict = True)
    
    # Results should be empty
    assert len(emptyResults) == 0

    # Look for values in 3 most recent available reports
    results = reporter.getRecentDatedEntries(DatedReport, now, branch, 3,
        src = path.TESTS, strict = False)

    # There should be as many entries in merged results, as there were reports
    # instanciated. The values should also fit.
    assert (len(results) == len(datetimes) and
        all([results[lib.formatTime(d)] == entries[d] for d in datetimes]))



def test_get_dated_entries(setup_and_teardown):

    """
    Get multiple dated entries from corresponding dated reports.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0)]

    formattedDatetimes = [lib.formatTime(d) for d in datetimes]

    dates = [d.date() for d in datetimes]

    values = [6.2, 6.0, 5.8]

    entries = dict(zip(datetimes, values))

    formattedEntries = dict(zip(formattedDatetimes, values))

    branch = ["A", "B"]

    # Add dated entries to corresponding reports (the latter will be created
    # if needed)
    reporter.setDatedEntries(DatedReport, branch, entries,
        path.TESTS)

    # Try and find entries in given dated reports
    # Search for entries strictly: none should be missing!
    storedEntries = reporter.getDatedEntries(DatedReport, dates, branch,
        path.TESTS, True)

    assert storedEntries == formattedEntries



def test_set_dated_entries(setup_and_teardown):

    """
    Add multiple dated entries to corresponding dated reports.
    """

    datetimes = [datetime.datetime(1970, 1, 1, 0, 0, 0),
                 datetime.datetime(1970, 1, 2, 0, 0, 0),
                 datetime.datetime(1970, 1, 3, 0, 0, 0)]

    values = [6.2, 6.0, 5.8]

    entries = dict(zip(datetimes, values))

    branch = ["A", "B"]

    # Add dated entries to corresponding reports (the latter will be created
    # if needed)
    reporter.setDatedEntries(DatedReport, branch, entries,
        path.TESTS)

    # Check for each datetime if report was created and value added
    for d in datetimes:

        # Instanciate and load corresponding report
        report = reporter.getReportByType(DatedReport, d.date())

        # Format datetime object to get key
        key = lib.formatTime(d)

        # Get corresponding value, as well as whole JSON
        value = report.get(branch + [key])
        json = report.get()

        # There should only be one key in JSON, and its value should be the
        # one listed in the entries above
        assert len(json.keys()) == 1 and value == entries[d]






def test_merge():

    """
    Merge dicts.
    """

    a = {
        "A": 0
    }
    b = {
        "B": 1
    }
    c = {
        "A": 0,
        "B": 1
    }

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