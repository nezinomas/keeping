from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class CountTab:
    name: str
    title: str

    @classmethod
    def resolve(cls, raw: str | None, default: str = "") -> "CountTab":
        return BY_NAME.get(raw) or BY_NAME.get(default) or DEFAULT_TAB

    @property
    def url_name(self) -> str:
        return f"counts:tab_{self.name}"

    # every counts route belongs to one Counter, so a url needs the slug too
    def url(self, slug: str) -> str:
        return reverse(self.url_name, kwargs={"slug": slug})

    @property
    def template_name(self) -> str:
        return f"counts/tab_{self.name}.html"

    @property
    def reload_trigger(self) -> str:
        return f"reload{self.name.title()}"


TABS = (
    CountTab("index", _("Overview")),
    CountTab("history", _("History")),
    CountTab("data", _("Data")),
)
BY_NAME = {tab.name: tab for tab in TABS}
DEFAULT_TAB = BY_NAME["index"]
