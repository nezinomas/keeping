from dataclasses import dataclass

from ..models import DrinkType

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

    @classmethod
    def for_type(cls, drink_type: str) -> "DrinkTypeSelector":
        return cls(drink_type)

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

    @classmethod
    def for_type(cls, drink_type: str) -> "FixedDrinkTypeSelector":
        return cls()

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

    @classmethod
    def for_type(cls, drink_type: str) -> "NoDrinkTypeSelector":
        return cls()


DrinkTypeControl = DrinkTypeSelector | FixedDrinkTypeSelector | NoDrinkTypeSelector
