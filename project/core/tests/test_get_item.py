from datetime import date

import pytest

from ..templatetags.get_item import (get_dict_val, get_obj_attr,
                                     get_sum_by_month, get_sum_by_title)


@pytest.fixture()
def _object():
    return type("myobj", (object,), dict(foo=1))


@pytest.fixture()
def _dict():
    return {'key': 'value'}


def test_attr_exists(_object):
    actual = get_obj_attr(_object, 'foo')

    assert actual == 1


def test_attr_not_exists(_object):
    actual = get_obj_attr(_object, 'foo1')

    assert actual == 'foo1'


def test_attr_object_none():
    actual = get_obj_attr(None, 'X')

    assert actual == 'X'


def test_dict_val_key_exists(_dict):
    actual = get_dict_val(_dict, 'key')

    assert 'value' == actual


def test_dict_val_key_not_exists(_dict):
    actual = get_dict_val(_dict, 'X')

    assert 'X' == actual


def test_dict_val_then_dictionary_none():
    actual = get_dict_val(None, 'X')

    assert 'X' == actual


@pytest.fixture()
def _date():
    return [
        {'date': date(1999, 2, 1), 'sum': 12},
        {'date': date(1999, 6, 1), 'sum': 66},
    ]


def test_get_sum_by_month_normal(_date):
    actual = get_sum_by_month(_date, 2)

    assert 12 == actual


def test_get_sum_by_month_not_exists(_date):
    actual = get_sum_by_month(_date, 12)

    assert not actual


def test_get_sum_by_month_list_empty():
    actual = get_sum_by_month([], 12)

    assert not actual


@pytest.fixture()
def _title():
    return [
        {'title': 'A', 'sum': 12},
        {'title': 'B', 'sum': 66},
    ]


def test_get_sum_by_title_normal(_title):
    actual = get_sum_by_title(_title, 'A')

    assert 12 == actual


def test_get_sum_by_title_not_exists(_title):
    actual = get_sum_by_title(_title, 'x')

    assert not actual


def test_get_sum_by_title_list_empty():
    actual = get_sum_by_title([], 12)

    assert not actual
