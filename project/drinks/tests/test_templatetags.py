from ..templatetags.drinks_templatetags import convert


def test_convert():
    actual = convert(2.5, 'beer')
    assert actual == 1
