#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    test_path

    Author:   David Leclerc

    Version:  0.1

    Date:     03.07.2019

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import os
import datetime
import pytest



# USER LIBRARIES
import path



# FUNCTIONS
def getDirAndFilePath(dirname, filename = ""):
    dirpath = path.SRC + dirname
    filepath = dirpath + os.sep + filename
    return dirpath, filepath



# TESTS
def test_empty():

    """
    Empty path should point to source.
    """

    _path = path.Path()

    assert _path.path == path.SRC



def test_expand():

    """
    Expanding path either with front- or backslash should work.
    """

    _path = path.Path()
    _path.expand("1/2")

    assert _path.path == path.SRC + "1" + os.sep + "2" + os.sep



def test_backslash():

    """
    Test path with backslashes.
    """

    with pytest.raises(TypeError):
        _path = path.Path("1\\2")



def test_list():

    """
    Test path as list.
    """

    with pytest.raises(TypeError):
        _path = path.Path(["1", "2"])



def test_touch_directory():

    """
    Test touching a directory.
    """

    dirname = "test"
    dirpath = getDirAndFilePath(dirname)[0]

    _path = path.Path(dirname)
    _path.touch()

    existed = os.path.isdir(dirpath)

    _path.delete()

    assert existed



def test_touch_file():

    """
    Test touching a file.
    """

    dirname = "test"
    filename = "test.json"
    filepath = getDirAndFilePath(dirname, filename)[1]

    _path = path.Path(dirname)
    _path.touch(filename)

    existed = os.path.isfile(filepath)

    _path.delete()

    assert existed



def test_scan():

    """
    Scanning directory for a file which exists should NOT return an empty list.
    """

    dirname = "test"
    filename = "test.json"

    _path = path.Path(dirname)
    _path.touch(filename)

    found = len(_path.scan(filename)) > 0

    _path.delete()

    assert found



def test_scan_recursively():

    """
    Scanning directory recursively for a file which exists should NOT return an
    empty list.
    """

    rootname = "test"
    dirname = rootname + os.sep + "1/2/3"
    filename = "test.json"

    _path = path.Path(dirname)
    _path.touch(filename)

    _path = path.Path(rootname)
    found = len(_path.scan(filename)) > 0

    _path.delete()

    assert found



def test_scan_non_existent_path():

    """
    Scanning non-existent directory for a file should return an empty list.
    """

    dirname = "test"
    filename = "test.json"
    dirpath = getDirAndFilePath(dirname, filename)[0]

    _path = path.Path(dirname)

    existed = os.path.isdir(dirpath)
    found = len(_path.scan(filename)) > 0

    assert not existed and not found



def test_scan_non_existent_file():

    """
    Scanning directory for a non-existent file should return an empty list.
    """

    dirname = "test"
    filename = "test.json"
    filepath = getDirAndFilePath(dirname, filename)[1]

    _path = path.Path(dirname)
    _path.touch()

    existed = os.path.isfile(filepath)
    found = len(_path.scan(filename)) > 0

    _path.delete()

    assert not existed and not found



def test_delete():

    """
    Creating, then deleting a directory a file should leave no trace.
    """

    dirname = "test"
    filename = "test.json"
    dirpath, filepath = getDirAndFilePath(dirname, filename)

    _path = path.Path(dirname)
    _path.touch(filename)

    existed = os.path.isdir(dirpath) and os.path.isfile(filepath)

    _path.delete()

    deleted = not os.path.isdir(dirpath)

    assert existed and deleted



def test_delete_recursively():

    """
    Creating, then recursively deleting directories and their files should leave
    no trace.
    """

    rootname = "test"
    dirname = rootname + os.sep + "1/2/3"
    filename = "test.json"
    dirpath, filepath = getDirAndFilePath(dirname, filename)

    _path = path.Path(dirname)
    _path.touch(filename)

    existed = os.path.isdir(dirpath) and os.path.isfile(filepath)

    _path = path.Path(rootname)
    _path.delete()

    deleted = not os.path.isdir(dirpath)

    assert existed and deleted