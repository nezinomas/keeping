import pytest

from ..templatetags.get_item import get_obj_attr


@pytest.fixture()
def _object():
    return type("myobj", (object,), dict(foo=1))


def test_attr_exists(_object):
    actual = get_obj_attr(_object, 'foo')

    assert actual == 1


def test_attr_not_exists(_object):
    actual = get_obj_attr(_object, 'foo1')

    assert actual == 'foo1'
