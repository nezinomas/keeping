import pytest

from ...services.drink_type_selector import DrinkTypeSelector


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_selected_is_the_given_drink_type(drink_type):
    assert DrinkTypeSelector.for_drink_type(drink_type).selected == drink_type


def test_label_is_translated():
    assert DrinkTypeSelector.for_drink_type("beer").label == "Alus"


def test_std_av_label_is_not_translated():
    assert DrinkTypeSelector.for_drink_type("stdav").label == "Std Av"


def test_options_hold_every_drink_type():
    actual = DrinkTypeSelector.for_drink_type("beer").options

    assert [value for _label, value in actual] == ["beer", "wine", "vodka", "stdav"]


def test_options_are_a_list_not_an_iterator():
    """Two templates iterate this on one page; an iterator would empty itself."""
    selector = DrinkTypeSelector.for_drink_type("beer")

    assert list(selector.options) == list(selector.options)


def test_needs_only_a_drink_type():
    """No request, no user — a tab can render for any drink type."""
    assert DrinkTypeSelector.for_drink_type("wine").label == "Vynas"
