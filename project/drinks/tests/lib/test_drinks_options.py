import pytest

from ...lib.drink_types import DrinkType
from ...lib.drinks_options import DRINK_SPECS, DrinkConverter, DrinkTypeSpec


def test_every_drink_type_has_a_spec():
    assert set(DRINK_SPECS) == set(DrinkType.values)


def test_a_canonical_type_reads_its_own_units_whatever_it_is_called(monkeypatch):
    monkeypatch.setitem(
        DRINK_SPECS,
        "grog",
        DrinkTypeSpec(
            stdav=1,
            ml=10,
            is_canonical=True,
            display_unit="Grog",
            total_unit="Grog",
            display_decimals=2,
        ),
    )

    actual = DrinkConverter("grog")

    assert actual.display_unit == "Grog"
    assert actual.total_unit == "Grog"
    assert actual.display_decimals == 2
    assert actual.figure_unit == ""
    assert actual.display_to_total(1000.0) == 1000.0
    assert actual.stdav_to_display(1.0) == 1.0


def test_an_undeclared_drink_type_is_an_error():
    with pytest.raises(ValueError):
        DrinkConverter("grog")


def test_converting_to_an_undeclared_drink_type_is_an_error():
    with pytest.raises(ValueError):
        DrinkConverter("beer").convert_qty(1, "grog")


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", 0.4),
        ("wine", 0.125),
        ("vodka", 0.025),
        ("stdav", 1.0),
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
    "drink_type, unit, decimals, total_unit",
    [
        ("beer", "ml", 0, "L"),
        ("wine", "ml", 0, "L"),
        ("vodka", "ml", 0, "L"),
        ("stdav", "Std Av", 1, "Std Av"),
    ],
)
def test_display_units(drink_type, unit, decimals, total_unit):
    actual = DrinkConverter(drink_type)

    assert actual.display_unit == unit
    assert actual.display_decimals == decimals
    assert actual.total_unit == total_unit


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        # a volume is shown as the volume it is
        ("beer", 2.5, 500.0),
        ("wine", 8.0, 750.0),
        ("vodka", 40.0, 1000.0),
        # Std Av is canonical: shown as typed, never as the ml of alcohol in it
        ("stdav", 1.0, 1.0),
    ],
)
def test_stdav_to_display(drink_type, stdav, expect):
    actual = DrinkConverter(drink_type).stdav_to_display(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        # a year's worth of a volume reads in litres
        ("beer", 2.5, 0.5),
        ("wine", 8.0, 0.75),
        ("vodka", 40.0, 1.0),
        # ... but Std Av is a count, so a thousand of them is not a litre
        ("stdav", 1.0, 1.0),
    ],
)
def test_stdav_to_total(drink_type, stdav, expect):
    actual = DrinkConverter(drink_type).stdav_to_total(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, value, expect",
    [
        ("beer", 1000.0, 1.0),
        ("stdav", 1000.0, 1000.0),
    ],
)
def test_display_to_total(drink_type, value, expect):
    actual = DrinkConverter(drink_type).display_to_total(value)

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", 2.5),
        ("wine", 8.0),
        ("vodka", 40.0),
        ("stdav", 1.0),
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
