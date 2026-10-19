import pytest
from django.test import override_settings
from django.urls import include, path

from ..tabs import Tab, Tabs


class ShopTab(Tab):
    app = "shop"


TABS = Tabs(ShopTab("index", "Overview"), ShopTab("data", "Data"))

urlpatterns = [
    path(
        "shop/",
        include(([path("data/", lambda request: None, name="tab_data")], "shop")),
    ),
]


@override_settings(ROOT_URLCONF=__name__)
def test_a_tab_derives_its_url_and_template_from_the_app():
    tab = ShopTab("data", "Data")

    assert tab.url == "/shop/data/"
    assert tab.template_name == "shop/tab_data.html"


@pytest.mark.parametrize("name, position", [("index", 0), ("data", 1)])
def test_tabs_are_found_by_name_in_their_order(name, position):
    assert TABS[name] is TABS[position]
    assert TABS[name].name == name


def test_an_unknown_name_raises():
    with pytest.raises(KeyError):
        TABS["missing"]
