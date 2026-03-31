from ...templatetags.drinks_templatetags import convert_to_quantity


def test_convert_to_quantity():
    actual = convert_to_quantity(2.5, "beer")
    assert actual == 1
