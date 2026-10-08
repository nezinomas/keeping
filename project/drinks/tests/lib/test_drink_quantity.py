from itertools import product

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.drink_quantity import DrinkQuantity
from ...lib.drink_types import DrinkType
from .drink_specs import STDAV_PER_SERVING

ML_PER_SERVING = {"beer": 500, "wine": 750, "vodka": 1000}
MAX_BOTTLES = 20

DRINK_TYPES = st.sampled_from(DrinkType.values)
QUANTITIES = st.floats(min_value=0.01, max_value=5000, allow_nan=False)
FLAGS = st.booleans()
# the rule turns over between 20 and 21: generation must land on both
INPUTS = st.one_of(QUANTITIES, st.sampled_from([MAX_BOTTLES, MAX_BOTTLES + 1]))


def type_by_number_examples(**axes):
    """An `@example` for every drink type against every number."""

    def decorate(test):
        for combo in product(*axes.values()):
            test = example(**dict(zip(axes, combo)))(test)
        return test

    return decorate


# from_input (typed number)


@given(value=INPUTS, drink_type=DRINK_TYPES)
# at or below MAX_BOTTLES the number is a count of pieces; the rule turns
# over between 20 and 21
@example(value=1, drink_type="beer")
@example(value=20, drink_type="beer")
@example(value=1, drink_type="wine")
@example(value=20, drink_type="wine")
@example(value=1, drink_type="vodka")
@example(value=20, drink_type="vodka")
# above MAX_BOTTLES it can only have been millilitres
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
def test_from_input(value, drink_type):
    stdav_per_serving = STDAV_PER_SERVING[drink_type]
    expect_is_volume = drink_type != "stdav" and value > MAX_BOTTLES
    expect_stdav = value
    if drink_type != "stdav":
        expect_stdav = value * stdav_per_serving
    if expect_is_volume:
        expect_stdav = value * stdav_per_serving / ML_PER_SERVING[drink_type]

    actual = DrinkQuantity.from_input(value, drink_type)

    assert actual.stdav == pytest.approx(expect_stdav)
    assert actual.is_volume is expect_is_volume
    assert actual.drink_type == drink_type


# from_volume (always a volume)


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


# from_stdav (stored record)


@given(stdav=QUANTITIES, drink_type=DRINK_TYPES, is_volume=FLAGS)
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
def test_from_stdav_value(stdav, drink_type, is_volume):
    expect_value = stdav
    if drink_type != "stdav" and is_volume:
        expect_value = (
            stdav * ML_PER_SERVING[drink_type] / STDAV_PER_SERVING[drink_type]
        )
    if drink_type != "stdav" and not is_volume:
        expect_value = stdav / STDAV_PER_SERVING[drink_type]

    actual = DrinkQuantity.from_stdav(stdav, drink_type, is_volume=is_volume)

    assert actual.value == expect_value


def test_from_stdav_forces_std_av_to_a_count():
    actual = DrinkQuantity.from_stdav(21, "stdav", is_volume=True)

    assert actual.is_volume is False


# round trip


@given(typed=QUANTITIES, drink_type=DRINK_TYPES)
@type_by_number_examples(
    drink_type=["beer", "wine", "vodka", "stdav"], typed=[1, 5, 20, 21, 500, 1000]
)
def test_typed_number_survives_the_round_trip(drink_type, typed):
    """What the user typed is what the form shows them again."""
    stored = DrinkQuantity.from_input(typed, drink_type)
    reloaded = DrinkQuantity.from_stdav(
        stored.stdav, drink_type, is_volume=stored.is_volume
    )

    assert reloaded.value == pytest.approx(typed, abs=5e-7)


@given(ml=QUANTITIES, drink_type=DRINK_TYPES)
@type_by_number_examples(
    drink_type=["beer", "wine", "vodka", "stdav"], ml=[1, 500, 750, 1000]
)
def test_volume_survives_the_round_trip(drink_type, ml):
    stored = DrinkQuantity.from_volume(ml, drink_type)
    reloaded = DrinkQuantity.from_stdav(
        stored.stdav, drink_type, is_volume=stored.is_volume
    )

    assert reloaded.value == pytest.approx(ml, abs=5e-7)


# display


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
