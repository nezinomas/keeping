import json

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ..lib.drink_type_control import (
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
)
from ..tabs import TABS, tab_reload_response

NAMES = tuple(tab.name for tab in TABS)


@given(
    raw=st.text().filter(lambda raw: raw not in NAMES),
    default=st.sampled_from(NAMES),
)
@example(raw="xxx", default="index")
@example(raw="", default="index")
@example(raw="Index", default="index")
@example(raw="target", default="index")
@example(raw="Habits", default="index")
@example(raw="xxx", default="data")
@example(raw="", default="data")
def test_resolve_falls_back_to_the_default_for_an_unknown_tab(raw, default):
    assert TABS.resolve(raw, default).name == default


def test_each_tab_declares_its_trigger_url_and_title_in_nav_order():
    actual = [(tab.name, tab.reload_trigger, tab.url, str(tab.title)) for tab in TABS]

    assert actual == [
        ("index", "reloadIndex", "/drinks/index/", "Apžvalga"),
        ("trends", "reloadTrends", "/drinks/trends/", "Tendencijos"),
        ("habits", "reloadHabits", "/drinks/habits/", "Įpročiai"),
        ("risk", "reloadRisk", "/drinks/risk/", "Rizikos"),
        ("history", "reloadHistory", "/drinks/history/", "Istorija"),
        ("data", "reloadData", "/drinks/data/", "Duomenys"),
    ]


@pytest.mark.parametrize(
    "url_name, expect",
    [
        ("drinks:new", "/drinks/risk/new/"),
        ("drinks:target_new", "/drinks/risk/target/new/"),
    ],
)
def test_form_url_carries_the_tab(url_name, expect):
    assert str(TABS["risk"].form_url(url_name)) == expect


@pytest.mark.parametrize("name", ["index", "trends", "history"])
def test_a_tab_reading_the_selected_type_offers_the_choice(name):
    control = TABS[name].control("wine")

    assert isinstance(control, DrinkTypeSelector)
    assert control.state == "choice"
    assert control.selected == "wine"


@pytest.mark.parametrize("name", ["habits", "risk"])
def test_a_tab_reading_a_harm_metric_names_std_av(name):
    control = TABS[name].control("wine")

    assert isinstance(control, FixedDrinkTypeSelector)
    assert control.state == "fixed"


def test_a_tab_reading_no_single_amount_draws_no_switcher():
    """The Data tab lists what was typed, each row in its own drink type."""
    control = TABS["data"].control("wine")

    assert isinstance(control, NoDrinkTypeSelector)
    assert control.state == "absent"


def test_a_reload_response_carries_no_body():
    response = tab_reload_response("trends")

    assert response.status_code == 204
    assert not response.content


@pytest.mark.parametrize(
    "raw, expect", [("trends", "reloadTrends"), ("nonsense", "reloadIndex")]
)
def test_a_reload_response_fires_the_resolved_tabs_trigger(raw, expect):
    response = tab_reload_response(raw)

    assert json.loads(response.headers["HX-Trigger"]) == {expect: {}}
