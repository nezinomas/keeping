from dataclasses import dataclass

NEUTRAL = "neutral"
POSITIVE = "positive"
NEGATIVE = "negative"
WARNING = "warning"

UP = "up"
DOWN = "down"

_ARROW_GLYPHS = {UP: "↑", DOWN: "↓"}

# risk bands, as RiskStats names them, resolved to a tone
RISK_BAND_TONES = {
    "low": POSITIVE,
    "medium": WARNING,
    "high": NEGATIVE,
}


@dataclass(frozen=True)
class StatCard:
    """One summary tile: a title, a value, a note, and how to colour them.

    The three tab modules describe their metrics in different domain
    vocabularies — a risk band is low/medium/high, a year-over-year comparison
    is improving/worsening, an index metric is under/over a limit. This module
    is where each of those resolves into the only two presentation facts a tile
    needs: a `tone` and an `arrow`. The template then branches on nothing.
    """

    title: str
    value: str = ""
    note: str = ""
    tone: str = NEUTRAL
    arrow: str = ""
    blank: bool = False
    explanation: str = ""

    # -- constructors ------------------------------------------------------
    @classmethod
    def empty(cls, title: str, note: str) -> "StatCard":
        """A tile with nothing to show; renders a dash in place of a value."""
        return cls(title=title, note=note, blank=True)

    @classmethod
    def comparison(
        cls,
        title: str,
        *,
        improving: bool,
        value: str,
        note: str,
        explanation: str = "",
    ) -> "StatCard":
        """A metric read against a baseline: tone and arrow follow direction."""
        return cls(
            title=title,
            value=value,
            note=note,
            tone=POSITIVE if improving else NEGATIVE,
            arrow=DOWN if improving else UP,
            explanation=explanation,
        )

    @classmethod
    def risk_band(cls, title: str, *, band: str, value: str, note: str) -> "StatCard":
        """A metric read against risk guidelines rather than a baseline."""
        return cls(
            title=title,
            value=value,
            note=note,
            tone=RISK_BAND_TONES.get(band, NEUTRAL),
        )

    # -- readers -----------------------------------------------------------
    @property
    def css_class(self) -> str:
        return "" if self.tone == NEUTRAL else self.tone

    @property
    def arrow_glyph(self) -> str:
        return _ARROW_GLYPHS.get(self.arrow, "")
