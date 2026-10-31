import pytest
import time_machine
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ...core.tests.test_integration_browser import Browser
from .factories import IncomeFactory

pytestmark = pytest.mark.django_db

COLUMNS = ("date", "type", "account", "remark", "amount")


@pytest.mark.webtest
class Incomes(Browser):
    def test_overview_chart_draws_on_load_and_after_a_tab_swap(self):
        self.assert_overview_chart_redraws(
            reverse("incomes:index"), "chart-months-container"
        )

    @time_machine.travel("1999-1-1")
    def test_search(self):
        IncomeFactory(remark="xxxx")
        IncomeFactory(remark="yyyy")
        IncomeFactory(remark="zzzz")

        self.browser.get(f"{self.live_server_url}{reverse('incomes:tab_data')}")
        self.wait_until_idle()

        assert sorted(income["remark"] for income in self.listed_rows(COLUMNS)) == [
            "xxxx",
            "yyyy",
            "zzzz",
        ]

        search = self.browser.find_element(by=By.ID, value="id_search")
        search.send_keys("xxxx")
        search.send_keys(Keys.RETURN)
        self.wait_until_idle()

        assert [income["remark"] for income in self.listed_rows(COLUMNS)] == ["xxxx"]
