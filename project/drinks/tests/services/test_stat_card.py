import pytest

from ...services.stat_card import StatCard

# -------------------------------------------------------------------------------------
#                                                                            empty
# -------------------------------------------------------------------------------------


def test_empty_card_is_blank_and_neutral():
    card = StatCard.empty("Days dry", "No data")

    assert card.blank is True
    assert card.value == ""
    assert card.note == "No data"
    assert card.tone == "neutral"
    assert card.arrow == ""


# -------------------------------------------------------------------------------------
#                                                                       comparison
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "improving, expect_tone, expect_arrow",
    [
        (True, "positive", "down"),
        (False, "negative", "up"),
    ],
)
def test_comparison_resolves_direction(improving, expect_tone, expect_arrow):
    card = StatCard.comparison(
        "Heavy days", improving=improving, value="1", note="1 / 2"
    )

    assert card.tone == expect_tone
    assert card.arrow == expect_arrow
    assert card.blank is False


def test_comparison_carries_the_explanation():
    card = StatCard.comparison(
        "Heavy days", improving=True, value="1", note="1 / 2", explanation="why"
    )

    assert card.explanation == "why"


# -------------------------------------------------------------------------------------
#                                                                        risk_band
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "band, expect_tone",
    [
        ("low", "positive"),
        ("medium", "warning"),
        ("high", "negative"),
        # RiskStats also emits these; neither maps to a colour
        ("empty", "neutral"),
        ("neutral", "neutral"),
    ],
)
def test_risk_band_resolves_to_a_tone(band, expect_tone):
    card = StatCard.risk_band("This week", band=band, value="3.0", note="")

    assert card.tone == expect_tone


def test_risk_band_never_shows_an_arrow():
    """A band is a level, not a comparison — nothing to point at."""
    card = StatCard.risk_band("This week", band="high", value="30.0", note="")

    assert card.arrow == ""


# -------------------------------------------------------------------------------------
#                                                                      presentation
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tone, expect",
    [
        ("neutral", ""),
        ("positive", "positive"),
        ("negative", "negative"),
        ("warning", "warning"),
    ],
)
def test_css_class_omits_the_neutral_tone(tone, expect):
    assert StatCard("t", tone=tone).css_class == expect


@pytest.mark.parametrize(
    "arrow, expect",
    [
        ("down", "↓"),
        ("up", "↑"),
        ("", ""),
    ],
)
def test_arrow_glyph(arrow, expect):
    assert StatCard("t", arrow=arrow).arrow_glyph == expect


def test_defaults_render_a_plain_card():
    card = StatCard("Pure alcohol", value="2.5 L", note="this year")

    assert card.css_class == ""
    assert card.arrow_glyph == ""
    assert card.blank is False
    assert card.explanation == ""
