import pytest

from ...lib.stat_card import StatCard

# -------------------------------------------------------------------------------------
#                                                                            empty
# -------------------------------------------------------------------------------------


def test_empty_card():
    card = StatCard.empty("Days dry", "No data")

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == "No data"
    assert card.show_icon is False


# -------------------------------------------------------------------------------------
#                                                                       comparison
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "improving, expect_state",
    [
        (True, "improving"),
        (False, "worsening"),
    ],
)
def test_comparison_resolves_direction(improving, expect_state):
    card = StatCard.comparison(
        "Heavy days", improving=improving, value="1", note="1 / 2"
    )

    assert card.state == expect_state


def test_comparison_always_shows_an_icon():
    """A direction is the one thing worth pointing an arrow at."""
    card = StatCard.comparison("Heavy days", improving=True, value="1", note="1 / 2")

    assert card.show_icon is True


def test_comparison_carries_the_explanation():
    card = StatCard.comparison(
        "Heavy days", improving=True, value="1", note="1 / 2", explanation=("why",)
    )

    assert card.explanation == ("why",)


# -------------------------------------------------------------------------------------
#                                                                            level
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["low", "medium", "high", "neutral", "empty"])
def test_level_keeps_the_state_it_is_given(state):
    card = StatCard.level("This week", state=state, value="3.0", note="")

    assert card.state == state


def test_level_shows_no_icon_unless_it_is_asked_for_one():
    """A threshold on its own has no direction to point at."""
    card = StatCard.level("This week", state="high", value="30.0", note="")

    assert card.show_icon is False


def test_level_carries_the_explanation():
    card = StatCard.level(
        "This week", state="high", value="30.0", note="", explanation=("why",)
    )

    assert card.explanation == ("why",)


# -------------------------------------------------------------------------------------
#                                                                         defaults
# -------------------------------------------------------------------------------------


def test_defaults_render_a_plain_card():
    card = StatCard("Pure alcohol", value="2.5", unit="L", note="this year")

    assert card.state == "neutral"
    assert card.show_icon is False
    assert card.explanation == ()


def test_an_explanation_carries_each_sentence_apart():
    """The template renders one paragraph per part, so the parts stay separate
    all the way from the service rather than being glued with a separator."""
    card = StatCard("Drinking days", explanation=("a share", "a definition."))

    assert card.explanation == ("a share", "a definition.")


# -------------------------------------------------------------------------------------
#                                                                             unit
# -------------------------------------------------------------------------------------


def test_unit_is_carried_apart_from_the_figure():
    """The unit is set smaller than the figure, so it cannot be baked into it."""
    card = StatCard("Pure alcohol", value="2.5", unit="L")

    assert card.value == "2.5"
    assert card.unit == "L"


def test_a_figure_with_no_unit_carries_an_empty_one():
    card = StatCard("Days dry", value="12")

    assert card.unit == ""


@pytest.mark.parametrize(
    "factory",
    [
        lambda: StatCard.empty("Days dry", "No data"),
        lambda: StatCard.comparison("Heavy days", improving=True, value="1", note=""),
        lambda: StatCard.level("This week", state="high", value="3.0", note=""),
    ],
)
def test_every_constructor_carries_a_unit(factory):
    assert factory().unit == ""


def test_comparison_carries_the_unit_it_is_given():
    card = StatCard.comparison(
        "Trend (2 weeks)", improving=True, value="20.0", unit="%", note=""
    )

    assert card.unit == "%"


def test_level_carries_the_unit_it_is_given():
    card = StatCard.level("Avg per day", state="low", value="300", unit="ml", note="")

    assert card.unit == "ml"


# -------------------------------------------------------------------------------------
#                                                                            arrow
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("improving", [True, False])
def test_comparison_carries_the_direction_the_arrow_points(improving):
    card = StatCard.comparison("Heavy days", improving=improving, value="1", note="")

    assert card.improving is improving


def test_a_level_can_point_at_a_direction_it_is_not_coloured_by():
    """A threshold owns the colour; a baseline owns the arrow, and one card can
    read against both."""
    card = StatCard.level(
        "Avg per day",
        state="high",
        value="3.0",
        note="",
        improving=True,
        show_icon=True,
    )

    assert card.state == "high"
    assert card.show_icon is True
    assert card.improving is True


def test_a_plain_card_points_at_nothing():
    assert StatCard("Pure alcohol", value="2.5").improving is False
