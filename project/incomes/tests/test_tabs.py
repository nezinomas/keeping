import pytest
from django.urls import reverse

from .. import views
from ..tabs import TABS


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_derives_its_url_and_template(tab):
    assert tab.url == reverse(f"incomes:tab_{tab.name}")
    assert tab.template_name == f"incomes/tab_{tab.name}.html"


def test_the_tabs_are_overview_data_and_types():
    assert [tab.name for tab in TABS] == ["index", "data", "types"]
    assert views.TabViewMixin.default_tab is TABS["index"]
