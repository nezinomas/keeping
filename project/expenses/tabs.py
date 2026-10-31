from datetime import date

from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs
from .services.month_filter import MonthFilter


class ExpenseTab(Tab):
    app = "expenses"


class DataTab(ExpenseTab):
    @property
    def url(self) -> str:
        return MonthFilter.at(date.today()).url()


TABS = Tabs(
    ExpenseTab("index", _("Overview")),
    DataTab("data", _("Data")),
    ExpenseTab("types", _("Types")),
)
