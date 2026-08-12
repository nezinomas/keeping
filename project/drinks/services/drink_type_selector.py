from dataclasses import dataclass

from ..models import DrinkType
from ..tabs import DrinkTabs

SELECTING_TABS = ("index", "trends", "history")
STDAV_TABS = ("habits", "risk")

# the template maps these to markup
CHOICE = "choice"
FIXED = "fixed"
ABSENT = "absent"


@dataclass(frozen=True)
class DrinkTypeSelector:
    """Needs only the drink type, not a request or a user, so a tab can render
    for any type without one."""

    selected: str  # the raw value, e.g. "beer"

    state = CHOICE

    @property
    def label(self) -> str:
        return DrinkType(self.selected).label

    @property
    def options(self) -> list[tuple[str, str]]:
        # a list, not the zip it used to be: two templates iterate this on the
        # same page and an iterator would be empty for the second
        return list(zip(DrinkType.labels, DrinkType.values))


@dataclass(frozen=True)
class FixedDrinkTypeSelector:
    """A harm metric is defined in Std Av, so the tabs reading one name that
    unit and offer no choice."""

    selected = DrinkType.STDAV.value
    state = FIXED
    options = ()

    @property
    def label(self) -> str:
        return DrinkType(self.selected).label


@dataclass(frozen=True)
class NoDrinkTypeSelector:
    """Never None: a tab that reads no single amount still answers every
    question the template asks."""

    selected = ""
    label = ""
    options = ()
    state = ABSENT


DrinkTypeControl = DrinkTypeSelector | FixedDrinkTypeSelector | NoDrinkTypeSelector


def control_for_tab(tab: str, drink_type: str) -> DrinkTypeControl:
    """Data lists what was typed, each row in its own drink type, so it reads no
    single amount and wears no control."""
    name = DrinkTabs.resolve(tab).name

    if name in SELECTING_TABS:
        return DrinkTypeSelector(drink_type)

    if name in STDAV_TABS:
        return FixedDrinkTypeSelector()

    return NoDrinkTypeSelector()
