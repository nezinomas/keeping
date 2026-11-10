import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.drink_quantity import DrinkQuantity
from ...lib.drink_types import DrinkType
from ...lib.drinks_options import DrinkConverter

MAX_BOTTLES = 20

DRINK_TYPES = st.sampled_from(DrinkType.values)
SERVED_TYPES = st.sampled_from([t for t in DrinkType.values if t != DrinkType.STDAV])
QUANTITIES = st.floats(min_value=0.01, max_value=5000, allow_nan=False)
# the rule turns over between 20 and 21: generation must land on both
INPUTS = st.one_of(QUANTITIES, st.sampled_from([MAX_BOTTLES, MAX_BOTTLES + 1]))

# Std Av in one piece (False) and in one millilitre (True), written out rather
# than read from DRINK_SPECS, so a wrong spec cannot agree with itself
STDAV_PER = {
    ("beer", False): 2.5,
    ("beer", True): 2.5 / 500,
    ("wine", False): 8,
    ("wine", True): 8 / 750,
    ("vodka", False): 40,
    ("vodka", True): 40 / 1000,
    ("stdav", False): 1,
    ("stdav", True): 1,
}


@given(value=INPUTS, drink_type=DRINK_TYPES)
# at or below MAX_BOTTLES the number is a count of pieces; the rule turns over
# between 20 and 21, above it the number can only have been millilitres
@example(value=1, drink_type="beer")
@example(value=20, drink_type="beer")
@example(value=1, drink_type="wine")
@example(value=20, drink_type="wine")
@example(value=1, drink_type="vodka")
@example(value=20, drink_type="vodka")
@example(value=21, drink_type="beer")
@example(value=500, drink_type="beer")
@example(value=21, drink_type="wine")
@example(value=750, drink_type="wine")
@example(value=21, drink_type="vodka")
@example(value=1000, drink_type="vodka")
# Std Av is canonical: never converted, never a volume
@example(value=1, drink_type="stdav")
@example(value=20, drink_type="stdav")
@example(value=21, drink_type="stdav")
def test_from_input_reads_a_count_up_to_max_bottles_and_millilitres_above(
    value, drink_type
):
    actual = DrinkQuantity.from_input(value, drink_type)

    is_volume = drink_type != "stdav" and value > MAX_BOTTLES
    assert actual == DrinkQuantity(
        stdav=pytest.approx(value * STDAV_PER[drink_type, is_volume]),
        drink_type=drink_type,
        is_volume=is_volume,
    )


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


@given(stdav=QUANTITIES, drink_type=DRINK_TYPES, is_volume=st.booleans())
# entered as a count -> shown as a count
@example(stdav=2.5, drink_type="beer", is_volume=False)
@example(stdav=8, drink_type="wine", is_volume=False)
@example(stdav=40, drink_type="vodka", is_volume=False)
@example(stdav=20, drink_type="vodka", is_volume=False)
# entered as a volume -> shown as a volume
@example(stdav=2.5, drink_type="beer", is_volume=True)
@example(stdav=8, drink_type="wine", is_volume=True)
@example(stdav=40, drink_type="vodka", is_volume=True)
@example(stdav=5, drink_type="beer", is_volume=True)
# Std Av ignores the flag entirely
@example(stdav=10, drink_type="stdav", is_volume=False)
@example(stdav=21, drink_type="stdav", is_volume=True)
def test_from_stdav_shows_the_amount_in_the_unit_it_was_entered(
    stdav, drink_type, is_volume
):
    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=is_volume)

    assert actual.value == pytest.approx(stdav / STDAV_PER[drink_type, is_volume])


@given(stdav=QUANTITIES, drink_type=SERVED_TYPES)
def test_from_stdav_volume_converts_back_to_the_stored_stdav(stdav, drink_type):
    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=True)

    reloaded = DrinkQuantity.from_volume(actual.value, drink_type)

    assert reloaded.stdav == pytest.approx(stdav)


@given(stdav=QUANTITIES, drink_type=SERVED_TYPES)
def test_from_stdav_count_converts_back_to_the_stored_stdav(stdav, drink_type):
    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=False)

    converter = DrinkConverter(drink_type)

    assert converter.servings_to_stdav(actual.value) == pytest.approx(stdav)


def test_from_stdav_forces_std_av_to_a_count():
    actual = DrinkQuantity.from_stdav(21, "stdav", is_volume=True)

    assert actual.is_volume is False


ENTRIES = st.sampled_from([DrinkQuantity.from_input, DrinkQuantity.from_volume])


@given(value=QUANTITIES, drink_type=DRINK_TYPES, enter=ENTRIES)
@example(value=20, drink_type="beer", enter=DrinkQuantity.from_input)
@example(value=21, drink_type="beer", enter=DrinkQuantity.from_input)
@example(value=20, drink_type="wine", enter=DrinkQuantity.from_input)
@example(value=21, drink_type="wine", enter=DrinkQuantity.from_input)
@example(value=20, drink_type="vodka", enter=DrinkQuantity.from_input)
@example(value=21, drink_type="vodka", enter=DrinkQuantity.from_input)
@example(value=21, drink_type="stdav", enter=DrinkQuantity.from_input)
@example(value=1, drink_type="beer", enter=DrinkQuantity.from_volume)
@example(value=1000, drink_type="beer", enter=DrinkQuantity.from_volume)
@example(value=1, drink_type="wine", enter=DrinkQuantity.from_volume)
@example(value=1000, drink_type="wine", enter=DrinkQuantity.from_volume)
@example(value=1, drink_type="vodka", enter=DrinkQuantity.from_volume)
@example(value=1000, drink_type="vodka", enter=DrinkQuantity.from_volume)
@example(value=1, drink_type="stdav", enter=DrinkQuantity.from_volume)
@example(value=1000, drink_type="stdav", enter=DrinkQuantity.from_volume)
def test_what_was_entered_survives_the_round_trip(value, drink_type, enter):
    """What the user entered is what the form shows them again."""
    stored = enter(value, drink_type)
    reloaded = DrinkQuantity.from_stdav(
        stored.stdav, drink_type, is_volume=stored.is_volume
    )

    assert reloaded.value == pytest.approx(value, abs=5e-7)


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


def test_an_undeclared_drink_type_is_an_error():
    with pytest.raises(ValueError):
        DrinkQuantity.from_input(500, "grog")
