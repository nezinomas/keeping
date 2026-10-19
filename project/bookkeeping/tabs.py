from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


@dataclass(frozen=True)
class DetailedTab(Tab):
    template: str

    @property
    def url(self) -> str:
        return reverse(f"bookkeeping:detailed_{self.name}")

    @property
    def template_name(self) -> str:
        return f"bookkeeping/detailed/tab_{self.template}.html"


TABS = Tabs(
    DetailedTab("incomes", _("Incomes"), "table"),
    DetailedTab("savings", _("Savings"), "table"),
    DetailedTab("expenses", _("Expenses"), "expenses"),
)
