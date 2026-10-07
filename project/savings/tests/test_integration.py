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
        a = AccountFactory()
        t = SavingTypeFactory()

        self.browser.get(f"{self.live_server_url}/savings/")
        self.wait_until_idle()

        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Įrašą"]'
        ).click()

        self.wait_until_idle()

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
        self.wait_until_idle()

        # sum and fee fields should be empty, not 0.0 or 0
        assert self.browser.find_element(By.ID, "id_price").get_attribute("value") == ""
        assert self.browser.find_element(By.ID, "id_fee").get_attribute("value") == ""
