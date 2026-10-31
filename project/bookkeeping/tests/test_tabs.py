import pytest
from django.urls import reverse

from .. import views
from ..tabs import TABS


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_derives_its_url(tab):
    assert tab.url == reverse(f"bookkeeping:detailed_{tab.name}")


@pytest.mark.parametrize(
    "name, template",
    [("incomes", "table"), ("savings", "table"), ("expenses", "expenses")],
)
def test_tab_template_single_table_tabs_share_one(name, template):
    tab = TABS[name]

    assert tab.template_name == f"bookkeeping/detailed/tab_{template}.html"


def test_the_tabs_are_incomes_savings_and_expenses():
    assert [tab.name for tab in TABS] == ["incomes", "savings", "expenses"]
    assert [str(tab.title) for tab in TABS] == ["Pajamos", "Taupymas", "Išlaidos"]
    assert views.DetailedTabMixin.default_tab is TABS["incomes"]
