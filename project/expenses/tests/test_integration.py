from datetime import date

import pytest
import time_machine
from django.urls import reverse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ...journals.models import Journal
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db

# expense_list.html's cells, up to the edit and delete links
COLUMNS = (
    "date",
    "type",
    "name",
    "quantity",
    "price",
    "remark",
    "attachment",
    "account",
)


@pytest.mark.webtest
class Expenses(Browser):
    def test_overview_chart_draws_on_load_and_after_a_tab_swap(self):
        self.assert_overview_chart_redraws("/expenses/", "chart-months-container")

    def data_url(self):
        month = date.today().month
        return f"{self.live_server_url}{reverse('expenses:tab_data', args=[month])}"

    def _open_add_expense(self, url):
        self.browser.get(url)
        self.wait_until_idle()
        self.browser.find_element(
            By.CSS_SELECTOR, f'.quick-add__pill[hx-get="{reverse("expenses:new")}"]'
        ).click()
        self.wait_until_idle()

    def _select(self, expense_type, expense_name, account):
        for field, option in [
            ("expense_type", expense_type),
            ("expense_name", expense_name),
            ("account", account),
        ]:
            Select(self.browser.find_element(By.ID, f"id_{field}")).select_by_value(
                f"{option.pk}"
            )

    def _fill_selects(self):
        account = AccountFactory()
        expense_type = ExpenseTypeFactory()
        expense_name = ExpenseNameFactory()

        self._open_add_expense(self.data_url())
        self._select(expense_type, expense_name, account)

    def _listed_expenses(self):
        return [
            dict(zip(COLUMNS, [td.text for td in tr.find_elements(By.TAG_NAME, "td")]))
            for tr in self.browser.find_elements(By.CSS_SELECTOR, "#data tbody tr")
        ]

    def _open_update_form(self):
        self.browser.get(self.data_url())
        self.wait_until_idle()

        self.browser.find_element(By.CSS_SELECTOR, "a.edit").click()
        self.wait_until_idle()

    def _submit_and_close_update_form(self):
        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

    def test_add_one_expense_and_hit_enter_key(self):
        self._fill_selects()

        price = self.browser.find_element(By.ID, "id_total_sum")
        price.send_keys("123.45")
        price.send_keys(Keys.RETURN)

        qty = self.browser.find_element(By.ID, "id_quantity")
        qty.send_keys(Keys.RETURN)
        self.wait_until_idle()

        ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.wait_until_idle()

        [expense] = self._listed_expenses()
        assert (expense["type"], expense["name"], expense["price"]) == (
            "Expense Type",
            "Expense Name",
            "123,45",
        )

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

        price = self.browser.find_element(By.ID, "id_price")
        assert price.get_attribute("value") == "0.0"
        assert price.value_of_css_property("font-weight") == "700"
        assert (
            self.browser.find_element(By.ID, "id_quantity").get_attribute("value")
            == "1"
        )

    def test_exclude_expense_reset_after_submit(self):
        self._fill_selects()

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()

        self.browser.find_element(By.ID, "id_exception").click()

        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        assert not self.browser.find_element(By.ID, "id_exception").is_selected()

    @time_machine.travel("1999-12-01 10:11:12")
    def test_add_two_expenses(self):
        account = AccountFactory()
        first = ExpenseNameFactory()
        second = ExpenseNameFactory(
            title="Expense Name 1", parent=ExpenseTypeFactory(title="Expense Type 1")
        )

        self._open_add_expense(self.data_url())
        for name, total, submit in [
            (first, "123.45", "_new"),
            (second, "65.78", "_close"),
        ]:
            self._select(name.parent, name, account)
            self.browser.find_element(By.ID, "id_total_sum").send_keys(total)
            self.browser.find_element(By.ID, "add_price").click()
            self.browser.find_element(By.ID, submit).click()
            self.wait_until_idle()

        expenses = sorted(
            (expense["type"], expense["name"], expense["price"], expense["account"])
            for expense in self._listed_expenses()
        )
        assert expenses == [
            ("Expense Type", "Expense Name", "123,45", "Account1"),
            ("Expense Type 1", "Expense Name 1", "65,78", "Account1"),
        ]

    @time_machine.travel("1999-1-1 10:11:12")
    def test_empty_required_fields(self):
        self._open_add_expense(f"{self.live_server_url}/expenses/")

        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        def get_error(field_id):
            xpath = f"//*[@id='{field_id}']/ancestor::div[div[contains(@class, 'invalid-feedback')]][1]//div[contains(@class, 'invalid-feedback')]"
            return self.browser.find_element(By.XPATH, xpath)

        e1 = get_error("id_expense_type")
        e2 = get_error("id_expense_name")
        e3 = get_error("id_price")

        assert "Šis laukas yra privalomas." in e1.text
        assert "Šis laukas yra privalomas." in e2.text
        assert "Įsitikinkite, kad reikšmė yra didesnė arba lygi 0.01." in e3.text

    @time_machine.travel("1999-1-1 10:11:12")
    def test_the_date_picker_names_its_month_in_the_journals_language(self):
        for lang, month in [("lt", "sausis"), ("en", "January")]:
            with self.subTest(lang=lang):
                Journal.objects.update(lang=lang)
                self._open_add_expense(f"{self.live_server_url}/expenses/")

                self.browser.find_element(By.ID, "id_date").click()

                picker = self.browser.find_element(
                    By.CSS_SELECTOR, ".litepicker .month-item-name"
                )
                assert picker.text == month

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

        assert not self.browser.find_elements(
            By.CSS_SELECTOR, "#mainModal .invalid-feedback"
        )
        assert [expense["price"] for expense in self._listed_expenses()] == ["6,48"]

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

        assert not self.browser.find_elements(
            By.CSS_SELECTOR, "#mainModal .invalid-feedback"
        )
        assert [expense["price"] for expense in self._listed_expenses()] == ["6,48"]

    @time_machine.travel("1999-1-1 10:11:12")
    def test_search(self):
        ExpenseFactory(remark="xxxx")
        ExpenseFactory(remark="yyyy")
        ExpenseFactory(remark="zzzz")

        self.browser.get(self.data_url())
        self.wait_until_idle()

        search = self.browser.find_element(by=By.ID, value="id_search")
        search.send_keys("xxxx")

        search.send_keys(Keys.RETURN)
        self.wait_until_idle()

        assert [expense["remark"] for expense in self._listed_expenses()] == ["xxxx"]

    def _modal_container(self):
        return self.browser.find_element(By.ID, "mainModalContainer")

    def _modal_display(self):
        return self._modal_container().value_of_css_property("display")

    @time_machine.travel("1999-1-1 10:11:12")
    def test_modal_closes_after_update_and_close(self):
        ExpenseFactory()

        self._open_update_form()
        assert self._modal_display() == "block"

        self._submit_and_close_update_form()

        assert self._modal_display() == "none"

    @time_machine.travel("1999-1-1 10:11:12")
    def test_delete_closes_the_modal_and_refreshes_the_table(self):
        ExpenseFactory(remark="AAAA")
        ExpenseFactory(remark="BBBB")

        self.browser.get(self.data_url())
        self.wait_until_idle()

        self.browser.find_element(By.CSS_SELECTOR, ".delete-col a").click()
        self.wait_until_idle()
        assert self._modal_display() == "block"

        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        assert self._modal_display() == "none"
        assert len(self._listed_expenses()) == 1

    def _click_the_backdrop(self):
        container = self._modal_container()
        # the dialog covers the container's centre, so press near its corner
        x, y = 5 - container.size["width"] // 2, 5 - container.size["height"] // 2
        ActionChains(self.browser).move_to_element_with_offset(
            container, x, y
        ).click().perform()

    def _press_the_close_button(self):
        self.browser.find_element(By.CSS_SELECTOR, "#mainModal .modal-close").click()

    def _press_escape(self):
        ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()

    @time_machine.travel("1999-1-1 10:11:12")
    def test_modal_closes_by_backdrop_button_and_escape(self):
        ExpenseFactory()
        closers = {
            "backdrop": self._click_the_backdrop,
            "button": self._press_the_close_button,
            "escape": self._press_escape,
        }

        for name, close in closers.items():
            with self.subTest(name):
                self._open_update_form()
                assert self._modal_display() == "block"

                close()
                self.wait_until_idle()

                assert self._modal_display() == "none"
                assert not self.browser.find_elements(
                    By.CSS_SELECTOR, "#mainModal .modal-form"
                )

    def test_insert_clears_the_form_and_its_errors(self):
        self._fill_selects()
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()
        assert self.browser.find_elements(By.CSS_SELECTOR, "#mainModal .is-invalid")

        self.browser.find_element(By.ID, "id_total_sum").send_keys("123.45")
        self.browser.find_element(By.ID, "add_price").click()
        self.browser.find_element(By.ID, "id_remark").send_keys("AAAA")
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        values = {
            field: self.browser.find_element(By.ID, f"id_{field}").get_attribute(
                "value"
            )
            for field in ("price", "quantity", "remark")
        }
        assert values == {"price": "0.0", "quantity": "1", "remark": ""}
        for marker in (".invalid-feedback", ".is-invalid"):
            assert not self.browser.find_elements(
                By.CSS_SELECTOR, f"#mainModal {marker}"
            )

    @time_machine.travel("1999-1-1 10:11:12")
    def test_a_receipt_image_opens_in_the_image_modal(self):
        ExpenseFactory(attachment="receipt.jpg")
        # from Apžvalga, so imgModal's container arrives with the Duomenys swap
        self.browser.get(f"{self.live_server_url}/expenses/")
        self.wait_until_idle()
        self.browser.find_element(By.ID, "tab-data").click()
        self.wait_until_idle()

        # the second open is the second swap into the same modal
        for _ in range(2):
            self.browser.find_element(
                By.CSS_SELECTOR, 'button[hx-target="#imgModal"]'
            ).click()
            self.wait_until_idle()

            image = self.browser.find_element(By.CSS_SELECTOR, "#imgModal img")
            assert image.get_attribute("src").endswith("/receipt.jpg")

            self.browser.find_element(By.CSS_SELECTOR, "#imgModal .modal-close").click()
            self.wait_until_idle()

            assert not self.browser.find_element(
                By.ID, "imgModalContainer"
            ).is_displayed()
