import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from ...core.tests.test_integration_browser import Browser
from .factories import SavingCloseFactory, TransactionFactory

pytestmark = pytest.mark.django_db

ROWS_TALLER_THAN_THE_WINDOW = 30

# the minimized webtest Chrome may draw no frame, and without one no scroll event
# fires: the event is dispatched here, so the library's handler runs every time
HEAD_POSITION_AFTER_A_SCROLL_PAST_THE_TABLE_TOP = """
const done = arguments[arguments.length - 1];
const table = document.querySelector('.sticky-table');
window.scrollTo(0, table.getBoundingClientRect().top + window.scrollY + 1);
window.dispatchEvent(new Event('scroll'));
setTimeout(() => done(getComputedStyle(table.querySelector('thead')).position), 100);
"""


@pytest.mark.webtest
class Transactions(Browser):
    def open_transactions(self):
        self.open_at(reverse("transactions:tab_transactions"), 1280)

    def swap_to_sales_and_back(self):
        self.open_transactions()
        for tab in ("sales", "transactions"):
            self.browser.find_element(By.ID, f"tab-{tab}").click()
            self.wait_until_idle()

    def test_a_tab_pins_its_table_head_on_scroll(self):
        TransactionFactory.create_batch(ROWS_TALLER_THAN_THE_WINDOW)
        arrivals = {
            "opened_by_url": self.open_transactions,
            "swapped_back": self.swap_to_sales_and_back,
        }

        for arrival, arrive in arrivals.items():
            with self.subTest(arrival):
                arrive()

                position = self.browser.execute_async_script(
                    HEAD_POSITION_AFTER_A_SCROLL_PAST_THE_TABLE_TOP
                )
                assert position == "fixed"

    def test_a_tab_swap_keeps_no_pin_of_the_swapped_out_table(self):
        TransactionFactory()
        SavingCloseFactory()

        self.swap_to_sales_and_back()

        print_styles = self.browser.find_elements(
            By.CSS_SELECTOR, "head style[media=print]"
        )
        assert len(print_styles) == 1
