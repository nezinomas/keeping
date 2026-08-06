from dataclasses import dataclass, field

from ..models import DrinkType
from ..tabs import DrinkTabs

# tabs whose amounts follow the selected Drink type, and tabs read in Std Av
# whatever it says; the rest read no amount, so they show no switcher at all
SELECTING_TABS = ("index", "trends", "history")
STDAV_TABS = ("habits", "risk")


@dataclass(frozen=True)
class DrinkTypeSelector:
    """The drink-type switcher shown beside the quick-add form.

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

    @classmethod
    def for_tab(cls, tab: str, drink_type: str) -> "DrinkTypeSelector | None":
        """What one tab shows where the switcher goes.

        Overview, Trends and History read their amounts in the selected Drink
        type, so they offer the choice. Habits and Risk are harm metrics,
        defined in Std Av, so they name that unit and offer nothing. Data lists
        what was typed, each row in its own drink type, so it needs neither.
        """
        name = DrinkTabs.resolve(tab).name

        if name in SELECTING_TABS:
            return cls.for_drink_type(drink_type)

        if name in STDAV_TABS:
            stdav = DrinkType.STDAV
            return cls(selected=stdav.value, label=stdav.label)

        return None
