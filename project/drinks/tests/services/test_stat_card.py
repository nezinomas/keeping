import pytest

from ...services.stat_card import StatCard

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
        "Heavy days", improving=True, value="1", note="1 / 2", explanation="why"
    )

    assert card.explanation == "why"


# -------------------------------------------------------------------------------------
#                                                                            level
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["low", "medium", "high", "neutral", "empty"])
def test_level_keeps_the_state_it_is_given(state):
    card = StatCard.level("This week", state=state, value="3.0", note="")

    assert card.state == state


def test_level_never_shows_an_icon():
    """A level is read against a threshold — there is no direction to point."""
    card = StatCard.level("This week", state="high", value="30.0", note="")

    assert card.show_icon is False


def test_level_carries_the_explanation():
    card = StatCard.level(
        "This week", state="high", value="30.0", note="", explanation="why"
    )

    assert card.explanation == "why"


# -------------------------------------------------------------------------------------
#                                                                         defaults
# -------------------------------------------------------------------------------------


def test_defaults_render_a_plain_card():
    card = StatCard("Pure alcohol", value="2.5 L", note="this year")

    assert card.state == "neutral"
    assert card.show_icon is False
    assert card.explanation == ""
