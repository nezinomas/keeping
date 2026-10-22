import pytest
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class BookkeepingIndex(TestCase, Browser):
    def test_index(self):
        with self.assertNumQueries(32):
            self.browser.get(f"{self.live_server_url}")
            self.wait_until_idle()

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
