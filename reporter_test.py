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
import errors
import path
import reporter



# CONSTANTS
PATH_TESTS = path.Path("Test")



# CLASSES
class Report(reporter.Report):

    def __init__(self, json = None):

        super(Report, self).__init__("test.json", path.Path("Test"), json)



class DatedReport(reporter.DatedReport):

    def __init__(self, date, json = None):

        super(DatedReport, self).__init__("test.json", date, path.Path("Test"),
                                          json)



# FIXTURES
@pytest.fixture()
def setup_and_teardown():

    """
    Setup and teardown for tests which store reports.
    """

    PATH_TESTS.touch()

    yield

    PATH_TESTS.delete()



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
            report.directory.path == PATH_TESTS.path and
            report.json == {})



def test_create_dated_report():

    """
    Create a dated report.
    """

    now = datetime.datetime.now()
    today = datetime.date.today()

    report = DatedReport(now)
    
    reportPath = path.Path(PATH_TESTS.path + lib.formatDate(today))

    assert (report.name == "test.json" and
            report.date == today and
            report.json == {} and 
            report.directory.path == reportPath.path)



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

    report = Report()
    report.reset()

    report.add(0, ["A"], touch = True)
    report.store(overwrite = True)
    
    report.erase()
    report.load()

    assert report.exists() and report.get(["A"]) == 0



def test_get():

    """
    Get something from report.
    """

    key = "A"
    value = 0

    report = Report({ key: value })
    
    assert report.get([key]) == value



def test_add():

    """
    Add something to report.
    """

    key = "A"
    value = 0

    report = Report()

    with pytest.raises(errors.InvalidBranch):
        report.get([key])

    report.add(value, [key], touch = True)
    
    assert report.get([key]) == value



def test_add_overwrite():

    """
    Add something to report while overwriting previous content.
    """

    key = "A"
    value = 0
    newValue = 1

    report = Report()

    report.add(value, [key], touch = True)
    
    assert report.get([key]) == value

    with pytest.raises(errors.NoOverwriting):
        report.add(newValue, [key])

    report.add(newValue, [key], overwrite = True)
    
    assert report.get([key]) == newValue



def test_add_dated_entries(setup_and_teardown):

    """
    Add multiple dated entries to corresponding dated reports.
    """

    dates = [datetime.datetime(1970, 1, 1, 0, 0, 0),
             datetime.datetime(1970, 1, 2, 0, 0, 0),
             datetime.datetime(1970, 1, 3, 0, 0, 0)]

    values = [6.2, 6.0, 5.8]

    reporter.addDatedEntries(DatedReport, [], dict(zip(dates, values)))

    reports = [DatedReport(d) for d in dates]

    for report in reports:
        report.load(strict = False)

    for i in range(len(dates)):
        report = reports[i]
        date = dates[i]
        key = lib.formatTime(date)
        value = report.get([key])
        json = report.get([])

        assert (len(json.keys()) == 1 and
                key == lib.formatTime(dates[i]) and
                value == values[i])






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