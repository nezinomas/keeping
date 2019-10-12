import pytest

from ..templatetags.get_item import get_obj_attr, get_dict_val


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


def test_dict_val_key_exists(_dict):
    actual = get_dict_val(_dict, 'key')

    assert 'value' == actual


def test_dict_val_key_not_exists(_dict):
    actual = get_dict_val(_dict, 'X')

    assert 'X' == actual


def test_dict_val_then_dictionary_none():
    actual = get_dict_val(None, 'X')

    assert 'X' == actual
