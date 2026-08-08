from dataclasses import dataclass

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

# in the order the tab row draws them, which is the order arrow keys walk
TAB_TITLES = {
    "index": _("Overview"),
    "trends": _("Trends"),
    "habits": _("Habits"),
    "risk": _("Risk"),
    "history": _("History"),
    "data": _("Data"),
}
TAB_NAMES = tuple(TAB_TITLES)
DEFAULT_TAB = "index"


@dataclass(frozen=True)
class DrinkTab:
    """One drinks tab, and the HTMX vocabulary that goes with it.

    Two naming conventions live here rather than at every call site: a tab is
    reloaded by the client event `reload` plus its title-cased name, and its
    partial is served by the url named `drinks:tab_` plus its name.
    """

    name: str

    @property
    def title(self) -> str:
        return TAB_TITLES[self.name]

    @property
    def reload_trigger(self) -> str:
        return f"reload{self.name.title()}"

    @property
    def url(self) -> str:
        return reverse(f"drinks:tab_{self.name}")

    def form_url(self, url_name: str):
        return reverse_lazy(url_name, kwargs={"tab": self.name})


class DrinkTabs:
    """The set of drinks tabs, and the one place a raw tab value is normalised."""

    @classmethod
    def all(cls) -> list[DrinkTab]:
        return [DrinkTab(name) for name in TAB_NAMES]

    @classmethod
    def resolve(cls, raw: str | None, default: str = DEFAULT_TAB) -> DrinkTab:
        """Normalise a tab value from a url kwarg, query string or form field.

        `default` is the tab that owns the change when the caller named no
        valid one — the Data tab for a drink, the Overview tab for a goal.
        """
        return DrinkTab(raw if raw in TAB_NAMES else default)
