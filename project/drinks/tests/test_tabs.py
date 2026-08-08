import pytest

from ..tabs import TAB_NAMES, DrinkTab, DrinkTabs

# -------------------------------------------------------------------------------------
#                                                                          resolve
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", TAB_NAMES)
def test_resolve_keeps_a_known_tab(name):
    assert DrinkTabs.resolve(name).name == name


@pytest.mark.parametrize("raw", ["xxx", "", None, "Index", "target", "Habits"])
def test_resolve_falls_back_for_an_unknown_tab(raw):
    # the default is Overview, and adding a tab must not quietly become the
    # place an unrecognised value lands
    assert DrinkTabs.resolve(raw).name == "index"


@pytest.mark.parametrize("raw", ["xxx", None])
def test_resolve_honours_an_explicit_default(raw):
    assert DrinkTabs.resolve(raw, default="data").name == "data"


def test_an_explicit_default_does_not_override_a_known_tab():
    assert DrinkTabs.resolve("risk", default="data").name == "risk"


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
    assert DrinkTab(name).reload_trigger == expect


def test_every_tab_has_a_distinct_trigger():
    triggers = [tab.reload_trigger for tab in DrinkTabs.all()]

    assert len(set(triggers)) == len(TAB_NAMES)


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
    assert DrinkTab(name).url == expect


@pytest.mark.parametrize("url_name", ["drinks:new", "drinks:target_new"])
def test_form_url_carries_the_tab(url_name):
    actual = DrinkTabs.resolve("risk").form_url(url_name)

    assert str(actual).endswith("/risk/new/") or str(actual).endswith(
        "/risk/target/new/"
    )


def test_form_url_normalises_an_unknown_tab():
    actual = DrinkTabs.resolve("xxx").form_url("drinks:new")

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
    assert str(DrinkTab(name).title) == expect


# -------------------------------------------------------------------------------------
#                                                                              all
# -------------------------------------------------------------------------------------


def test_the_tabs_are_declared_in_the_order_the_nav_draws_them():
    # the row is a tablist now, so this is also the order arrow keys walk
    assert TAB_NAMES == ("index", "trends", "habits", "risk", "history", "data")


def test_all_returns_every_tab_in_order():
    assert [tab.name for tab in DrinkTabs.all()] == list(TAB_NAMES)
