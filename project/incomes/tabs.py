from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class IncomeTab:
    name: str
    title: str

    @classmethod
    def resolve(cls, name: str) -> "IncomeTab":
        return BY_NAME[name]

    # one page for the whole journal, so unlike Counts a url needs no slug
    @property
    def url(self) -> str:
        return reverse(f"incomes:tab_{self.name}")

    @property
    def template_name(self) -> str:
        return f"incomes/tab_{self.name}.html"


TABS = (
    IncomeTab("index", _("Overview")),
    IncomeTab("data", _("Data")),
    IncomeTab("types", _("Types")),
)
BY_NAME = {tab.name: tab for tab in TABS}
DEFAULT_TAB = BY_NAME["index"]
