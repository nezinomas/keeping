import pytest

from ...services.drink_type_selector import (
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
    control_for_tab,
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


# -------------------------------------------------------------------------------------
#                                                                    for the tab
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("tab", ["index", "trends", "history"])
def test_a_tab_reading_the_selected_type_offers_the_choice(tab):
    control = control_for_tab(tab, "wine")

    assert isinstance(control, DrinkTypeSelector)
    assert control.state == "choice"
    assert control.selected == "wine"


@pytest.mark.parametrize("tab", ["habits", "risk"])
def test_a_tab_reading_a_harm_metric_names_std_av(tab):
    control = control_for_tab(tab, "wine")

    assert isinstance(control, FixedDrinkTypeSelector)
    assert control.state == "fixed"


def test_a_tab_reading_no_single_amount_draws_no_switcher():
    """The Data tab lists what was typed, each row in its own drink type."""
    control = control_for_tab("data", "wine")

    assert isinstance(control, NoDrinkTypeSelector)
    assert control.state == "absent"


def test_an_unknown_tab_falls_back_to_the_default_one():
    assert control_for_tab("nonsense", "wine").selected == "wine"
