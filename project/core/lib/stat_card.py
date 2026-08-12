from dataclasses import dataclass

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
    note: str = ""
    edit_url: str = ""
    edit_label: str = ""

    value: str = ""
    unit: str = ""
    show_icon = False
    improving = False
    explanation: tuple[str, ...] = ()

    state = NEUTRAL


@dataclass(frozen=True)
class EmptyStatCard:
    """A tile with nothing to show, and often the pencil that would fill it."""

    title: str
    note: str = ""
    edit_url: str = ""
    edit_label: str = ""

    value = ""
    unit = ""
    show_icon = False
    improving = False
    explanation = ()

    state = EMPTY


@dataclass(frozen=True)
class ComparisonStatCard:
    """A metric read against a baseline, so its direction is its state."""

    title: str
    note: str = ""
    edit_url = ""
    edit_label = ""

    value: str = ""
    unit: str = ""
    show_icon = True
    improving: bool = False
    explanation: tuple[str, ...] = ()

    @property
    def state(self) -> str:
        return IMPROVING if self.improving else WORSENING


@dataclass(frozen=True)
class LevelStatCard:
    """A metric read against a threshold, which colours it — and optionally
    against a baseline too, which only points its arrow."""

    title: str
    note: str = ""
    edit_url = ""
    edit_label = ""

    value: str = ""
    unit: str = ""
    show_icon: bool = False
    improving: bool = False
    explanation: tuple[str, ...] = ()

    state: str = NEUTRAL


Card = StatCard | EmptyStatCard | ComparisonStatCard | LevelStatCard
