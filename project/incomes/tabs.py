from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class IncomeTab(Tab):
    # one page for the whole journal, so unlike Counts a url needs no slug
    app = "incomes"


TABS = Tabs(
    IncomeTab("index", _("Overview")),
    IncomeTab("data", _("Data")),
    IncomeTab("types", _("Types")),
)
