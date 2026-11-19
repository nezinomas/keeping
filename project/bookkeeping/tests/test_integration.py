import re

import pytest
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import Browser
from ...expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.tests.factories import IncomeFactory
from ...pensions.tests.factories import PensionFactory, PensionTypeFactory
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
YEAR_STRIP = ".overview-grid__column:first-child .panel:first-child"
EXPENSE_PARTS = "#chart-expenses-container .highcharts-data-label span"
HAIR, HAIR_SOFT = "rgb(207, 214, 218)", "rgb(225, 230, 232)"
DATA = "0.0862745 0.411765 0.607843"  # --skin-data's channels in `color(srgb)`
CLEAR = "rgba(0, 0, 0, 0)"
WASH = "rgba(232, 194, 26, 0.3)"
# CSS's named colours, `transparent` and `currentcolor` among them
NAMED_COLOURS = """
    aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
    blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue
    cornsilk crimson currentcolor cyan darkblue darkcyan darkgoldenrod darkgray
    darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
    darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey
    darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick
    floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green
    greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender
    lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
    lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
    lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow
    lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid
    mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise
    mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace
    olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise
    palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple
    red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna
    silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal
    thistle tomato transparent turquoise violet wheat white whitesmoke yellow
    yellowgreen
""".split()


def test_index_chart_scripts_hold_no_colour_literal():
    # a chart reads the skin's tokens: a literal or a legacy token is the bug; the one
    # named colour allowed is an alpha step's `color-mix(..., N%, transparent)` (Q78)
    scripts = ("chart_index_balance.js", "chart_index_expenses.js")
    literal = re.compile(
        r"#\w+|\b(?:rgb|hsl|hwb|lab|lch|oklab|oklch|color)a?\(|--chart-[\w-]+"
        rf"|\b(?:{'|'.join(NAMED_COLOURS)})\b"
    )
    literals = {
        script: literal.findall(
            (settings.SITE_ROOT / "static" / "js" / script)
            .read_text(encoding="utf-8")
            .replace("%, transparent)", "%)")
        )
        for script in scripts
    }

    assert literals == dict.fromkeys(scripts, [])


