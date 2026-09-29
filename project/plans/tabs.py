from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class PlanTab:
    name: str
    title: str

    @classmethod
    def resolve(cls, name: str) -> "PlanTab":
        return BY_NAME[name]

    @property
    def url(self) -> str:
        return reverse(f"plans:tab_{self.name}")

    @property
    def template_name(self) -> str:
        return f"plans/tab_{self.name}.html"


TABS = (
    PlanTab("incomes", _("Incomes")),
    PlanTab("expenses", _("Expenses")),
    PlanTab("savings", _("Savings")),
    PlanTab("day", _("Sum per day")),
)
BY_NAME = {tab.name: tab for tab in TABS}
# the outcome the other three tabs feed, so it opens first
DEFAULT_TAB = BY_NAME["day"]
