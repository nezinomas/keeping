from dataclasses import dataclass

# The one vocabulary every tab describes a metric in. It is the union of what
# the three tabs used to say separately: a level read against a threshold, or a
# direction read against a baseline. Templates map these to colours and icons.
EMPTY = "empty"
NEUTRAL = "neutral"
LOW = "low"
MEDIUM = "medium"
HIGH = "high"
IMPROVING = "improving"
WORSENING = "worsening"


@dataclass(frozen=True)
class StatCard:
    """One summary tile on a tab: a title, a value, a note, and a state.

    The three tab modules used to each publish their own `state` vocabulary and
    each have their own near-identical template decode it. This is the single
    vocabulary they now share, so one template decodes it once.
    """

    title: str
    value: str = ""
    # kept apart from the figure rather than baked into it: the skin sets a unit
    # at a third of the figure's size, and a "300 ml" string cannot be split in
    # a template without guessing where the number ends
    unit: str = ""
    note: str = ""
    state: str = NEUTRAL
    show_icon: bool = False
    explanation: str = ""

    @classmethod
    def empty(cls, title: str, note: str) -> "StatCard":
        """A tile with nothing to show."""
        return cls(title=title, note=note, state=EMPTY)

    @classmethod
    def comparison(
        cls,
        title: str,
        *,
        improving: bool,
        value: str,
        note: str,
        unit: str = "",
        explanation: str = "",
    ) -> "StatCard":
        """A metric read against a baseline, so it has a direction."""
        return cls(
            title=title,
            value=value,
            unit=unit,
            note=note,
            state=IMPROVING if improving else WORSENING,
            show_icon=True,
            explanation=explanation,
        )

    @classmethod
    def level(
        cls,
        title: str,
        *,
        state: str,
        value: str,
        note: str,
        unit: str = "",
        explanation: str = "",
    ) -> "StatCard":
        """A metric read against a threshold: a level, with no direction."""
        return cls(
            title=title,
            value=value,
            unit=unit,
            note=note,
            state=state,
            explanation=explanation,
        )
