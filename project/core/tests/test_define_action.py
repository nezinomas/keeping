from ..templatetags.define_action import define


def test_value():
    actual = define('test')

    assert actual == 'test'


def test_no_value():
    actual = define()

    assert not actual
