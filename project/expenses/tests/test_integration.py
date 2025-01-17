from time import sleep

import pytest
import time_machine
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ...accounts.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Expenses(Browser):
    def _fill_selects(self):
        self.browser.get(f"{self.live_server_url}/expenses/")

        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        sleep(0.5)

        # select expense type
        elem = Select(self.browser.find_element(By.ID, "id_expense_type"))
        elem.select_by_value(f"{t.id}")

        # select expense name
        elem = Select(self.browser.find_element(By.ID, "id_expense_name"))
        elem.select_by_value(f"{n.id}")

        # select Account
        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{a.id}")

    def test_add_one_expense_and_close_modal_form(self):
        self._fill_selects()

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()

        # click 'Save and Close' button
        self.browser.find_element(By.ID, "_close").click()

        # wait while form is closing
        sleep(0.5)

        page = self.browser.page_source
        assert "Account1" in page
        assert "Expense Name" in page
        assert "123.45" in page

    def test_add_one_expense_and_hit_enter_key(self):
        self._fill_selects()

        price = self.browser.find_element(By.ID, "id_total_sum")
        price.send_keys("123.45")
        price.send_keys(Keys.RETURN)

        qty = self.browser.find_element(By.ID, "id_quantity")
        qty.send_keys(Keys.RETURN)
        sleep(0.25)

        # click Esc button
        ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()

        # wait while form is closing
        sleep(0.25)

        page = self.browser.page_source
        assert "Expense Type" in page
        assert "Expense Name" in page
        assert "123.45" in page

    def test_add_one_expense_check_quantity_and_price_fields_values(self):
        self._fill_selects()

        price = self.browser.find_element(By.ID, "id_total_sum")
        price.send_keys("123.45")
        price.send_keys(Keys.RETURN)

        qty = self.browser.find_element(By.ID, "id_quantity")
        qty.clear()
        qty.send_keys("66")
        qty.send_keys(Keys.ENTER)

        sleep(0.5)

        assert (
            self.browser.find_element(By.ID, "id_price").get_attribute("value") == "0.0"
        )
        assert (
            self.browser.find_element(By.ID, "id_quantity").get_attribute("value")
            == "1"
        )

    def test_exclude_expense_reset_after_submit(self):
        self._fill_selects()

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()

        self.browser.find_element(By.ID, "id_exception").click()

        # click 'Save and Close' button
        self.browser.find_element(By.ID, "_new").click()

        # wait while form is closing
        sleep(0.5)

        assert not self.browser.find_element(By.ID, "id_exception").is_selected()

    @time_machine.travel("1999-12-01 10:11:12")
    def test_add_two_expenses(self):
        self.browser.get(f"{self.live_server_url}/expenses/")

        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()
        t1 = ExpenseTypeFactory(title="Expense Type 1")
        n1 = ExpenseNameFactory(title="Expense Name 1", parent=t1)

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        sleep(0.5)

        # select expense type
        elem = Select(self.browser.find_element(By.ID, "id_expense_type"))
        elem.select_by_value(f"{t.id}")

        # select expense name
        elem = Select(self.browser.find_element(By.ID, "id_expense_name"))
        elem.select_by_value(f"{n.id}")

        # select Account
        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{a.id}")

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()

        # # click Insert button
        self.browser.find_element(By.ID, "_new").click()
        sleep(1)

        # ----------------------------- Second expense
        # select ExpenseType
        elem = Select(self.browser.find_element(By.ID, "id_expense_type"))
        elem.select_by_value(f"{t1.id}")

        # select ExpenseName
        elem = Select(self.browser.find_element(By.ID, "id_expense_name"))
        elem.select_by_value(f"{n1.id}")

        # select Account
        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{a.id}")

        self.browser.find_element(By.ID, "id_total_sum").send_keys("65.78")
        self.browser.find_element(By.ID, "add_price").click()

        # click Insert button
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)

        page = self.browser.page_source

        assert t.title in page
        assert n.title in page
        assert "123.45" in page

        assert t1.title in page
        assert n1.title in page
        assert "65.78" in page

    @time_machine.travel("1999-1-1 10:11:12")
    def test_empty_required_fields(self):
        self.browser.get(f"{self.live_server_url}/expenses/")

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        sleep(0.5)

        # click 'Save And Close' button
        self.browser.find_element(By.ID, "_close").click()
        sleep(0.5)
        e1 = self.browser.find_element(By.ID, "error_1_id_expense_type")
        e2 = self.browser.find_element(By.ID, "error_1_id_expense_name")
        e3 = self.browser.find_element(By.ID, "error_1_id_price")

        assert e1.text == e2.text == "This field is required."
        assert e3.text == "Ensure this value is greater than or equal to 0.01."

    @time_machine.travel("1999-1-1 10:11:12")
    def test_search(self):
        self.browser.get(f"{self.live_server_url}/expenses")

        ExpenseFactory(remark="xxxx")
        ExpenseFactory(remark="yyyy")
        ExpenseFactory(remark="zzzz")

        search = self.browser.find_element(by=By.ID, value="id_search")
        search.send_keys("xxxx")

        search.send_keys(Keys.RETURN)

        sleep(0.1)

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 1  # head row + find row

        cells = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr[1]/td")
        assert cells[5].text == "xxxx"
