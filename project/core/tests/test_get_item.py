from datetime import date

import pytest

from ..templatetags import get_item

@pytest.fixture()
def _object():
    return type("myobj", (object,), dict(foo=1))


@pytest.fixture()
def _dict():
    return {'key': 'value'}


def test_attr_exists(_object):
    actual = get_item.get_obj_attr(_object, 'foo')

    assert actual == 1


def test_attr_not_exists(_object):
    actual = get_item.get_obj_attr(_object, 'foo1')

    assert actual == 'foo1'


def test_attr_object_none():
    actual = get_item.get_obj_attr(None, 'X')

    assert actual == 'X'


@pytest.fixture()
def _date():
    return [
        {'date': date(1999, 2, 1), 'sum': 12},
        {'date': date(1999, 6, 1), 'sum': 66},
    ]


def test_get_sum_by_month_normal(_date):
    actual = get_item.get_sum_by_month(_date, 2)

    assert actual == 12


def test_get_sum_by_month_not_exists(_date):
    actual = get_item.get_sum_by_month(_date, 12)

    assert not actual


def test_get_sum_by_month_list_empty():
    actual = get_item.get_sum_by_month([], 12)

    assert not actual


@pytest.fixture()
def _title():
    return [
        {'title': 'A', 'sum': 12},
        {'title': 'B', 'sum': 66},
    ]


def test_get_sum_by_title_normal(_title):
    actual = get_item.get_sum_by_title(_title, 'A')

    assert actual == 12


def test_get_sum_by_title_not_exists(_title):
    actual = get_item.get_sum_by_title(_title, 'x')

    assert not actual


def test_get_sum_by_title_list_empty():
    actual = get_item.get_sum_by_title([], 12)

    assert not actual


@pytest.mark.parametrize('lst, expect', [([1], 1), ([], None)])
def test_get_list_val(lst, expect):
    actual = get_item.get_list_val(arr=lst, key=0)

    assert actual == expect
