from .. import views
from ..tabs import TABS


def test_the_tabs_are_overview_data_and_types_in_nav_order():
    actual = [(tab.name, tab.url, tab.template_name) for tab in TABS]

    assert actual == [
        ("index", "/incomes/index/", "incomes/tab_index.html"),
        ("data", "/incomes/data/", "incomes/tab_data.html"),
        ("types", "/incomes/types/", "incomes/tab_types.html"),
    ]
    assert views.TabViewMixin.default_tab is TABS["index"]
