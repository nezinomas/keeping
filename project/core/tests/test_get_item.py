from datetime import date

import pytest

from ..templatetags import get_item


@pytest.fixture()
def _object():
    return type("myobj", (object,), dict(foo=1))


@pytest.fixture()
def _dict():
    return {"key": "value"}


def test_attr_exists(_object):
    actual = get_item.get_obj_attr(_object, "foo")

    assert actual == 1


def test_attr_not_exists(_object):
    actual = get_item.get_obj_attr(_object, "foo1")

    assert actual == "foo1"


def test_attr_object_none():
    actual = get_item.get_obj_attr(None, "X")

    assert actual == "X"


@pytest.fixture()
def _date():
    return [
        {"date": date(1999, 2, 1), "sum": 12},
        {"date": date(1999, 6, 1), "sum": 66},
    ]


@pytest.fixture()
def _title():
    return [
        {"title": "A", "sum": 12},
        {"title": "B", "sum": 66},
    ]


@pytest.mark.parametrize("lst, expect", [([1], 1), ([], None)])
def test_get_list_val(lst, expect):
    actual = get_item.get_list_val(arr=lst, key=0)

    assert actual == expect


@pytest.mark.parametrize(
    "dictionary, key, expect",
    [
        ({"x": "val"}, "x", "val"),
        ({"x": "val"}, "y", 0.0),
        (None, "y", None),
        ({}, "y", None),
    ],
)
def test_get_item(dictionary, key, expect):
    assert get_item.get_item(dictionary, key) == expect
