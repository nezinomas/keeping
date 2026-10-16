import pytest

from ...templatetags.colorize import bg_color


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(1, "food", id="known_type"),
        pytest.param("x", "", id="unknown_value"),
    ],
)
def test_bg_color(value, expected):
    actual = bg_color(value)

    assert actual == expected
