import pytest

from ...services.drink_type_selector import (
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
)


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_selected_is_the_given_drink_type(drink_type):
    assert DrinkTypeSelector(drink_type).selected == drink_type


def test_label_is_translated():
    assert DrinkTypeSelector("beer").label == "Alus"


def test_std_av_label_is_not_translated():
    assert DrinkTypeSelector("stdav").label == "Std Av"


def test_options_hold_every_drink_type():
    actual = DrinkTypeSelector("beer").options

    assert [value for _label, value in actual] == ["beer", "wine", "vodka", "stdav"]


def test_options_are_a_list_not_an_iterator():
    """Two templates iterate this on one page; an iterator would empty itself."""
    selector = DrinkTypeSelector("beer")

    assert list(selector.options) == list(selector.options)


def test_needs_only_a_drink_type():
    """No request, no user — a tab can render for any drink type."""
    assert DrinkTypeSelector("wine").label == "Vynas"


# -------------------------------------------------------------------------------------
#                                                                            fixed
# -------------------------------------------------------------------------------------


def test_a_fixed_switcher_names_std_av():
    fixed = FixedDrinkTypeSelector()

    assert fixed.selected == "stdav"
    assert fixed.label == "Std Av"


def test_a_fixed_switcher_offers_nothing():
    assert FixedDrinkTypeSelector().options == ()


def test_a_fixed_switcher_cannot_be_given_a_drink_type():
    """A harm metric is defined in Std Av, so a choice could only misname it."""
    with pytest.raises(TypeError):
        FixedDrinkTypeSelector("wine")


# -------------------------------------------------------------------------------------
#                                                                          absent
# -------------------------------------------------------------------------------------


def test_an_absent_switcher_reads_no_amount():
    absent = NoDrinkTypeSelector()

    assert absent.selected == ""
    assert absent.label == ""
    assert absent.options == ()


# -------------------------------------------------------------------------------------
#                                                                     one contract
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "control",
    [
        DrinkTypeSelector("beer"),
        FixedDrinkTypeSelector(),
        NoDrinkTypeSelector(),
    ],
)
def test_every_control_answers_what_the_template_reads(control):
    """The template asks one set of questions and never asks which class it got."""
    for name in ("selected", "label", "options", "state"):
        assert hasattr(control, name), name


@pytest.mark.parametrize(
    "control_class", [DrinkTypeSelector, FixedDrinkTypeSelector, NoDrinkTypeSelector]
)
def test_every_control_is_built_from_a_drink_type(control_class):
    assert isinstance(control_class.for_type("beer"), control_class)
