from time import sleep

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from ...core.tests.test_integration_browser import Browser
from ..factories import CountTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class CountsIntegrationTests(Browser):
    def test_create(self):
        self.browser.get(f"{self.live_server_url}/counts/")

        self.browser.find_element(By.CSS_SELECTOR , ".button-success").click()
        sleep(0.5)

        self.browser.find_element(By.ID, "id_title").send_keys("-AAA-")
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)

        page = self.browser.page_source
        assert '-AAA-' in page


    def test_delete(self):
        CountTypeFactory(title='-AAA-')

        self.browser.get(f"{self.live_server_url}/counts/")

        # hover over dropdown menu
        self.browser.find_element(By.XPATH, '//a[contains(@href,"/counts/")]/following::button[1]').click()
        sleep(0.25)

        # click on add count type
        self.browser.find_element(By.XPATH, "//a[text()='Add count type']").click()
        sleep(0.25)

        # fill form
        self.browser.find_element(By.ID, "id_title").send_keys("-XXX-")
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.25)

        # fink delete button and click it
        self.browser.find_element(By.CSS_SELECTOR, ".button-danger").click()
        sleep(0.25)

        # delete button in delete form
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.25)

        page = self.browser.page_source
        assert '-AAA-' in page
