from time import sleep

import pytest
from selenium.webdriver.common.by import By

from ...core.tests.test_integration_browser import Browser
from ..factories import CountTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Incomes(Browser):
    def test_create(self):
        self.browser.get(f"{self.live_server_url}/counts/")

        self.browser.find_element(By.CSS_SELECTOR , ".btn-success").click()
        sleep(0.5)

        self.browser.find_element(By.ID, "id_title").send_keys("-AAA-")
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)

        page = self.browser.page_source
        assert '-AAA-' in page


    def test_delete(self):
        CountTypeFactory(title='-AAA-')

        self.browser.get(f"{self.live_server_url}/counts/")

        self.browser.find_element(By.CSS_SELECTOR, ".btn.dropdown-toggle.dropdown-toggle-split.nav-link.active").click()
        self.browser.find_element(By.XPATH, "//button[text()='Add count type']").click()
        sleep(0.5)

        self.browser.find_element(By.ID, "id_title").send_keys("-XXX-")
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)

        self.browser.find_element(By.CSS_SELECTOR, ".btn-danger").click()
        sleep(0.5)
        # delete button in delete form
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)

        page = self.browser.page_source
        assert '-AAA-' in page
