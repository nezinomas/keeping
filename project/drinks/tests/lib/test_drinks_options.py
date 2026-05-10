import pytest

from ...lib.drinks_options import DrinkConverter


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", 0.4),
        ("wine", 0.125),
        ("vodka", 0.025),
        ("stdav", 1.0),
        ("unknown", 1.0),
    ],
)
def test_ratio(drink_type, expect):
    actual = DrinkConverter(drink_type).ratio

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, ml, expect",
    [
        ("beer", 500, 2.5),
        ("wine", 750, 8.0),
        ("vodka", 1000, 40.0),
        ("stdav", 10, 1.0),
        ("unknown", 500, 50.0),
    ],
)
def test_ml_to_stdav(drink_type, ml, expect):
    actual = DrinkConverter(drink_type).ml_to_stdav(ml)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        ("beer", 2.5, 500.0),
        ("wine", 8.0, 750.0),
        ("vodka", 40.0, 1000.0),
        ("stdav", 1.0, 10.0),
    ],
)
def test_stdav_to_ml(drink_type, stdav, expect):
    actual = DrinkConverter(drink_type).stdav_to_ml(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", 2.5),
        ("wine", 8.0),
        ("vodka", 40.0),
        ("stdav", 1.0),
        ("unknown", 1.0),
    ],
)
def test_stdav_per_unit(drink_type, expect):
    actual = DrinkConverter(drink_type).stdav_per_unit

    assert actual == expect


@pytest.mark.parametrize(
    "qty, from_, to, expect",
    [
        (1, "beer", "beer", 1),
        (1, "beer", "wine", 0.31),
        (1, "beer", "vodka", 0.06),
        (1, "beer", "stdav", 2.5),
        (1, "wine", "beer", 3.2),
        (1, "wine", "wine", 1),
        (1, "wine", "vodka", 0.2),
        (1, "wine", "stdav", 8),
        (1, "vodka", "beer", 16),
        (1, "vodka", "wine", 5),
        (1, "vodka", "vodka", 1),
        (1, "vodka", "stdav", 40),
    ],
)
def test_convert_qty(qty, from_, to, expect):
    actual = DrinkConverter(from_).convert_qty(qty, to)

    assert round(actual, 2) == expect


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        ("beer", 2.5, 0.025),
        ("wine", 8, 0.08),
        ("vodka", 40, 0.4),
        ("stdav", 1, 0.01),
    ],
)
def test_stdav_to_alcohol(drink_type, stdav, expect):
    actual = DrinkConverter(drink_type).stdav_to_alcohol(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, year, stdav, expect",
    [
        ("beer", 1999, 2.5, 365),
        ("wine", 1999, 8, 365),
        ("vodka", 1999, 40, 365),
        ("stdav", 1999, 1, 365),
    ],
)
def test_max_bottles_per_year(drink_type, year, stdav, expect):
    actual = DrinkConverter(drink_type).max_bottles_per_year(year=year, max_stdav=stdav)

    assert actual == expect
