import re

import pytest
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ...expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.tests.factories import IncomeFactory
from ...pensions.tests.factories import PensionFactory
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..tabs import INDEX_TABS
from .factories import AccountWorthFactory
from .signals.helpers import buy, worth

pytestmark = pytest.mark.django_db

CHART_ROOTS = (
    "#chart-balance-container .highcharts-root,"
    " #chart-expenses-container .highcharts-root"
)
GAIN, HARM = "rgb(31, 107, 74)", "rgb(125, 39, 51)"
INK, INK_FAINT = "rgb(22, 34, 43)", "rgb(139, 151, 159)"
INK_MUTED = "rgb(90, 106, 117)"
HAIR, HAIR_SOFT = "rgb(207, 214, 218)", "rgb(225, 230, 232)"
DATA = "0.0862745 0.411765 0.607843"  # --skin-data's channels in `color(srgb)`
CLEAR = "rgba(0, 0, 0, 0)"
WASH = "rgba(232, 194, 26, 0.3)"


def test_index_chart_scripts_hold_no_colour_literal():
    # a chart reads the skin's tokens: a literal or a legacy token is the bug
    scripts = ("chart_index_balance.js", "chart_index_expenses.js")
    literals = {
        script: re.findall(
            r"#\w+|(?:rgb|hsl)a?\(|color\(|--chart-[\w-]+",
            (settings.SITE_ROOT / "static" / "js" / script).read_text(encoding="utf-8"),
        )
        for script in scripts
    }

    assert literals == dict.fromkeys(scripts, [])


