import tempfile

import pytest
from django.test import override_settings
from selenium.webdriver.common.by import By

from ...core.tests.test_integration_browser import Browser
from .factories import CountTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class CountsIntegrationTests(Browser):
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_create(self):
        self.browser.get(f"{self.live_server_url}/counts/")
        self.wait_until_idle()

        self.browser.find_element(By.CSS_SELECTOR, ".button-secondary").click()
        self.wait_until_idle()

        self.browser.find_element(By.ID, "id_title").send_keys("-AAA-")
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        page = self.browser.page_source
        assert "-AAA-" in page

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete(self):
        CountTypeFactory(title="-AAA-")

        self.browser.get(f"{self.live_server_url}/counts/")
        self.wait_until_idle()

        # the counter menu opens on focus, so the pill is clicked to open it
        self.browser.find_element(
            By.CSS_SELECTOR, ".quick-add__bar .dropdown__btn"
        ).click()
        self.wait_until_idle()

        self.browser.find_element(
            By.XPATH,
            "//div[@class='quick-add__bar']//a[contains(@hx-get,'/counts/type/new/')]",
        ).click()
        self.wait_until_idle()

        self.browser.find_element(By.ID, "id_title").send_keys("-XXX-")
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        self.browser.find_element(
            By.CSS_SELECTOR, ".quick-add__bar .dropdown__btn"
        ).click()
        self.wait_until_idle()

        self.browser.find_element(
            By.XPATH,
            "//div[@class='quick-add__bar']//a[contains(@hx-get,'/counts/type/delete/')]",
        ).click()
        self.wait_until_idle()

        # the title has to be typed before the delete button is anything but grey
        self.browser.find_element(By.ID, "delete-confirm").send_keys("-XXX-")
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        page = self.browser.page_source
        assert "-AAA-" in page
        assert "-XXX-" not in page
