from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class DetailedTab:
    name: str
    title: str
    template: str

    @classmethod
    def resolve(cls, name: str) -> "DetailedTab":
        return BY_NAME[name]

    @property
    def url(self) -> str:
        return reverse(f"bookkeeping:detailed_{self.name}")

    @property
    def template_name(self) -> str:
        return f"bookkeeping/detailed/tab_{self.template}.html"


TABS = (
    DetailedTab("incomes", _("Incomes"), "table"),
    DetailedTab("savings", _("Savings"), "table"),
    DetailedTab("expenses", _("Expenses"), "expenses"),
)
BY_NAME = {tab.name: tab for tab in TABS}
DEFAULT_TAB = BY_NAME["incomes"]
