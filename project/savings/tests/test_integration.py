import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from .factories import SavingTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Savings(Browser):
    def test_a_saving_saved_lands_in_the_table_and_empties_the_form(self):
        account = AccountFactory()
        fund = SavingTypeFactory(title="Zeta fund")

        self.open("/savings/")
        self.browser.find_element(By.CSS_SELECTOR, ".quick-add__pill").click()
        self.wait_until_idle()

        Select(self.browser.find_element(By.ID, "id_saving_type")).select_by_value(
            f"{fund.id}"
        )
        Select(self.browser.find_element(By.ID, "id_account")).select_by_value(
            f"{account.id}"
        )
        self.browser.find_element(By.ID, "id_price").send_keys("100")
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        assert self.browser.find_elements(
            By.XPATH, '//*[@id="tab_content"]//td[normalize-space()="Zeta fund"]'
        )
        # sum and fee fields should be empty, not 0.0 or 0
        assert self.browser.find_element(By.ID, "id_price").get_attribute("value") == ""
        assert self.browser.find_element(By.ID, "id_fee").get_attribute("value") == ""
