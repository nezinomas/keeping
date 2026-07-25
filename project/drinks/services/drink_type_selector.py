from dataclasses import dataclass, field

from ..models import DrinkType


@dataclass(frozen=True)
class DrinkTypeSelector:
    """The drink-type switcher shown on every drinks tab.

    Needs only the drink type itself — not a request, not a user — so a tab
    can be rendered for any drink type without one.
    """

    selected: str  # the raw value, e.g. "beer"
    label: str  # its translated label, e.g. "Beer"
    options: list[tuple[str, str]] = field(default_factory=list)  # (label, value)

    @classmethod
    def for_drink_type(cls, drink_type: str) -> "DrinkTypeSelector":
        return cls(
            selected=drink_type,
            label=DrinkType(drink_type).label,
            # a list, not the zip it used to be: two templates iterate this on
            # the same page and an iterator would be empty for the second
            options=list(zip(DrinkType.labels, DrinkType.values)),
        )