@pytest.mark.webtest
class BookkeepingIndex(TestCase, Browser):
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

    # a tab opened by its URL is the reload test's charts row
    def test_the_charts_tab_draws_both_charts_by_click(self):
        self.click_tab("charts")

        assert self._drawn_charts() == 2

    def test_a_reload_redraws_each_chart_once_and_throws_nothing(self):
        # the overview has no chart: a reload there must find none to redraw
        for url_name, drawn in (
            ("bookkeeping:tab_overview", 0),
            ("bookkeeping:tab_charts", 2),
        ):
            with self.subTest(tab=url_name):
                self.open(reverse(url_name))

                assert self._reload() == {
                    "drawn_on_load": drawn,
                    "roots": ["redrawn"] * drawn,
                    "draws": drawn,
                    "errors": [],
                }

    def test_charts_draw_incomes_gain_expenses_harm_and_bars_fading_from_the_biggest(
        self,
    ):
        IncomeFactory()
        for title, price in (("Small", 100), ("Big", 300), ("Middle", 200)):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        self.open_at(reverse("bookkeeping:tab_charts"), 1500)

        drawn = self.browser.execute_script(
            "const all = q => [...document.querySelectorAll(q)];"
            " const fills = q => all(q).map(mark => getComputedStyle(mark).fill);"
            " return {areas: fills('#chart-balance-container"
            "  .highcharts-series .highcharts-area'),"
            " bars: fills('#chart-expenses-container .highcharts-point'),"
            " types: all('#chart-expenses-container .highcharts-xaxis-labels text')"
            "  .map(label => label.textContent)};"
        )
        # a mixed colour computes as `color(srgb r g b / alpha)`, its alpha 1 unsaid
        hues, alphas = set(), []
        for fill in drawn.pop("bars"):
            hue, _, alpha = fill.removeprefix("color(srgb ").partition(" / ")
            hues.add(hue.removesuffix(")"))
            alphas.append(alpha.removesuffix(")") or "1")

        assert (drawn, hues, alphas) == (
            {
                "areas": [GAIN, HARM],
                # the factory's own type, spent nothing, comes last, cut to 11
                "types": ["Big", "Middle", "Small", "Expense Typ"],
            },
            {DATA},
            ["1", "0.733333", "0.466667", "0.2"],
        )

    def test_the_charts_stand_side_by_side_from_1200_and_stack_below(self):
        placed = {}
        for width in (1200, 1199):
            self.open_at(reverse("bookkeeping:tab_charts"), width)
            placed[width] = self.browser.execute_script(
                "const [a, b] = [...document.querySelectorAll('#tab_content .panel')]"
                "  .map(panel => panel.getBoundingClientRect());"
                " const [x, y] = [...document.querySelectorAll("
                "  '#tab_content .highcharts-xaxis .highcharts-axis-line')]"
                "  .map(line => line.getBoundingClientRect().top);"
                " return {beside: a.top === b.top && a.right < b.left,"
                " stacked: b.top > a.bottom, same_width: a.width === b.width,"
                " axes_on_one_line: x === y};"
            )

        assert placed == {
            1200: {
                "beside": True,
                "stacked": False,
                "same_width": True,
                "axes_on_one_line": True,
            },
            1199: {
                "beside": False,
                "stacked": True,
                "same_width": True,
                "axes_on_one_line": False,
            },
        }

    def test_expenses_bars_print_their_part_of_the_year_and_axes_read_thousands(
        self,
    ):
        # a year with no expenses draws one empty bar, and no part of nothing
        self.open_at(reverse("bookkeeping:tab_charts"), 1500)
        empty_year = [
            self._chart_texts()["parts"],
            self.browser.execute_script(
                "return getComputedStyle(document.querySelector("
                "  '#chart-expenses-container .highcharts-point')).fill;"
            ),
        ]
        for title, price in (("Big", 30000), ("Small", 10000)):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        self.open_at(reverse("bookkeeping:tab_charts"), 1500)
        printed = self._chart_texts()
        printed["tooltip"] = self.read_chart(
            "chart-expenses-container",
            "c.tooltip.refresh([c.series[0].points[0]]);"
            " return c.tooltip.label.text.element.textContent;",
        ).split()
        printed["balance_tooltip"] = self.read_chart(
            "chart-balance-container",
            # a split tooltip draws a label per series: read what each would say
            "return c.series.map(s => c.tooltip.options.pointFormatter"
            "  .call(s.points[0]).replace(/<[^>]*>/g, ''));",
        )
        # a phone prints every other month, and no tick past December
        self.open_at(reverse("bookkeeping:tab_charts"), 360)
        printed["phone_months"] = self._chart_texts()["months"]

        # the factory's own type, spent nothing, gets the last bar and no figure
        assert (empty_year, printed) == (
            [[], f"color(srgb {DATA})"],
            {
                "parts": ["75,0%", "25,0%"],
                "part_look": [INK_MUTED, "12px", "400"],
                "expenses_axis": ["0", "0,1k", "0,2k", "0,3k", "0,4k"],
                "balance_axis": ["0", "0,1k", "0,2k", "0,3k", "0,4k", "0,5k"],
                "months": [
                    "Sausis",
                    "Vasaris",
                    "Kovas",
                    "Balandis",
                    "Gegužė",
                    "Birželis",
                    "Liepa",
                    "Rugpjūtis",
                    "Rugsėjis",
                    "Spalis",
                    "Lapkritis",
                    "Gruodis",
                ],
                "tooltip": ["Big", "300€", "75,0%"],
                "balance_tooltip": ["Pajamos: 0€", "Išlaidos: 400€"],
                # the widened edges' tick past December, printed empty
                "phone_months": [
                    "Sausis",
                    "Kovas",
                    "Gegužė",
                    "Liepa",
                    "Rugsėjis",
                    "Lapkritis",
                    "",
                ],
            },
        )

    def test_a_signed_figure_is_gain_or_harm_text_and_a_zero_is_not(self):
        for title, have in (("Even", 10000), ("Gain", 15000), ("Loss", 5000)):
            account = AccountFactory(title=title)
            IncomeFactory(account=account, price=10000)
            AccountWorthFactory(account=account, price=have)

        self.open_at(reverse("bookkeeping:tab_overview"), 1500)
        looks = self._looks(
            # Delta's zero is drawn "ok": a gain, unlike every other zero (Q26)
            delta_ok="#accounts tbody tr:nth-child(1) td:last-child",
            delta_gain="#accounts tbody tr:nth-child(2) td:last-child",
            delta_loss="#accounts tbody tr:nth-child(3) td:last-child",
            # Even + Gain + Loss: a zero with no data-cell to paint it faint
            delta_total="#accounts tfoot td:last-child",
            # the year strip's end, not highlighted: a figure, not a sign
            year_end="#last td:nth-child(3)",
        )
        # a signed total keeps its colour on the skin's ink total row (Q35)
        account = AccountFactory(title="Gain 2")
        IncomeFactory(account=account, price=10000)
        AccountWorthFactory(account=account, price=12000)
        self.open_at(reverse("bookkeeping:tab_overview"), 1500)
        looks |= self._looks(delta_total_gain="#accounts tfoot td:last-child")
        fund = SavingTypeFactory(title="Up")
        buy(fund, 100000)
        worth(fund, 150000)
        self.open_at(reverse("bookkeeping:tab_funds"), 1500)
        looks |= self._looks(profit_total="#savings tfoot td:last-child")
        self.open_at(reverse("bookkeeping:tab_balance"), 1500)
        looks |= self._looks(
            zero_month="#table-balance tbody tr:nth-child(2) td:nth-child(4)"
        )

        assert looks == {
            "delta_ok": [GAIN, True],
            "delta_gain": [GAIN, True],
            "delta_loss": [HARM, True],
            "delta_total": [INK, True],
            "delta_total_gain": [GAIN, True],
            "profit_total": [GAIN, True],
            "year_end": [INK, True],
            "zero_month": [INK_FAINT, True],
        }

    def test_a_cash_flow_mismatch_wears_the_attention_wash_on_each_tab(self):
        IncomeFactory(price=100000)
        cells = {
            "bookkeeping:tab_overview": "#accounts tfoot [data-check]",
            "bookkeeping:tab_balance": "#table-balance tfoot [data-check]",
        }
        marks = {}
        for case, accounts_balance in (("equal", 100000), ("differ", 99900)):
            AccountBalance.objects.filter(year=1999).update(balance=accounts_balance)
            for url_name, cell in cells.items():
                self.open_at(reverse(url_name), 1500)
                marks[case, url_name.removeprefix("bookkeeping:tab_")] = (
                    self.browser.execute_script(
                        "const cell = document.querySelector(arguments[0]);"
                        " return [getComputedStyle(cell).backgroundColor,"
                        " getComputedStyle(cell, '::before').content];",
                        cell,
                    )
                )

        assert marks == {
            ("equal", "overview"): [CLEAR, "none"],
            ("equal", "balance"): [CLEAR, "none"],
            ("differ", "overview"): [WASH, '"! "'],
            ("differ", "balance"): [WASH, '"! "'],
        }

    def test_balance_head_groups_its_columns_and_a_bordered_toggle_shows_the_debts(
        self,
    ):
        self.open_at(reverse("bookkeeping:tab_balance"), 1500)
        toggle = self.browser.find_element(
            By.CSS_SELECTOR, "#table-balance a[role=button]"
        )
        # without a border the toggle reads as a header label (Q63); the first group
        # is blank under the Panel's title (Q62), the others centred over their columns
        looks = self.browser.execute_script(
            "const groups = document.querySelector('#table-balance thead tr').cells;"
            " const toggle = getComputedStyle(arguments[0]);"
            " return [toggle.borderTopStyle, toggle.borderTopColor,"
            " groups[0].textContent.trim(),"
            " ...[groups[1], groups[2]].map(c => getComputedStyle(c).textAlign)];",
            toggle,
        )
        shown = []
        for _press in range(3):
            self.wait_two_frames()
            # each row's visible cells span every column, the group row's too
            spans = self.browser.execute_script(
                "const rows = document.querySelector('#table-balance table').rows;"
                " return [...new Set([...rows].map(row => [...row.cells]"
                ".filter(c => c.checkVisibility())"
                ".reduce((sum, c) => sum + c.colSpan, 0)))];"
            )
            shown.append((spans, toggle.text))
            toggle.click()

        hidden, opened = ([7], "Rodyti skolas"), ([11], "Slėpti skolas")
        assert (looks, shown) == (
            ["solid", HAIR, "", "center", "center"],
            [hidden, opened, hidden],
        )

    def test_insert_clears_each_worth_row(self):
        AccountFactory(title="Account 0")
        AccountFactory(title="Account 1")
        self.open(reverse("bookkeeping:index"))

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

    def test_every_index_tab_fits_a_phone(self):
        # a funds table and the accounts table run wider than a phone's column
        IncomeFactory()
        SavingFactory()
        PensionFactory()
        overflow = {}
        for tab in INDEX_TABS:
            self.open_at(tab.url, 360)
            overflow[tab.name] = self.page_overflow()

        assert overflow == dict.fromkeys(("overview", "funds", "balance", "charts"), 0)

    def test_month_page_fits_a_phone_and_its_table_scrolls_in_its_box(self):
        # a column per type: ten make the table wider than the phone
        for i in range(10):
            ExpenseTypeFactory(title=f"Expense Type {i}")
        self.open_at(reverse("bookkeeping:month"), 360)

        overflow = self.browser.execute_script(
            "const box = document.getElementById('month-content');"
            " return {width: innerWidth,"
            " table_scrolls: box.scrollWidth > box.clientWidth};"
        ) | {"page_overflow": self.page_overflow()}

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
        # each quarter's first month, then the rule closing December
        quarters = (5, 8, 11)
        body = [[i, HAIR_SOFT] for i in quarters] + [[14, HAIR]]
        assert ruled == [
            [[3, HAIR], [4, HAIR], [5, HAIR], [6, HAIR]],
            [[i, HAIR] for i in (*quarters, 14)],
            body,
            body,
        ]

    def test_month_table_fades_its_edge_only_while_it_scrolls(self):
        IncomeFactory()
        for width, fade in ((360, True), (1500, False)):
            with self.subTest(width=width):
                self.open_at(reverse("bookkeeping:detailed"), width)
                faded = self.browser.execute_script(
                    "return getComputedStyle(document.querySelector('.month-table'))"
                    "  .maskImage !== 'none';"
                )

                assert faded is fade

    def test_a_swap_beside_a_table_with_no_pin_library_throws_nothing(self):
        # the summary draws a .sticky-table and loads no sticky-table-headers.js
        self.open(reverse("bookkeeping:summary_savings_and_incomes"))
        self.browser.execute_script(
            "window.errors = [];"
            " addEventListener('error', e => errors.push(e.message));"
            f" htmx.ajax('GET', '{reverse('incomes:new')}', '#mainModal');"
        )
        self.wait_until_idle()

        swap = self.browser.execute_script(
            "return {tables: document.querySelectorAll('.sticky-table').length,"
            " form: !!document.querySelector('#mainModal .modal-form'), errors};"
        )
        assert swap == {"tables": 1, "form": True, "errors": []}

    def _looks(self, **cells):
        """Each cell's colour, and whether its background is its row's first cell's."""
        return self.browser.execute_script(
            "return Object.fromEntries(Object.entries(arguments[0]).map(([k, q]) => {"
            " const cell = document.querySelector(q);"
            " const own = getComputedStyle(cell);"
            " const row = getComputedStyle(cell.parentElement.firstElementChild);"
            " return [k, [own.color, own.backgroundColor === row.backgroundColor]];"
            " }));",
            cells,
        )

    def _chart_texts(self):
        return self.browser.execute_script(
            "const texts = q => [...document.querySelectorAll(q)]"
            "  .map(e => e.textContent);"
            " const part = document.querySelector("
            "  '#chart-expenses-container .highcharts-data-label span');"
            " const look = part ? getComputedStyle(part) : {};"
            " return {parts: texts('#chart-expenses-container"
            "  .highcharts-data-label span'),"
            " part_look: [look.color, look.fontSize, look.fontWeight],"
            " expenses_axis: texts('#chart-expenses-container"
            "  .highcharts-yaxis-labels text'),"
            " balance_axis: texts('#chart-balance-container"
            "  .highcharts-yaxis-labels text'),"
            " months: texts('#chart-balance-container .highcharts-xaxis-labels text')};"
        )

    def page_overflow(self):
        """How far the page runs past the window's width."""
        return self.browser.execute_script(
            "const page = document.documentElement;"
            " return page.scrollWidth - page.clientWidth;"
        )

    def _drawn_charts(self):
        return self.browser.execute_script(
            f"return document.querySelectorAll('{CHART_ROOTS}').length;"
        )

    def _reload(self):
        """Roots marked on load, then each read after one reload."""
        drawn_on_load = self.browser.execute_script(
            f"const drawn = document.querySelectorAll('{CHART_ROOTS}');"
            " drawn.forEach(root => root.dataset.drawnOnLoad = '');"
            " window.draws = 0; window.errors = [];"
            " addEventListener('error', e => errors.push(e.message));"
            " Highcharts.addEvent(Highcharts.Chart, 'load', () => window.draws++);"
            " htmx.trigger(document.body, 'reload');"
            " return drawn.length;"
        )
        self.wait_until_idle()

        return {"drawn_on_load": drawn_on_load} | self.browser.execute_script(
            f"return {{roots: [...document.querySelectorAll('{CHART_ROOTS}')]"
            ".map(root => 'drawnOnLoad' in root.dataset ? 'stale' : 'redrawn'),"
            " draws: window.draws, errors: window.errors};"
        )
