import pytest

from ...lib.stat_card import (
    ComparisonStatCard,
    EmptyStatCard,
    LevelStatCard,
    StatCard,
)

# -------------------------------------------------------------------------------------
#                                                                            empty
# -------------------------------------------------------------------------------------


def test_empty_card():
    card = EmptyStatCard("Days dry", "No data")

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == "No data"
    assert card.show_icon is False


def test_empty_card_carries_the_pencil_that_would_fill_it():
    """The absent figure is the one most worth offering to set."""
    card = EmptyStatCard(
        "Daily limit", "No limit set", edit_url="/new/", edit_label="Set"
    )

    assert card.edit_url == "/new/"
    assert card.edit_label == "Set"


@pytest.mark.parametrize("field", ["value", "unit", "state", "show_icon", "improving"])
def test_empty_card_cannot_be_given_something_to_show(field):
    with pytest.raises(TypeError):
        EmptyStatCard("Days dry", "No data", **{field: "1"})


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
    card = ComparisonStatCard(
        "Heavy days", improving=improving, value="1", note="1 / 2"
    )

    assert card.state == expect_state


def test_comparison_always_shows_an_icon():
    """A direction is the one thing worth pointing an arrow at."""
    card = ComparisonStatCard("Heavy days", improving=True, value="1", note="1 / 2")

    assert card.show_icon is True


def test_comparison_carries_the_explanation():
    card = ComparisonStatCard(
        "Heavy days", improving=True, value="1", note="1 / 2", explanation=("why",)
    )

    assert card.explanation == ("why",)


def test_comparison_cannot_be_given_a_state_of_its_own():
    """Its direction is the state, so a second one could contradict it."""
    with pytest.raises(TypeError):
        ComparisonStatCard("Heavy days", improving=True, value="1", state="high")


# -------------------------------------------------------------------------------------
#                                                                            level
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["low", "medium", "high", "neutral"])
def test_level_keeps_the_state_it_is_given(state):
    card = LevelStatCard("This week", state=state, value="3.0", note="")

    assert card.state == state


def test_level_shows_no_icon_unless_it_is_asked_for_one():
    """A threshold on its own has no direction to point at."""
    card = LevelStatCard("This week", state="high", value="30.0", note="")

    assert card.show_icon is False


def test_level_carries_the_explanation():
    card = LevelStatCard(
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


def test_a_plain_card_cannot_be_given_a_state():
    """A reading with a threshold behind it is a LevelStatCard, and one with
    nothing to show is an EmptyStatCard."""
    with pytest.raises(TypeError):
        StatCard("Pure alcohol", value="2.5", state="high")


def test_an_explanation_carries_each_sentence_apart():
    card = StatCard("Drinking days", explanation=("a share", "a definition."))

    assert card.explanation == ("a share", "a definition.")


# -------------------------------------------------------------------------------------
#                                                                             unit
# -------------------------------------------------------------------------------------


def test_unit_is_carried_apart_from_the_figure():
    card = StatCard("Pure alcohol", value="2.5", unit="L")

    assert card.value == "2.5"
    assert card.unit == "L"


def test_a_figure_with_no_unit_carries_an_empty_one():
    card = StatCard("Days dry", value="12")

    assert card.unit == ""


@pytest.mark.parametrize(
    "factory",
    [
        lambda: EmptyStatCard("Days dry", "No data"),
        lambda: ComparisonStatCard("Heavy days", improving=True, value="1", note=""),
        lambda: LevelStatCard("This week", state="high", value="3.0", note=""),
        lambda: StatCard("Pure alcohol", value="2.5"),
    ],
)
def test_every_card_carries_a_unit(factory):
    assert factory().unit == ""


def test_comparison_carries_the_unit_it_is_given():
    card = ComparisonStatCard(
        "Trend (2 weeks)", improving=True, value="20.0", unit="%", note=""
    )

    assert card.unit == "%"


def test_level_carries_the_unit_it_is_given():
    card = LevelStatCard("Avg per day", state="low", value="300", unit="ml", note="")

    assert card.unit == "ml"


# -------------------------------------------------------------------------------------
#                                                                            arrow
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("improving", [True, False])
def test_comparison_carries_the_direction_the_arrow_points(improving):
    card = ComparisonStatCard("Heavy days", improving=improving, value="1", note="")

    assert card.improving is improving


def test_a_level_can_point_at_a_direction_it_is_not_coloured_by():
    """A threshold owns the colour; a baseline owns the arrow, and one card can
    read against both."""
    card = LevelStatCard(
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


# -------------------------------------------------------------------------------------
#                                                                     one contract
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "card",
    [
        StatCard("Pure alcohol", value="2.5"),
        EmptyStatCard("Days dry", "No data"),
        ComparisonStatCard("Heavy days", improving=True, value="1", note=""),
        LevelStatCard("This week", state="high", value="3.0", note=""),
    ],
)
def test_every_card_answers_what_the_template_reads(card):
    """The template asks one set of questions and never asks which class it got."""
    for name in (
        "title",
        "value",
        "unit",
        "note",
        "state",
        "show_icon",
        "improving",
        "explanation",
        "edit_url",
        "edit_label",
    ):
        assert hasattr(card, name), name
