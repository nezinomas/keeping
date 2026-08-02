import pytest

from ...lib.drink_quantity import DrinkQuantity

# -------------------------------------------------------------------------------------
#                                                            from_input (typed number)
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, drink_type, expect_stdav, expect_is_volume",
    [
        # at or below MAX_BOTTLES the number is a count of pieces; the rule turns
        # over between 20 and 21
        (1, "beer", 2.5, False),
        (20, "beer", 50.0, False),
        (1, "wine", 8.0, False),
        (20, "wine", 160.0, False),
        (1, "vodka", 40.0, False),
        (20, "vodka", 800.0, False),
        # above MAX_BOTTLES it can only have been millilitres
        (21, "beer", 0.1, True),
        (500, "beer", 2.5, True),
        (21, "wine", 0.22, True),
        (750, "wine", 8.0, True),
        (21, "vodka", 0.84, True),
        (1000, "vodka", 40.0, True),
        # Std Av is canonical: never converted, never a volume
        (1, "stdav", 1, False),
        (20, "stdav", 20, False),
        (21, "stdav", 21, False),
    ],
)
def test_from_input(value, drink_type, expect_stdav, expect_is_volume):
    actual = DrinkQuantity.from_input(value, drink_type)

    assert round(actual.stdav, 2) == expect_stdav
    assert actual.is_volume is expect_is_volume
    assert actual.drink_type == drink_type


# -------------------------------------------------------------------------------------
#                                                          from_volume (always a volume)
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ml, drink_type, expect_stdav, expect_is_volume",
    [
        (500, "beer", 2.5, True),
        (750, "wine", 8.0, True),
        (1000, "vodka", 40.0, True),
        (1, "beer", 0.005, True),
        # Std Av is canonical: still not converted, even asked as a volume
        (10, "stdav", 10, False),
    ],
)
def test_from_volume(ml, drink_type, expect_stdav, expect_is_volume):
    actual = DrinkQuantity.from_volume(ml, drink_type)

    assert round(actual.stdav, 3) == expect_stdav
    assert actual.is_volume is expect_is_volume


# -------------------------------------------------------------------------------------
#                                                            from_stdav (stored record)
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stdav, drink_type, is_volume, expect_value",
    [
        # entered as a count -> shown as a count
        (2.5, "beer", False, 1.0),
        (8, "wine", False, 1.0),
        (40, "vodka", False, 1.0),
        (20, "vodka", False, 0.5),
        # entered as a volume -> shown as a volume
        (2.5, "beer", True, 500.0),
        (8, "wine", True, 750.0),
        (40, "vodka", True, 1000.0),
        (5, "beer", True, 1000.0),
        # Std Av ignores the flag entirely
        (10, "stdav", False, 10.0),
        (21, "stdav", True, 21.0),
    ],
)
def test_from_stdav_value(stdav, drink_type, is_volume, expect_value):
    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=is_volume)

    assert actual.value == expect_value


def test_from_stdav_forces_std_av_to_a_count():
    actual = DrinkQuantity.from_stdav(21, "stdav", is_volume=True)

    assert actual.is_volume is False


# -------------------------------------------------------------------------------------
#                                                                        round trip
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@pytest.mark.parametrize("typed", [1, 5, 20, 21, 500, 1000])
def test_typed_number_survives_the_round_trip(drink_type, typed):
    """What the user typed is what the form shows them again."""
    stored = DrinkQuantity.from_input(typed, drink_type)
    reloaded = DrinkQuantity.from_stdav(
        stored.stdav, drink_type, is_volume=stored.is_volume
    )

    assert round(reloaded.value, 6) == typed


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@pytest.mark.parametrize("ml", [1, 500, 750, 1000])
def test_volume_survives_the_round_trip(drink_type, ml):
    stored = DrinkQuantity.from_volume(ml, drink_type)
    reloaded = DrinkQuantity.from_stdav(
        stored.stdav, drink_type, is_volume=stored.is_volume
    )

    assert round(reloaded.value, 6) == ml


# -------------------------------------------------------------------------------------
#                                                                          display
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stdav, drink_type, is_volume, expect",
    [
        (2.5, "beer", False, "1,0 vnt"),
        (2.5, "beer", True, "500 ml"),
        (5, "beer", True, "1.000 ml"),
        (47.5, "beer", False, "19,0 vnt"),
        (10, "stdav", False, "10,0 vnt"),
    ],
)
def test_display(stdav, drink_type, is_volume, expect):
    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=is_volume)

    assert actual.display == expect


@pytest.mark.parametrize(
    "is_volume, expect_places",
    [
        (True, 0),
        (False, 1),
    ],
)
def test_decimal_places(is_volume, expect_places):
    actual = DrinkQuantity.from_stdav(2.5, "beer", is_volume=is_volume)

    assert actual.decimal_places == expect_places


def test_unknown_drink_type_falls_back_to_std_av_ratios():
    actual = DrinkQuantity.from_input(500, "unknown")

    assert actual.is_volume is True
    assert actual.stdav == 50.0
