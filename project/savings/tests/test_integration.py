from time import sleep

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from .factories import SavingTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Savings(Browser):
    def test_add_savings_and_check_fields_not_zero(self):
        self.browser.get(f"{self.live_server_url}/savings/")

        a = AccountFactory()
        t = SavingTypeFactory()

        # click Add Savings button (translated as 'Record' or 'Įrašas')
        buttons = self.browser.find_elements(By.TAG_NAME, "button")
        record_btn = None
        for b in buttons:
            if "Record" in b.text or "Įrašas" in b.text:
                record_btn = b
                break

        if record_btn:
            record_btn.click()

        sleep(0.5)

        # select saving type
        elem = Select(self.browser.find_element(By.ID, "id_saving_type"))
        elem.select_by_value(f"{t.id}")

        # select Account
        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{a.id}")

        # fill sum
        self.browser.find_element(By.ID, "id_price").send_keys("100")

        # click 'Insert' button
        self.browser.find_element(By.ID, "_new").click()
        sleep(0.5)

        # sum and fee fields should be empty, not 0.0 or 0
        assert self.browser.find_element(By.ID, "id_price").get_attribute("value") == ""
        assert self.browser.find_element(By.ID, "id_fee").get_attribute("value") == ""
