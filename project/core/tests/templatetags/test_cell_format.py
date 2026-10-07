import pytest

from ...templatetags.cell_format import cell_state, cellformat, sign


@pytest.mark.parametrize(
    "value, expect",
    [
        (-12, "loss"),
        (-12.2, "loss"),
        ("-12.2", "loss"),
        (0, "gain"),
        (12, "gain"),
        (12.2, "gain"),
        ("12.2", "gain"),
        ("abc", ""),
        (None, ""),
    ],
)
def test_sign(value, expect):
    actual = sign(value)

    assert actual == expect


@pytest.mark.parametrize(
    "value, default, expect",
    [
        (0, "-", "-"),
        (0.0, "-", "-"),
        ("0", "-", "-"),
        ("0.0", "-", "-"),
        ("0,0", "-", "-"),
        ("0.00", "-", "-"),
        ("0,00", "-", "-"),
        (-0.0001, "-", "-"),
        ("-0.0001", "-", "-"),
        (1, "-", "1,00"),
        (1.0, "-", "1,00"),
        ("1.00", "-", "1,00"),
        ("1,00", "-", "1,00"),
        (1.0111, "-", "1,01"),
        (1.049, "-", "1,05"),
        (-0.5, "-", "-0,50"),
        ("-0.5", "-", "-0,50"),
        ("-0,5", "-", "-0,50"),
        (None, "-", "-"),
        (None, "ok", "ok"),
        ("None", "ok", "ok"),
        ("xx", "-", "-"),
        (1000, "-", "1.000,00"),
        ("1000", "-", "1.000,00"),
    ],
)
def test_cellformat(value, default, expect):
    actual = cellformat(value, default)

    assert actual == expect


@pytest.mark.parametrize(
    "value, expect",
    [
        (None, "empty"),
        (0, "empty"),
        (0.0, "empty"),
        ("", "empty"),
        ([], "empty"),
        (1, ""),
        (-1, ""),
        (0.5, ""),
        ("abc", ""),
    ],
)
def test_cell_state(value, expect):
    assert cell_state(value) == expect
