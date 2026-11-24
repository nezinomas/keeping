import pytest
from django.urls import reverse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ...accounts.tests.factories import AccountFactory
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
CLOSED_FOLD_SWITCH = "#tab_content .switch"
# the switch's state, whether the closed accounts' table (the second) is drawn, its
# left edge against where the names start, the gap below it and a name's side padding
CLOSED_FOLD = """
const own = document.querySelector(arguments[0]);
const closed = document.querySelectorAll('#tab_content table')[1];
const drawn = closed.checkVisibility();
if (!own || !drawn) return [own && own.getAttribute('aria-checked'), drawn, []];
const name = closed.querySelector('td.main__name');
const pad = getComputedStyle(name);
const names = name.getBoundingClientRect().left + parseFloat(pad.paddingLeft);
const [at, table] = [own.getBoundingClientRect(), closed.getBoundingClientRect()];
return [own.getAttribute('aria-checked'), drawn,
    [Math.round(at.left - names), Math.round(table.top - at.bottom),
     pad.paddingLeft, pad.paddingRight]];
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

    def test_the_closed_accounts_switch_by_the_names_presses_and_folds_on_reload(self):
        AccountFactory(title="Open")
        AccountFactory(title="Old", closed=1998)
        # in line with the names (Q200), a gap above the table it unfolds; a phone's
        # name keeps half the side padding (Q202)
        folded = ["false", False, []]
        unfolded = {
            1280: ["true", True, [0, 12, "12px", "12px"]],
            360: ["true", True, [0, 12, "6px", "6px"]],
        }
        pressed = {}
        for width in (1280, 360):
            self.open_at(reverse("transactions:tab_accounts"), width)
            opened = self.browser.execute_script(CLOSED_FOLD, CLOSED_FOLD_SWITCH)
            assert opened == folded

            reads = []
            for press in (None, Keys.ENTER, Keys.SPACE):
                switch = self.browser.find_element(By.CSS_SELECTOR, CLOSED_FOLD_SWITCH)
                if press:
                    self.browser.execute_script("arguments[0].focus();", switch)
                    ActionChains(self.browser).send_keys(press).perform()
                else:
                    switch.click()
                self.wait_two_frames()
                reads.append(
                    self.browser.execute_script(CLOSED_FOLD, CLOSED_FOLD_SWITCH)
                )
            # a tab reload draws it afresh, folded (Q173)
            self.browser.execute_script("htmx.trigger(document.body, 'reload');")
            self.wait_until_idle()
            self.wait_two_frames()
            reads.append(self.browser.execute_script(CLOSED_FOLD, CLOSED_FOLD_SWITCH))
            pressed[width] = reads

        assert pressed == {
            width: [shown, folded, shown, folded] for width, shown in unfolded.items()
        }
