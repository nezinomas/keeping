import pytest
from django.urls import reverse

from ..tabs import DEFAULT_TAB, TABS, CountTab


@pytest.mark.parametrize("tab", TABS)
def test_tab_url_names_the_counter(tab):
    assert tab.url("xxx") == reverse(tab.url_name, kwargs={"slug": "xxx"})


@pytest.mark.parametrize("tab", TABS)
def test_tab_derives_its_template_and_trigger(tab):
    assert tab.template_name == f"counts/tab_{tab.name}.html"
    assert tab.reload_trigger == f"reload{tab.name.title()}"


@pytest.mark.parametrize("tab", TABS)
def test_resolve_returns_the_named_tab(tab):
    assert CountTab.resolve(tab.name) is tab


def test_resolve_unknown_falls_back_to_the_default():
    assert CountTab.resolve("nonsense") is DEFAULT_TAB
    assert CountTab.resolve(None) is DEFAULT_TAB


def test_resolve_takes_the_default_it_is_given():
    assert CountTab.resolve(None, default="data").name == "data"


def test_the_default_tab_is_overview():
    assert DEFAULT_TAB.name == "index"
