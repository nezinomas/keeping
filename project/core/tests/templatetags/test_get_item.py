import pytest

from ...templatetags import get_item


@pytest.mark.parametrize("lst, expect", [([1], 1), ([], 0)])
def test_get_list_val(lst, expect):
    actual = get_item.get_list_val(arr=lst, key=0)

    assert actual == expect


@pytest.mark.parametrize(
    "dictionary, key, expect",
    [
        ({"x": "val"}, "x", "val"),
        ({"x": "val"}, "y", 0.0),
        (None, "y", 0),
        ({}, "y", 0),
    ],
)
def test_get_item(dictionary, key, expect):
    assert get_item.get_item(dictionary, key) == expect
