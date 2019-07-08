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
import path
import reporter



# FUNCTIONS



# TESTS
def test_load_non_existent_report():

    """
    Load a non existent report.
    """

    name = "test.json"
    directory = path.Path("Test")
    
    report = reporter.Report(name, None, directory)
    
    with pytest.raises(IOError):
        report.load()



def test_create_report():

    """
    Create a report.
    """

    name = "test.json"
    directory = path.Path("Test")
    json = {
        "A": 0
    }
    
    report = reporter.Report(name, None, directory, json)
    
    assert (report.name == "test.json" and
            report.date == None and
            report.directory.path == directory.path and
            report.json == {"A": 0})



def test_create_dated_report():

    """
    Create a dated report.
    """

    now = datetime.datetime.now()
    today = datetime.date.today()

    name = "test.json"
    directory = path.Path("Test")
    json = {
        "A": 0
    }
    
    report = reporter.Report(name, now, directory, json)
    
    directory.expand(lib.formatDate(today))

    assert (report.name == "test.json" and
            report.date == today and
            report.directory.path == directory.path and
            report.json == {"A": 0})



def test_store_report():

    """
    Store a report.
    """

    name = "test.json"
    directory = path.Path("Test")
    
    report = reporter.Report(name, None, directory)
    report.store()

    assert report.exists()



def test_store_dated_report():

    """
    Store a dated report.
    """

    today = datetime.date.today()

    name = "test.json"
    directory = path.Path("Test")
    
    report = reporter.Report(name, today, directory)
    report.store()

    assert report.exists()



def test_store_report_overwrite():

    """
    Overwrite a report.
    """

    name = "test.json"
    directory = path.Path("Test")
    
    report = reporter.Report(name, None, directory)
    report.store()

    assert report.exists()

    report.add(0, ["A"], touch = True)
    report.store()

    assert report.exists() and report.get(["A"]) == 0






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