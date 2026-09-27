import pytest
from django.urls import reverse

from ..tabs import DEFAULT_TAB, TABS, BookTab


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_derives_its_url_and_template(tab):
    assert tab.url == reverse(f"books:tab_{tab.name}")
    assert tab.template_name == f"books/tab_{tab.name}.html"


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_resolve_returns_the_named_tab(tab):
    assert BookTab.resolve(tab.name) is tab


def test_resolve_refuses_an_unknown_name():
    with pytest.raises(KeyError):
        BookTab.resolve("nonsense")


def test_the_tabs_are_overview_and_data():
    assert [tab.name for tab in TABS] == ["index", "data"]
    assert DEFAULT_TAB.name == "index"
