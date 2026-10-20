from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class ExpenseTab(Tab):
    app = "expenses"


TABS = Tabs(
    ExpenseTab("index", _("Overview")),
    ExpenseTab("data", _("Data")),
    ExpenseTab("types", _("Types")),
)
