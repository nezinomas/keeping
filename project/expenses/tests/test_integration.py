import pytest
import time_machine
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Expenses(Browser):
    def _fill_selects(self):
        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()

        self.browser.get(f"{self.live_server_url}/expenses/")
        self.wait_until_idle()

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        self.wait_until_idle()

        # select expense type
        elem = Select(self.browser.find_element(By.ID, "id_expense_type"))
        elem.select_by_value(f"{t.id}")

        # select expense name
        elem = Select(self.browser.find_element(By.ID, "id_expense_name"))
        elem.select_by_value(f"{n.id}")

        # select Account
        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{a.id}")

    def _open_update_form(self):
        self.browser.get(f"{self.live_server_url}/expenses/")
        self.wait_until_idle()

        self.browser.find_element(By.CSS_SELECTOR, "a.edit").click()
        self.wait_until_idle()

    def _submit_and_close_update_form(self):
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

    def test_add_one_expense_and_close_modal_form(self):
        self._fill_selects()

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()

        # click 'Save and Close' button
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        page = self.browser.page_source
        assert "Account1" in page
        assert "Expense Name" in page
        assert "123,45" in page

    def test_add_one_expense_and_hit_enter_key(self):
        self._fill_selects()

        price = self.browser.find_element(By.ID, "id_total_sum")
        price.send_keys("123.45")
        price.send_keys(Keys.RETURN)

        qty = self.browser.find_element(By.ID, "id_quantity")
        qty.send_keys(Keys.RETURN)
        self.wait_until_idle()

        # click Esc button
        ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.wait_until_idle()

        page = self.browser.page_source
        assert "Expense Type" in page
        assert "Expense Name" in page
        assert "123,45" in page

    def test_add_one_expense_check_quantity_and_price_fields_values(self):
        self._fill_selects()

        price = self.browser.find_element(By.ID, "id_total_sum")
        price.send_keys("123.45")
        price.send_keys(Keys.RETURN)

        qty = self.browser.find_element(By.ID, "id_quantity")
        qty.clear()
        qty.send_keys("66")
        qty.send_keys(Keys.ENTER)
        self.wait_until_idle()

        assert (
            self.browser.find_element(By.ID, "id_price").get_attribute("value") == "0.0"
        )
        assert (
            self.browser.find_element(By.ID, "id_price").value_of_css_property(
                "font-weight"
            )
            == "700"
            or self.browser.find_element(By.ID, "id_price").value_of_css_property(
                "font-weight"
            )
            == "bold"
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
        self.wait_until_idle()

        assert not self.browser.find_element(By.ID, "id_exception").is_selected()

    @time_machine.travel("1999-12-01 10:11:12")
    def test_add_two_expenses(self):
        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()
        t1 = ExpenseTypeFactory(title="Expense Type 1")
        n1 = ExpenseNameFactory(title="Expense Name 1", parent=t1)

        self.browser.get(f"{self.live_server_url}/expenses/")
        self.wait_until_idle()

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        self.wait_until_idle()

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
        self.wait_until_idle()

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
        self.wait_until_idle()

        page = self.browser.page_source

        assert t.title in page
        assert n.title in page
        assert "123,45" in page

        assert t1.title in page
        assert n1.title in page
        assert "65,78" in page

    @time_machine.travel("1999-1-1 10:11:12")
    def test_empty_required_fields(self):
        self.browser.get(f"{self.live_server_url}/expenses/")
        self.wait_until_idle()

        # click Add Expenses button
        self.browser.find_element(
            By.XPATH, '//button[normalize-space()="Expenses"]'
        ).click()
        self.wait_until_idle()

        # click 'Save And Close' button
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        def get_error(field_id):
            xpath = f"//*[@id='{field_id}']/ancestor::div[div[contains(@class, 'invalid-feedback')]][1]//div[contains(@class, 'invalid-feedback')]"
            return self.browser.find_element(By.XPATH, xpath)

        # Grab the errors
        e1 = get_error("id_expense_type")
        e2 = get_error("id_expense_name")
        e3 = get_error("id_price")

        # Assertions (using 'in' is safer than '==' to avoid trailing whitespace issues)
        assert "This field is required." in e1.text
        assert "This field is required." in e2.text
        assert "Ensure this value is greater than or equal to 0.01." in e3.text

    @time_machine.travel("1999-1-1 10:11:12")
    def test_update_one_expense_price(self):
        ExpenseFactory()

        self._open_update_form()

        assert (
            self.browser.find_element(By.ID, "id_price").get_attribute("value")
            == "1.12"
        )

        self.browser.find_element(By.ID, "id_total_sum").send_keys("5.36")
        self.browser.find_element(By.ID, "add_price").click()

        self._submit_and_close_update_form()

        page = self.browser.page_source
        assert "6,48" in page
        assert "invalid-feedback" not in page

    @time_machine.travel("1999-1-1 10:11:12")
    def test_update_one_expense_account_keeps_the_price(self):
        account = AccountFactory(title="Account2")
        ExpenseFactory(price=648)

        self._open_update_form()

        assert (
            self.browser.find_element(By.ID, "id_price").get_attribute("value")
            == "6.48"
        )

        elem = Select(self.browser.find_element(By.ID, "id_account"))
        elem.select_by_value(f"{account.id}")

        self._submit_and_close_update_form()

        page = self.browser.page_source
        assert "6,48" in page
        assert "invalid-feedback" not in page

    @time_machine.travel("1999-1-1 10:11:12")
    def test_search(self):
        ExpenseFactory(remark="xxxx")
        ExpenseFactory(remark="yyyy")
        ExpenseFactory(remark="zzzz")

        self.browser.get(f"{self.live_server_url}/expenses")
        self.wait_until_idle()

        search = self.browser.find_element(by=By.ID, value="id_search")
        search.send_keys("xxxx")

        search.send_keys(Keys.RETURN)
        self.wait_until_idle()

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 1  # head row + find row

        cells = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr[1]/td")
        assert cells[5].text == "xxxx"
