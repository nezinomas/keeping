from datetime import date

import pytest

from ..templatetags.get_item import get_dict_val, get_obj_attr, get_sum


@pytest.fixture()
def _object():
    return type("myobj", (object,), dict(foo=1))


@pytest.fixture()
def _dict():
    return {'key': 'value'}


@pytest.fixture()
def _date():
    return [{'date': date(1999, 1, 1), 'sum': 12}]


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


def test_get_sum_normal(_date):
    actual = get_sum(_date, 0)

    assert 12 == actual


def test_get_sum_month_not_exists(_date):
    actual = get_sum(_date, 12)

    assert not actual


def test_get_sum_month_list_empty():
    actual = get_sum([], 12)

    assert not actual
