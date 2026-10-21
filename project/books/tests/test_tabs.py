import pytest
from django.urls import reverse

from .. import views
from ..tabs import TABS


@pytest.mark.parametrize(
    ("name", "url_name", "kwargs", "template"),
    [
        ("index", "books:tab_index", {}, "books/tab_index.html"),
        ("data", "books:tab_data", {"scope": "year"}, "books/tab_data.html"),
    ],
    ids=["index", "data"],
)
def test_tab_derives_its_url_and_template(name, url_name, kwargs, template):
    tab = TABS[name]

    assert tab.url == reverse(url_name, kwargs=kwargs)
    assert tab.template_name == template


def test_the_tabs_are_overview_and_data():
    assert [tab.name for tab in TABS] == ["index", "data"]
    assert views.TabViewMixin.default_tab is TABS["index"]
