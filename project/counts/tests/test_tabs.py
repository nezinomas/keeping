import pytest
from django.urls import reverse

from .. import views
from ..tabs import TABS


@pytest.mark.parametrize("tab", TABS)
def test_tab_url_names_the_counter(tab):
    assert tab.url("xxx") == reverse(tab.url_name, kwargs={"slug": "xxx"})


@pytest.mark.parametrize("tab", TABS)
def test_tab_derives_its_template_and_trigger(tab):
    assert tab.template_name == f"counts/tab_{tab.name}.html"
    assert tab.reload_trigger == f"reload{tab.name.title()}"


@pytest.mark.parametrize("tab", TABS)
def test_resolve_returns_the_named_tab(tab):
    assert TABS.resolve(tab.name, "index") is tab


def test_resolve_unknown_falls_back_to_the_default():
    assert TABS.resolve("nonsense", "index") is TABS["index"]
    assert TABS.resolve("", "index") is TABS["index"]


def test_resolve_takes_the_default_it_is_given():
    assert TABS.resolve("", "data").name == "data"


def test_the_default_tab_is_overview():
    assert views.TabViewMixin.default_tab is TABS["index"]
