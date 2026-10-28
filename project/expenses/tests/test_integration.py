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
from .receipts.pdfs import FIXTURES

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
        self.assert_overview_chart_redraws(
            reverse("expenses:index"), "chart-months-container"
        )

    def index_url(self):
        return f"{self.live_server_url}{reverse('expenses:index')}"

    def data_url(self):
        month = date.today().month
        return f"{self.live_server_url}{reverse('expenses:tab_data', args=[month])}"

    def _open_add_expense(self, url):
        self.browser.get(url)
        self.wait_until_idle()
        self._press_add_expense()

    def _press_add_expense(self):
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

        self._press_escape()
        self.wait_until_idle()

        [expense] = self.listed_rows(COLUMNS)
        assert (expense["type"], expense["name"], expense["price"]) == (
            "Expense Type",
            "Expense Name",
            "123,45",
        )

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
            for expense in self.listed_rows(COLUMNS)
        )
        assert expenses == [
            ("Expense Type", "Expense Name", "123,45", "Account1"),
            ("Expense Type 1", "Expense Name 1", "65,78", "Account1"),
        ]

    @time_machine.travel("1999-1-1 10:11:12")
    def test_empty_required_fields(self):
        self._open_add_expense(self.index_url())

        self.browser.find_element(By.ID, "_close").click()
        self.wait_until_idle()

        feedback = "div[@class='invalid-feedback']"
        errors = {
            field: self.browser.find_element(
                By.XPATH,
                f"//*[@id='id_{field}']/ancestor::div[{feedback}][1]/{feedback}",
            ).text
            for field in ("expense_type", "expense_name", "price")
        }
        assert errors == {
            "expense_type": "Šis laukas yra privalomas.",
            "expense_name": "Šis laukas yra privalomas.",
            "price": "Įsitikinkite, kad reikšmė yra didesnė arba lygi 0.01.",
        }

    @time_machine.travel("1999-1-1 10:11:12")
    def test_the_date_picker_names_its_month_in_the_journals_language(self):
        for lang, month in [("lt", "sausis"), ("en", "January")]:
            with self.subTest(lang=lang):
                Journal.objects.update(lang=lang)
                self._open_add_expense(self.index_url())

                self.browser.find_element(By.ID, "id_date").click()

                picker = self.browser.find_element(
                    By.CSS_SELECTOR, ".litepicker .month-item-name"
                )
                assert picker.text == month

    @time_machine.travel("1999-1-1 10:11:12")
    def test_a_reopened_form_leaves_one_date_picker(self):
        self._open_add_expense(self.index_url())
        self.browser.find_element(By.CSS_SELECTOR, "#mainModal .modal-close").click()
        self._press_add_expense()

        self.browser.find_element(By.ID, "id_date").click()

        pickers = self.browser.find_elements(By.CSS_SELECTOR, ".litepicker")
        assert [
            p.find_element(By.CLASS_NAME, "month-item-name").text for p in pickers
        ] == ["sausis"]

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
        assert [expense["price"] for expense in self.listed_rows(COLUMNS)] == ["6,48"]

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

        assert [expense["remark"] for expense in self.listed_rows(COLUMNS)] == ["xxxx"]

    def _modal_container(self):
        return self.browser.find_element(By.ID, "mainModalContainer")

    def _modal_display(self):
        return self._modal_container().value_of_css_property("display")

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
        assert len(self.listed_rows(COLUMNS)) == 1

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
    def test_modal_closes_by_backdrop_button_escape_and_save(self):
        ExpenseFactory()
        closers = {
            "backdrop": self._click_the_backdrop,
            "button": self._press_the_close_button,
            "escape": self._press_escape,
            "save": self._submit_and_close_update_form,
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
        self.browser.find_element(By.ID, "id_exception").click()
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        values = {
            field: self.browser.find_element(By.ID, f"id_{field}").get_attribute(
                "value"
            )
            for field in ("price", "quantity", "remark")
        }
        assert values == {"price": "0.0", "quantity": "1", "remark": ""}
        assert not self.browser.find_element(By.ID, "id_exception").is_selected()
        price = self.browser.find_element(By.ID, "id_price")
        assert price.value_of_css_property("font-weight") == "700"
        for marker in (".invalid-feedback", ".is-invalid"):
            assert not self.browser.find_elements(
                By.CSS_SELECTOR, f"#mainModal {marker}"
            )

    @time_machine.travel("1999-1-1 10:11:12")
    def test_a_receipt_image_opens_in_the_image_modal(self):
        ExpenseFactory(attachment="receipt.jpg")
        # from Apžvalga, so imgModal's container arrives with the Duomenys swap
        self.browser.get(self.index_url())
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

    def _type_price(self, line, value):
        price = self.browser.find_element(By.NAME, f"form-{line}-price")
        price.send_keys(Keys.CONTROL, "a")
        price.send_keys(value)

    def _review_totals(self):
        lines_total = self.browser.find_element(By.CSS_SELECTOR, "#review tfoot span")
        notice = self.browser.find_element(
            By.XPATH, "//form[@id='review']/p[contains(., 'Sumos nesutampa')]"
        )
        return lines_total.text, notice.is_displayed()

    def test_the_import_review_lines_total_follows_a_typed_price(self):
        AccountFactory()
        self.browser.get(f"{self.live_server_url}{reverse('expenses:import')}")
        self.wait_until_idle()
        self.browser.find_element(By.ID, "id_pdf").send_keys(
            str(FIXTURES / "barbora.pdf")
        )
        self.browser.find_element(By.CSS_SELECTOR, "#upload button").click()
        self.wait_until_idle()

        # line 2 reads 2,80 of the receipt's 71,35
        self._type_price(1, "12,80")
        assert self._review_totals() == ("81,35", True)

        self._type_price(1, "2,80")
        assert self._review_totals() == ("71,35", False)