def page_overflow(browser):
    """How far the page runs past the window's width."""
    return browser.execute_script(
        "const page = document.documentElement;"
        " return page.scrollWidth - page.clientWidth;"
    )


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
        for tab, drawn in (("overview", 0), ("charts", 2)):
            with self.subTest(tab=tab):
                self.open(INDEX_TABS[tab].url)

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
        self.open_at(INDEX_TABS["charts"].url, 1500)

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

    def test_two_types_cut_alike_on_the_axis_keep_a_bar_each(self):
        for title, price in (
            ("Transportas kuras", 30000),
            ("Transportas remontas", 10000),
        ):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        self.open_at(INDEX_TABS["charts"].url, 1500)

        bars = self.read_chart(
            "chart-expenses-container",
            "return c.series[0].points.filter(p => p.y).map(p => {"
            "  c.tooltip.refresh([p]);"
            "  return [p.x, p.series.xAxis.ticks[p.x].label.textStr,"
            "   p.dataLabel.text.textStr,"
            "   c.tooltip.label.text.element.textContent.trim().split('\\n')[0]];"
            " });",
        )

        # the axis cuts a name to fit; the tooltip names the type whole
        assert bars == [
            [0, "Transportas", "75,0%", "Transportas kuras"],
            [1, "Transportas", "25,0%", "Transportas remontas"],
        ]

    def test_the_charts_stand_side_by_side_from_1200_and_stack_below(self):
        placed = {}
        for width in (1200, 1199):
            self.open_at(INDEX_TABS["charts"].url, width)
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

    def test_a_year_with_no_expenses_draws_one_whole_bar_and_no_part(self):
        self.open_at(INDEX_TABS["charts"].url, 1500)

        drawn = self.browser.execute_script(
            "return getComputedStyle(document.querySelector("
            "  '#chart-expenses-container .highcharts-point')).fill;"
        )

        assert (drawn, self._texts(EXPENSE_PARTS)) == (f"color(srgb {DATA})", [])

    def test_each_expense_bar_prints_its_part_of_the_year_in_the_muted_figure(self):
        self._open_charts_with_two_types(1500)

        look = self.browser.execute_script(
            f"const look = getComputedStyle(document.querySelector('{EXPENSE_PARTS}'));"
            " return [look.color, look.fontSize, look.fontWeight];"
        )

        # the factory's own type, spent nothing, gets the last bar and no figure
        assert (self._texts(EXPENSE_PARTS), look) == (
            ["75,0%", "25,0%"],
            [INK_MUTED, "12px", "400"],
        )

    def test_both_money_axes_read_from_100_in_thousands(self):
        self._open_charts_with_two_types(1500)

        axes = [
            self._texts(f"#{chart} .highcharts-yaxis-labels text")
            for chart in ("chart-expenses-container", "chart-balance-container")
        ]

        assert axes == [
            ["0", "0,1k", "0,2k", "0,3k", "0,4k"],
            ["0", "0,1k", "0,2k", "0,3k", "0,4k", "0,5k"],
        ]

    def test_the_month_axis_names_each_month_and_no_tick_past_december(self):
        months = {}
        for width in (1500, 360):
            self._open_charts_with_two_types(width)
            months[width] = self._texts(
                "#chart-balance-container .highcharts-xaxis-labels text"
            )

        # a phone prints every other month; the widened edges' tick past December
        # prints empty
        assert months == {
            1500: [
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
            360: ["Sausis", "Kovas", "Gegužė", "Liepa", "Rugsėjis", "Lapkritis", ""],
        }

    def test_each_chart_tooltip_prints_whole_euros(self):
        self._open_charts_with_two_types(1500)

        expenses = self.read_chart(
            "chart-expenses-container",
            "c.tooltip.refresh([c.series[0].points[0]]);"
            " return c.tooltip.label.text.element.textContent;",
        ).split()
        balance = self.read_chart(
            "chart-balance-container",
            # a split tooltip draws a label per series: read what each would say
            "return c.series.map(s => c.tooltip.options.pointFormatter"
            "  .call(s.points[0]).replace(/<[^>]*>/g, ''));",
        )

        assert (expenses, balance) == (
            ["Big", "300€", "75,0%"],
            ["Pajamos: 0€", "Išlaidos: 400€"],
        )

    def test_the_overview_panels_stand_in_three_columns_from_992_and_one_below(self):
        placed = {}
        for width in (992, 991):
            self.open_at(INDEX_TABS["overview"].url, width)
            placed[width] = self.browser.execute_script(
                "const [a, b, c] = [...document.querySelectorAll("
                "  '.overview-grid__column')].map(col => col.getBoundingClientRect());"
                " return {beside: a.top === b.top && b.top === c.top"
                "  && a.right < b.left && b.right < c.left,"
                " stacked: a.bottom <= b.top && b.bottom <= c.top,"
                " middle_widest: b.width > a.width"
                "  && Math.round(a.width) === Math.round(c.width)};"
            )

        # no open debt: the third column is empty and keeps its track
        assert placed == {
            992: {"beside": True, "stacked": False, "middle_widest": True},
            991: {"beside": False, "stacked": True, "middle_widest": False},
        }

    def test_the_forecast_title_opens_and_folds_its_table_and_loads_it_once(self):
        self.open_at(INDEX_TABS["overview"].url, 1500)
        title = self.browser.find_element(By.CSS_SELECTOR, ".panel__toggle")
        seen = []
        for _press in range(4):
            self.wait_two_frames()
            seen.append(
                self.browser.execute_script(
                    "const icon = document.querySelector('.panel__toggle i');"
                    " const table = document.querySelector('#forecast table');"
                    " const fetched = performance.getEntriesByType('resource')"
                    "  .filter(e => e.name.includes(arguments[0])).length;"
                    " return [icon.classList.contains('bi-chevron-up'),"
                    "  icon.getBoundingClientRect().width > 0,"
                    "  !!table && table.checkVisibility(), fetched];",
                    reverse("bookkeeping:forecast"),
                )
            )
            # the title's word, not its chevron (Q54)
            ActionChains(self.browser).move_to_element_with_offset(
                title, -title.size["width"] // 2 + 5, 0
            ).click().perform()
            self.wait_until_idle()

        folded, opened = [False, True, False, 1], [True, True, True, 1]
        assert seen == [[False, True, False, 0], opened, folded, opened]

    def test_a_signed_figure_is_gain_or_harm_text_and_a_zero_is_not(self):
        for title, have in (("Even", 10000), ("Gain", 15000), ("Loss", 5000)):
            account = AccountFactory(title=title)
            IncomeFactory(account=account, price=10000)
            AccountWorthFactory(account=account, price=have)

        self.open_at(INDEX_TABS["overview"].url, 1500)
        looks = self._looks(
            # Delta's zero is drawn "ok": a gain, unlike every other zero (Q26)
            delta_ok="#accounts tbody tr:nth-child(1) td:last-child",
            delta_gain="#accounts tbody tr:nth-child(2) td:last-child",
            delta_loss="#accounts tbody tr:nth-child(3) td:last-child",
            # Even + Gain + Loss: a zero with no data-cell to paint it faint
            delta_total="#accounts tfoot td:last-child",
            # the year strip's end, not highlighted: a figure, not a sign
            year_end=f"{YEAR_STRIP} td:nth-child(2)",
        )
        # a signed total keeps its colour on the skin's ink total row (Q35)
        account = AccountFactory(title="Gain 2")
        IncomeFactory(account=account, price=10000)
        AccountWorthFactory(account=account, price=12000)
        self.open_at(INDEX_TABS["overview"].url, 1500)
        looks |= self._looks(delta_total_gain="#accounts tfoot td:last-child")
        fund = SavingTypeFactory(title="Up")
        buy(fund, 100000)
        worth(fund, 150000)
        self.open_at(INDEX_TABS["funds"].url, 1500)
        looks |= self._looks(profit_total="#savings tfoot td:last-child")
        self.open_at(INDEX_TABS["balance"].url, 1500)
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
            "overview": "#accounts tfoot [data-check]",
            "balance": "#table-balance tfoot [data-check]",
        }
        marks = {}
        for case, accounts_balance in (("equal", 100000), ("differ", 99900)):
            AccountBalance.objects.filter(year=1999).update(balance=accounts_balance)
            for tab, cell in cells.items():
                self.open_at(INDEX_TABS[tab].url, 1500)
                marks[case, tab] = self.browser.execute_script(
                    "const cell = document.querySelector(arguments[0]);"
                    " return [getComputedStyle(cell).backgroundColor,"
                    " getComputedStyle(cell, '::before').content];",
                    cell,
                )

        assert marks == {
            ("equal", "overview"): [CLEAR, "none"],
            ("equal", "balance"): [CLEAR, "none"],
            ("differ", "overview"): [WASH, '"! "'],
            ("differ", "balance"): [WASH, '"! "'],
        }

    def test_balance_head_groups_its_columns_beside_a_bordered_toggle(self):
        toggle = self.balance_toggle()
        # without a border the toggle reads as a header label (Q63), and an action
        # reads in the body face (sass.md *Type*); the first group is blank under the
        # Panel's title (Q62), the others centred over their columns
        looks = self.browser.execute_script(
            "const groups = document.querySelector('#table-balance thead tr').cells;"
            " const toggle = getComputedStyle(arguments[0]);"
            " return [toggle.borderTopStyle, toggle.borderTopColor,"
            " toggle.fontFamily.split(',')[0],"
            " groups[0].textContent.trim(),"
            " ...[groups[1], groups[2]].map(c => getComputedStyle(c).textAlign)];",
            toggle,
        )

        assert looks == [
            "solid",
            HAIR,
            '"Segoe UI Variable Text"',
            "",
            "center",
            "center",
        ]

    def test_the_balance_toggle_shows_and_hides_the_debts(self):
        toggle = self.balance_toggle()
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
        assert shown == [hidden, opened, hidden]

    def test_insert_clears_each_worth_row(self):
        AccountFactory(title="Account 0")
        AccountFactory(title="Account 1")
        self.open(INDEX_TABS["overview"].url)

        self.press_the_pill("bookkeeping:accounts_worth_new")
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

    def test_a_worth_saved_from_its_pill_reloads_the_tab_once_and_closes_the_modal(
        self,
    ):
        AccountFactory()
        SavingTypeFactory()
        PensionTypeFactory()
        after_save = {}
        for tab, url_name in (
            ("overview", "bookkeeping:accounts_worth_new"),
            ("funds", "bookkeeping:savings_worth_new"),
            ("funds", "bookkeeping:pensions_worth_new"),
        ):
            self.open(INDEX_TABS[tab].url)
            self.press_the_pill(url_name)
            self.browser.execute_script(
                "window.tabSwaps = 0;"
                " htmx.on('htmx:after:swap', e => {"
                " if (e.detail.ctx.target.id === 'tab_content') tabSwaps++; });"
            )
            self.browser.find_element(By.ID, "id_form-0-price").send_keys("5")
            self.browser.find_element(By.ID, "_close").click()
            self.wait_until_idle()
            after_save[url_name] = self.browser.execute_script(
                "return {tab_swaps: tabSwaps,"
                " modal_hidden: document.getElementById('mainModalContainer').hidden,"
                " form: !!document.querySelector('#mainModal .modal-form')};"
            )

        assert after_save == dict.fromkeys(
            after_save, {"tab_swaps": 1, "modal_hidden": True, "form": False}
        )

    def test_every_index_tab_fits_a_phone(self):
        # a funds table and the accounts table run wider than a phone's column
        IncomeFactory()
        SavingFactory()
        PensionFactory()
        overflow = {}
        for tab in INDEX_TABS:
            self.open_at(tab.url, 360)
            overflow[tab.name] = page_overflow(self.browser)

        assert overflow == dict.fromkeys((tab.name for tab in INDEX_TABS), 0)

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

    def _open_charts_with_two_types(self, width: int):
        for title, price in (("Big", 30000), ("Small", 10000)):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        self.open_at(INDEX_TABS["charts"].url, width)

    def _texts(self, selector: str) -> list[str]:
        return self.browser.execute_script(
            "return [...document.querySelectorAll(arguments[0])]"
            "  .map(e => e.textContent);",
            selector,
        )

    def balance_toggle(self):
        self.open_at(INDEX_TABS["balance"].url, 1500)

        return self.browser.find_element(
            By.CSS_SELECTOR, "#table-balance a[role=button]"
        )

    def press_the_pill(self, url_name):
        url = reverse(url_name)
        self.browser.find_element(
            By.CSS_SELECTOR, f".quick-add__pill[hx-get='{url}']"
        ).click()
        self.wait_until_idle()

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


@pytest.mark.webtest
class BookkeepingMonthDetailedAndSummary(TestCase, Browser):
    def test_month_page_fits_a_phone_and_its_table_scrolls_in_its_box(self):
        # a column per type: ten make the table wider than the phone
        for i in range(10):
            ExpenseTypeFactory(title=f"Expense Type {i}")
        self.open_at(reverse("bookkeeping:month"), 360)

        overflow = self.browser.execute_script(
            "const box = document.getElementById('month-content');"
            " return {width: innerWidth,"
            " table_scrolls: box.scrollWidth > box.clientWidth};"
        ) | {"page_overflow": page_overflow(self.browser)}

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
