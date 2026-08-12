import pytest

from ..lib.drink_type_control import (
    DrinkTypeSelector,
    FixedDrinkTypeSelector,
    NoDrinkTypeSelector,
)
from ..tabs import TABS, DrinkTab

NAMES = tuple(tab.name for tab in TABS)

# -------------------------------------------------------------------------------------
#                                                                          resolve
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_resolve_keeps_a_known_tab(name):
    assert DrinkTab.resolve(name).name == name


@pytest.mark.parametrize("raw", ["xxx", "", None, "Index", "target", "Habits"])
def test_resolve_falls_back_for_an_unknown_tab(raw):
    # the default is Overview, and adding a tab must not quietly become the
    # place an unrecognised value lands
    assert DrinkTab.resolve(raw).name == "index"


@pytest.mark.parametrize("raw", ["xxx", None])
def test_resolve_honours_an_explicit_default(raw):
    assert DrinkTab.resolve(raw, default="data").name == "data"


def test_an_explicit_default_does_not_override_a_known_tab():
    assert DrinkTab.resolve("risk", default="data").name == "risk"


# -------------------------------------------------------------------------------------
#                                                                   reload_trigger
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, expect",
    [
        ("index", "reloadIndex"),
        ("data", "reloadData"),
        ("history", "reloadHistory"),
        ("trends", "reloadTrends"),
        ("risk", "reloadRisk"),
        ("habits", "reloadHabits"),
    ],
)
def test_reload_trigger(name, expect):
    assert DrinkTab.resolve(name).reload_trigger == expect


def test_every_tab_has_a_distinct_trigger():
    triggers = [tab.reload_trigger for tab in TABS]

    assert len(set(triggers)) == len(TABS)


# -------------------------------------------------------------------------------------
#                                                                             urls
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, expect",
    [
        ("index", "/drinks/index/"),
        ("data", "/drinks/data/"),
        ("history", "/drinks/history/"),
        ("trends", "/drinks/trends/"),
        ("risk", "/drinks/risk/"),
        ("habits", "/drinks/habits/"),
    ],
)
def test_url_resolves_for_every_tab(name, expect):
    assert DrinkTab.resolve(name).url == expect


@pytest.mark.parametrize("url_name", ["drinks:new", "drinks:target_new"])
def test_form_url_carries_the_tab(url_name):
    actual = DrinkTab.resolve("risk").form_url(url_name)

    assert str(actual).endswith("/risk/new/") or str(actual).endswith(
        "/risk/target/new/"
    )


def test_form_url_normalises_an_unknown_tab():
    actual = DrinkTab.resolve("xxx").form_url("drinks:new")

    assert str(actual) == "/drinks/index/new/"


# -------------------------------------------------------------------------------------
#                                                                            title
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, expect",
    [
        ("index", "Apžvalga"),
        ("trends", "Tendencijos"),
        ("habits", "Įpročiai"),
        ("risk", "Rizikos"),
        ("history", "Istorija"),
        ("data", "Duomenys"),
    ],
)
def test_title_is_translated(name, expect):
    assert str(DrinkTab.resolve(name).title) == expect


# -------------------------------------------------------------------------------------
#                                                                    the tab table
# -------------------------------------------------------------------------------------


def test_the_tabs_are_declared_in_the_order_the_nav_draws_them():
    # the row is a tablist now, so this is also the order arrow keys walk
    assert NAMES == ("index", "trends", "habits", "risk", "history", "data")


@pytest.mark.parametrize("name", ["index", "trends", "history"])
def test_a_tab_reading_the_selected_type_offers_the_choice(name):
    control = DrinkTab.resolve(name).control("wine")

    assert isinstance(control, DrinkTypeSelector)
    assert control.state == "choice"
    assert control.selected == "wine"


@pytest.mark.parametrize("name", ["habits", "risk"])
def test_a_tab_reading_a_harm_metric_names_std_av(name):
    control = DrinkTab.resolve(name).control("wine")

    assert isinstance(control, FixedDrinkTypeSelector)
    assert control.state == "fixed"


def test_a_tab_reading_no_single_amount_draws_no_switcher():
    """The Data tab lists what was typed, each row in its own drink type."""
    control = DrinkTab.resolve("data").control("wine")

    assert isinstance(control, NoDrinkTypeSelector)
    assert control.state == "absent"
