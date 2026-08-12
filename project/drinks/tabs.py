from collections.abc import Callable
from dataclasses import dataclass

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from .services.drink_type_selector import (
    DrinkTypeControl,
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
)


@dataclass(frozen=True)
class DrinkTab:
    """One drinks tab. Every spelling of its name — url, template, client
    event — is derived here rather than retyped at the call site."""

    name: str
    title: str
    control: Callable[[str], DrinkTypeControl]

    @property
    def url_name(self) -> str:
        return f"tab_{self.name}"

    @property
    def url(self) -> str:
        return reverse(f"drinks:{self.url_name}")

    @property
    def template_name(self) -> str:
        return f"drinks/tab_{self.name}.html"

    @property
    def reload_trigger(self) -> str:
        return f"reload{self.name.title()}"

    def form_url(self, url_name: str):
        return reverse_lazy(url_name, kwargs={"tab": self.name})

    @classmethod
    def resolve(cls, raw: str | None, default: str = "") -> "DrinkTab":
        """`default` is the tab that owns the change when a url kwarg, query
        string or form field named no valid one."""
        return BY_NAME.get(raw) or BY_NAME.get(default) or DEFAULT_TAB


# in the order the tab row draws them, which is the order arrow keys walk
TABS = (
    DrinkTab("index", _("Overview"), DrinkTypeSelector.for_type),
    DrinkTab("trends", _("Trends"), DrinkTypeSelector.for_type),
    DrinkTab("habits", _("Habits"), FixedDrinkTypeSelector.for_type),
    DrinkTab("risk", _("Risk"), FixedDrinkTypeSelector.for_type),
    DrinkTab("history", _("History"), DrinkTypeSelector.for_type),
    DrinkTab("data", _("Data"), NoDrinkTypeSelector.for_type),
)
BY_NAME = {tab.name: tab for tab in TABS}
DEFAULT_TAB = BY_NAME["index"]
