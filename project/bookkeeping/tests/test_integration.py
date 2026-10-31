import pytest
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeFactory
from ...pensions.tests.factories import PensionFactory, PensionTypeFactory
from ...savings.tests.factories import SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class BookkeepingIndex(TestCase, Browser):
    def test_index_queries_do_not_grow_with_rows(self):
        self._add_rows(range(2))
        queries_at_two = self._index_queries()
        self._add_rows(range(2, 6))

        assert self._index_queries() == queries_at_two

    def test_a_pressed_nav_act_closes_its_menu(self):
        url = reverse("incomes:new")
        act = self.browser.find_element(
            By.CSS_SELECTOR, f"#main-nav button[hx-get='{url}']"
        )
        menu = act.find_element(By.XPATH, "./ancestor::div[@class='dropdown']")
        menu.find_element(By.CSS_SELECTOR, ".dropdown__btn").click()
        WebDriverWait(self.browser, timeout=2).until(lambda _: act.is_displayed())
        act.click()
        self.wait_until_idle()

        assert self.browser.find_elements(By.CSS_SELECTOR, "#mainModal .modal-form")
        assert not self.browser.execute_script(
            "return arguments[0].matches(':focus-within')", menu
        )

    def test_reload_redraws_both_index_charts(self):
        roots = (
            "#chart-balance-container .highcharts-root,"
            " #chart-expenses-container .highcharts-root"
        )
        # the reload settles the tables too: each chart draws on its own data's swap only
        drawn_on_load = self.browser.execute_script(
            f"const drawn = document.querySelectorAll('{roots}');"
            " drawn.forEach(root => root.dataset.drawnOnLoad = '');"
            " window.draws = 0;"
            " Highcharts.addEvent(Highcharts.Chart, 'load', () => window.draws++);"
            " htmx.trigger(document.body, 'reload');"
            " return drawn.length;"
        )
        self.wait_until_idle()

        reload = self.browser.execute_script(
            f"return {{roots: [...document.querySelectorAll('{roots}')]"
            ".map(root => 'drawnOnLoad' in root.dataset ? 'stale' : 'redrawn'),"
            " draws: window.draws};"
        )
        assert (drawn_on_load, reload) == (
            2,
            {"roots": ["redrawn", "redrawn"], "draws": 2},
        )

    def test_insert_clears_each_worth_row(self):
        AccountFactory(title="Account 0")
        AccountFactory(title="Account 1")
        self.browser.get(self.live_server_url)
        self.wait_until_idle()

        url = reverse("bookkeeping:accounts_worth_new")
        self.browser.find_element(By.CSS_SELECTOR, f"button[hx-get='{url}']").click()
        self.wait_until_idle()
        price_ids = ["id_form-0-price", "id_form-1-price"]
        for price_id in price_ids:
            self.browser.find_element(By.ID, price_id).send_keys("5")
        self.browser.find_element(By.ID, "_new").click()
        self.wait_until_idle()

        values = [
            self.browser.find_element(By.ID, price_id).get_attribute("value")
            for price_id in price_ids
        ]
        assert values == ["", ""]

    def test_month_page_fits_a_phone_and_its_table_scrolls_in_its_box(self):
        # a column per type: ten make the table wider than the phone
        for i in range(10):
            ExpenseTypeFactory(title=f"Expense Type {i}")
        self.open_at(reverse("bookkeeping:month"), 360)

        overflow = self.browser.execute_script(
            "const page = document.documentElement;"
            " const box = document.getElementById('month-content');"
            " return {width: innerWidth,"
            " page_overflow: page.scrollWidth - page.clientWidth,"
            " table_scrolls: box.scrollWidth > box.clientWidth};"
        )
        assert overflow == {"width": 360, "page_overflow": 0, "table_scrolls": True}

    def test_month_table_rules_run_from_the_band_to_the_foot(self):
        IncomeFactory()
        self.open_at(reverse("bookkeeping:detailed"), 1280)

        # per row, each cell with a left rule, by position from 1, and its colour;
        # no width: a scaled display snaps 1px to a device pixel (0.8px at 125%)
        ruled = self.browser.execute_script(
            "return [...document.querySelectorAll('.month-table tr')].map(tr =>"
            " [...tr.children].flatMap((c, i) => {"
            " const s = getComputedStyle(c);"
            " return s.borderLeftStyle === 'solid' ? [[i + 1, s.borderLeftColor]] : [];"
            " }));"
        )
        hair, soft = "rgb(207, 214, 218)", "rgb(225, 230, 232)"
        body = [[5, soft], [8, soft], [11, soft], [14, hair]]
        assert ruled == [
            [[3, hair], [4, hair], [5, hair], [6, hair]],
            [[5, hair], [8, hair], [11, hair], [14, hair]],
            body,
            body,
        ]

    def _add_rows(self, numbers):
        # A type's save re-syncs its balances, so the rows come from records.
        for i in numbers:
            IncomeFactory(account=AccountFactory(title=f"Account {i}"))
            SavingFactory(saving_type=SavingTypeFactory(title=f"Fund {i}"))
            PensionFactory(pension_type=PensionTypeFactory(title=f"Pension {i}"))

    def _index_queries(self):
        with CaptureQueriesContext(connection) as queries:
            self.browser.get(self.live_server_url)
            self.wait_until_idle()
        return len(queries)
