from collections.abc import Callable
from dataclasses import dataclass

from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_htmx.http import trigger_client_event

from ..core.tabs import Tab, Tabs
from .lib.drink_type_control import (
    DrinkTypeControl,
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
)


@dataclass(frozen=True)
class DrinkTab(Tab):
    app = "drinks"
    control: Callable[[str], DrinkTypeControl]

    @classmethod
    def resolve(cls, raw: str | None, default: str = "index") -> "DrinkTab":
        """`default` is the tab that owns the change when a url kwarg, query
        string or form field named no valid one."""
        try:
            return TABS[raw or default]
        except KeyError:
            return TABS[default]

    @property
    def url_name(self) -> str:
        return f"tab_{self.name}"

    @property
    def reload_trigger(self) -> str:
        return f"reload{self.name.title()}"

    def form_url(self, url_name: str):
        return reverse_lazy(url_name, kwargs={"tab": self.name})


# in the order the tab row draws them, which is the order arrow keys walk
TABS = Tabs(
    DrinkTab("index", _("Overview"), DrinkTypeSelector.for_type),
    DrinkTab("trends", _("Trends"), DrinkTypeSelector.for_type),
    DrinkTab("habits", _("Habits"), FixedDrinkTypeSelector.for_type),
    DrinkTab("risk", _("Risk"), FixedDrinkTypeSelector.for_type),
    DrinkTab("history", _("History"), DrinkTypeSelector.for_type),
    DrinkTab("data", _("Data"), NoDrinkTypeSelector.for_type),
)


def tab_reload_response(raw: str, default: str = "index") -> HttpResponse:
    response = HttpResponse(status=204)
    trigger_client_event(
        response=response, name=DrinkTab.resolve(raw, default).reload_trigger, params={}
    )

    return response
