from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class BookTab:
    name: str
    title: str

    @classmethod
    def resolve(cls, name: str) -> "BookTab":
        return BY_NAME[name]

    @property
    def url(self) -> str:
        return reverse(f"books:tab_{self.name}")

    @property
    def template_name(self) -> str:
        return f"books/tab_{self.name}.html"


TABS = (
    BookTab("index", _("Overview")),
    BookTab("data", _("Data")),
)
BY_NAME = {tab.name: tab for tab in TABS}
DEFAULT_TAB = BY_NAME["index"]
