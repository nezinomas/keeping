from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class PlanTab(Tab):
    app = "plans"


TABS = Tabs(
    PlanTab("incomes", _("Incomes")),
    PlanTab("expenses", _("Expenses")),
    PlanTab("savings", _("Savings")),
    PlanTab("day", _("Sum per day")),
)
