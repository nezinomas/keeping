import pytest
from ..templatetags.colorize import bg_color


def test_value_exists():
    actual = bg_color(1)

    assert 'food' == actual


def test_value_not_exists():
    actual = bg_color('x')

    assert '' == actual
