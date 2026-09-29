import pytest
from django.urls import reverse

from ..tabs import DEFAULT_TAB, TABS, PlanTab


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_derives_its_url_and_template(tab):
    assert tab.url == reverse(f"plans:tab_{tab.name}")
    assert tab.template_name == f"plans/tab_{tab.name}.html"


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_resolve_returns_the_named_tab(tab):
    assert PlanTab.resolve(tab.name) is tab


def test_resolve_refuses_an_unknown_name():
    with pytest.raises(KeyError):
        PlanTab.resolve("nonsense")


def test_the_tabs_are_incomes_expenses_savings_and_day_in_order():
    assert [tab.name for tab in TABS] == ["incomes", "expenses", "savings", "day"]
    assert DEFAULT_TAB.name == "day"
