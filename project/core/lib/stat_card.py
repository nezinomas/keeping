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
    """A figure that stands on its own: no threshold behind it, no baseline."""

    title: str
    value: str = ""
    # apart from the figure: the skin sets it at a third of the figure's size,
    # and a template cannot split "300 ml" without guessing where the number ends
    unit: str = ""
    note: str = ""
    # one sentence per part: the template renders each as its own paragraph, so
    # nothing here decides how they are separated
    explanation: tuple[str, ...] = ()
    # a figure the user can change: the url a pencil beside it opens, and what
    # that pencil is called. The figure itself is still read, never pressed.
    edit_url: str = ""
    edit_label: str = ""

    # Not fields - invalid states are unconstructible (e.g., `StatCard(state="high")`)
    state = NEUTRAL
    show_icon = False
    improving = False


@dataclass(frozen=True)
class EmptyStatCard:
    """A tile with nothing to show, and often the pencil that would fill it."""

    title: str
    note: str = ""
    edit_url: str = ""
    edit_label: str = ""

    value = ""
    unit = ""
    state = EMPTY
    show_icon = False
    improving = False
    explanation = ()


@dataclass(frozen=True)
class ComparisonStatCard:
    """A metric read against a baseline, so its direction is its state."""

    title: str
    improving: bool = False
    value: str = ""
    unit: str = ""
    note: str = ""
    explanation: tuple[str, ...] = ()

    show_icon = True
    edit_url = ""
    edit_label = ""

    @property
    def state(self) -> str:
        return IMPROVING if self.improving else WORSENING


@dataclass(frozen=True)
class LevelStatCard:
    """A metric read against a threshold, which colours it — and optionally
    against a baseline too, which only points its arrow."""

    title: str
    state: str = NEUTRAL
    value: str = ""
    unit: str = ""
    note: str = ""
    # kept apart from `state` so a card read against a threshold can still point
    # at a baseline
    improving: bool = False
    show_icon: bool = False
    explanation: tuple[str, ...] = ()

    edit_url = ""
    edit_label = ""


Card = StatCard | EmptyStatCard | ComparisonStatCard | LevelStatCard
