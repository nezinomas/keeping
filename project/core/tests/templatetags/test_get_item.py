import pytest

from ...templatetags import get_item

OBJECT = type("myobj", (object,), dict(foo=1))


@pytest.mark.parametrize(
    "obj, name, expect",
    [
        pytest.param(OBJECT, "foo", 1, id="exists"),
        pytest.param(OBJECT, "foo1", "foo1", id="not_exists"),
        pytest.param(None, "X", "X", id="object_none"),
    ],
)
def test_get_obj_attr_returns_the_attribute_or_its_name(obj, name, expect):
    assert get_item.get_obj_attr(obj, name) == expect


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
