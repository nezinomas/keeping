from dataclasses import dataclass

# A level read against a threshold, or a direction read against a baseline.
# Templates map these to colours and icons.
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
    # apart from the figure: the skin sets it at a third of the figure's size,
    # and a template cannot split "300 ml" without guessing where the number ends
    unit: str = ""
    note: str = ""
    state: str = NEUTRAL
    show_icon: bool = False
    # which way the arrow points, kept apart from `state` so a card read against
    # a threshold can still point at a baseline
    improving: bool = False
    # one sentence per part: the template renders each as its own paragraph, so
    # nothing here decides how they are separated
    explanation: tuple[str, ...] = ()
    # a figure the user can change: the url a pencil beside it opens, and what
    # that pencil is called. The figure itself is still read, never pressed.
    edit_url: str = ""
    edit_label: str = ""

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
        explanation: tuple[str, ...] = (),
    ) -> "StatCard":
        """A metric read against a baseline, so it has a direction."""
        return cls(
            title=title,
            value=value,
            unit=unit,
            note=note,
            state=IMPROVING if improving else WORSENING,
            show_icon=True,
            improving=improving,
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
        explanation: tuple[str, ...] = (),
        improving: bool = False,
        show_icon: bool = False,
    ) -> "StatCard":
        """A metric read against a threshold, which colours it — and optionally
        against a baseline too, which only points its arrow."""
        return cls(
            title=title,
            value=value,
            unit=unit,
            note=note,
            state=state,
            show_icon=show_icon,
            improving=improving,
            explanation=explanation,
        )
