import pytest

from ...core.tests.test_integration_browser import Browser

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Books(Browser):
    def test_overview_chart_draws_on_load_and_after_a_tab_swap(self):
        self.assert_overview_chart_redraws("/books/", "chart-finished-container")
