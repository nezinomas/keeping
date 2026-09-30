import pytest
from django.urls import reverse

from ..tabs import BY_NAME, DEFAULT_TAB, TABS, DetailedTab


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_derives_its_url(tab):
    assert tab.url == reverse(f"bookkeeping:detailed_{tab.name}")


@pytest.mark.parametrize(
    "name, template",
    [("incomes", "table"), ("savings", "table"), ("expenses", "expenses")],
)
def test_tab_template_single_table_tabs_share_one(name, template):
    tab = DetailedTab.resolve(name)

    assert tab.template_name == f"bookkeeping/detailed/tab_{template}.html"


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_resolve_returns_the_named_tab(tab):
    assert DetailedTab.resolve(tab.name) is tab
    assert BY_NAME[tab.name] is tab


def test_resolve_refuses_an_unknown_name():
    with pytest.raises(KeyError):
        DetailedTab.resolve("nonsense")


def test_the_tabs_are_incomes_savings_and_expenses():
    assert [tab.name for tab in TABS] == ["incomes", "savings", "expenses"]
    assert [str(tab.title) for tab in TABS] == ["Pajamos", "Taupymas", "Išlaidos"]
    assert DEFAULT_TAB.name == "incomes"
