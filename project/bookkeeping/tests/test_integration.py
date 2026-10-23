import pytest
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ...incomes.tests.factories import IncomeFactory
from ...pensions.tests.factories import PensionFactory, PensionTypeFactory
from ...savings.tests.factories import SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class BookkeepingIndex(TestCase, Browser):
    def test_index_queries_do_not_grow_with_rows(self):
        self._add_rows(range(2))
        queries_at_two = self._index_queries()
        self._add_rows(range(2, 6))

        assert self._index_queries() == queries_at_two

    def test_a_pressed_nav_act_closes_its_menu(self):
        self.browser.get(f"{self.live_server_url}")
        self.wait_until_idle()

        act = self.browser.find_element(
            By.CSS_SELECTOR, "#main-nav button[hx-get='/incomes/new/']"
        )
        menu = act.find_element(By.XPATH, "./ancestor::div[@class='dropdown']")
        menu.find_element(By.CSS_SELECTOR, ".dropdown__btn").click()
        WebDriverWait(self.browser, 2).until(lambda _: act.is_displayed())
        act.click()
        self.wait_until_idle()

        assert self.browser.find_elements(By.CSS_SELECTOR, "#mainModal .modal-form")
        assert not self.browser.execute_script(
            "return arguments[0].matches(':focus-within')", menu
        )

    def test_insert_clears_each_worth_row(self):
        AccountFactory()
        self.browser.get(f"{self.live_server_url}")
        self.wait_until_idle()

        url = reverse("bookkeeping:accounts_worth_new")
        self.browser.find_element(By.CSS_SELECTOR, f"button[hx-get='{url}']").click()
        self.wait_until_idle()
        self.browser.find_element(By.ID, "id_form-0-price").send_keys("5")
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        price = self.browser.find_element(By.ID, "id_form-0-price")
        assert price.get_attribute("value") == ""

    def _add_rows(self, numbers):
        # A type's save re-syncs its balances, so the rows come from records.
        for i in numbers:
            IncomeFactory(account=AccountFactory(title=f"Account {i}"))
            SavingFactory(saving_type=SavingTypeFactory(title=f"Fund {i}"))
            PensionFactory(pension_type=PensionTypeFactory(title=f"Pension {i}"))

    def _index_queries(self):
        with CaptureQueriesContext(connection) as queries:
            self.browser.get(self.live_server_url)
            self.wait_until_idle()
        return len(queries)
