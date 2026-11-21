import json
import re
from datetime import date

import pytest
import time_machine
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...core.tests.test_integration_browser import (
    FIND_TIP,
    NO_ANCHORING,
    TIP_BOX,
    Browser,
)
from ...expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.tests.factories import IncomeFactory
from ...journals.tests.factories import JournalFactory
from ...pensions.tests.factories import PensionFactory, PensionTypeFactory
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..tabs import INDEX_TABS
from .factories import AccountWorthFactory
from .signals.helpers import buy, worth

pytestmark = pytest.mark.django_db

CHART_ROOTS = (
    "#chart-balance-container .highcharts-root,"
    " #chart-expenses-container .highcharts-root,"
    " #chart-incomes-expenses-container .highcharts-root"
)
# the dev DB's longest fund name
LONGEST_FUND = "VALL - Vanguard FTSE GLB AL-CAP ETF"
GAIN, HARM = "rgb(31, 107, 74)", "rgb(125, 39, 51)"
INK, INK_FAINT = "rgb(22, 34, 43)", "rgb(139, 151, 159)"
INK_MUTED = "rgb(90, 106, 117)"
YEAR_STRIP = ".overview-grid__column:first-child .panel:first-child"
EXPENSE_PARTS = "#chart-expenses-container .highcharts-data-label text"
HAIR, HAIR_SOFT = "rgb(207, 214, 218)", "rgb(225, 230, 232)"
DATA_RGB, TINT = "rgb(22, 105, 155)", "rgba(22, 105, 155, 0.22)"  # --skin-data
YEAR_0, HARM_SOFT = "rgb(110, 151, 178)", "rgb(196, 127, 134)"
# a current month's mark at the theme's inactive opacity, 0.35
TINT_FADED = "color(srgb 0.0862745 0.411765 0.607843 / 0.0768628)"
DATA_FADED = "color(srgb 0.0862745 0.411765 0.607843 / 0.35)"
HARM_FADED = "color(srgb 0.490196 0.152941 0.2 / 0.35)"
CLEAR = "rgba(0, 0, 0, 0)"
PAPER = "rgb(255, 255, 255)"
BODY_FACE = (
    '"Segoe UI Variable Text", "Segoe UI", -apple-system, "Helvetica Neue", Arial,'
    " sans-serif"
)
NO_INCOMES_TIP = "th > .tip[data-tip^='Nebūtinos išlaidos']"
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
    scripts = ("chart_index_months.js", "chart_index_expenses.js", "chart_paper.js")
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


# each mark under `q` read as the computed `keys` of its style
LOOK = (
    "const look = (q, ...keys) => [...document.querySelectorAll(q)]"
    "  .map(mark => keys.map(key => getComputedStyle(mark)[key]));"
)


def tooltip_at(x: int) -> str:
    """A `read_chart` script's start: the tooltip opened on month `x`, its lines `tip`."""
    return (
        f"const at = c.series.map(s => s.points[{x}]);"
        " c.tooltip.refresh(c.options.tooltip.shared ? at : at[0]);"
        " const tip = c.tooltip.label.text.element.innerText.split('\\n')"
        "  .filter(Boolean);"
    )


def page_overflow(browser):
    """How far the page runs past the window's width."""
    return browser.execute_script(
        "const page = document.documentElement;"
        " return page.scrollWidth - page.clientWidth;"
    )


# a header tip's bubble against its cell, its scroll box, the window and the page;
# whole within 2px, since the points are whole pixels and its edges are not
TIP_BUBBLE = (
    TIP_BOX
    + """
    const box = tip.closest('.table-responsive');
    const edge = box.getBoundingClientRect();
    const page = document.documentElement;
    return {
        lines: Math.round(lines),
        whole: !!at && Math.abs(at.right - at.left - width) < 2
            && Math.abs(at.bottom - at.top - height) < 2,
        below_its_header: !!at
            && at.top >= tip.closest('th').getBoundingClientRect().bottom,
        gap_is_8px: !!at && Math.abs(at.top - own.bottom - 8) < 2,
        in_the_window: !!at && at.left >= 0 && at.top >= 0
            && at.right <= innerWidth && at.bottom <= innerHeight,
        leaves_its_box: !!at && (at.left < edge.left || at.top < edge.top
            || at.right > edge.right || at.bottom > edge.bottom),
        box_scrolls: box.scrollWidth > box.clientWidth
            || box.scrollHeight > box.clientHeight,
        page_overflow: page.scrollWidth - page.clientWidth,
    };
"""
)
# where the bubble lies against its trigger: under it or beside it, 8px away, its
# middle on the trigger's
TIP_AGAINST_ITS_TRIGGER = (
    TIP_BOX
    + """
    const under = !!at && at.top >= own.bottom - 1;
    const gap = under ? at.top - own.bottom : at.left - own.right;
    const off = under
        ? at.left + at.right - own.left - own.right
        : at.top + at.bottom - own.top - own.bottom;
    return {
        position: bubble.position,
        lines: Math.round(lines),
        side: !at ? 'none' : under ? 'under' : 'beside',
        gap_is_8px: !!at && Math.abs(gap - 8) < 2,
        middle_on_its_trigger: !!at && Math.abs(off) < 4,
    };
"""
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
    def test_the_charts_tab_draws_its_three_charts_by_click(self):
        self.click_tab("charts")

        assert self._drawn_charts() == 3

    def test_a_reload_redraws_each_chart_once_and_throws_nothing(self):
        # the overview has no chart: a reload there must find none to redraw
        for tab, drawn in (("overview", 0), ("charts", 3)):
            with self.subTest(tab=tab):
                self.open(INDEX_TABS[tab].url)

                assert self._reload() == {
                    "drawn_on_load": drawn,
                    "roots": ["redrawn"] * drawn,
                    "draws": drawn,
                    "errors": [],
                }

    def test_charts_draw_flat_named_one_hue_bars_and_two_marked_lines_on_their_averages(
        self,
    ):
        IncomeFactory(price=120000)
        for title, price in (
            ("Transportas remontas", 60000),
            ("Transportas kuras", 180000),
        ):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        self.open_at(INDEX_TABS["charts"].url, 1500)

        drawn = self.browser.execute_script(
            "const all = q => [...document.querySelectorAll(q)];"
            f" {LOOK}"
            " const lines = '#chart-incomes-expenses-container ';"
            " return {bars: look('#chart-expenses-container .highcharts-point',"
            "  'fill', 'stroke', 'strokeWidth'),"
            " types: all('#chart-expenses-container .highcharts-xaxis-labels text')"
            "  .map(label => label.textContent),"
            " lines: look(lines + '.highcharts-series .highcharts-graph',"
            "  'stroke', 'fill'),"
            " rules: look(lines + '.highcharts-plot-line', 'stroke', 'strokeDasharray'),"
            " rule_labels: all(lines + '.chart-rule-label').map(l => l.textContent),"
            " legend: all(lines + '.highcharts-legend-item text')"
            "  .map(item => item.textContent)};"
        )
        markers = self.read_chart(
            "chart-incomes-expenses-container",
            "return c.series.map(s => s.symbol);",
        )
        drawn["horizontal"] = self.read_chart(
            "chart-expenses-container", "return c.inverted;"
        )

        assert (drawn, markers) == (
            {
                "bars": [[TINT, YEAR_0, "1px"]] * 3,
                # whole and flat, biggest first; the factory's own type spent nothing
                "types": ["Transportas kuras", "Transportas remontas", "Expense Type"],
                "lines": [[DATA_RGB, "none"], [HARM, "none"]],
                "rules": [[DATA_RGB, "1px, 3px"], [HARM, "1px, 3px"]],
                # the twelve months of a past year: 1.200€ and 2.400€ over twelve
                "rule_labels": ["Vidurkis: 100€", "Vidurkis: 200€"],
                "legend": ["Pajamos", "Išlaidos"],
                "horizontal": True,
            },
            ["circle", "diamond"],
        )

    def test_a_line_whose_average_is_nought_draws_no_rule(self):
        # a year with no expenses: its line lies at nought, read against no rule (Q122)
        IncomeFactory(price=120000)
        self.open_at(INDEX_TABS["charts"].url, 1500)

        drawn = self.browser.execute_script(
            f"{LOOK}"
            " const lines = '#chart-incomes-expenses-container ';"
            " return {rules: look(lines + '.highcharts-plot-line', 'stroke'),"
            " rule_labels: [...document.querySelectorAll(lines + '.chart-rule-label')]"
            "  .map(l => l.textContent)};"
        )

        assert drawn == {"rules": [[DATA_RGB]], "rule_labels": ["Vidurkis: 100€"]}

    def test_the_balance_chart_draws_each_month_s_balance_against_a_zero_rule(self):
        IncomeFactory(price=50000)
        ExpenseFactory(price=20000)
        ExpenseFactory(date=date(1999, 2, 1), price=150000)
        drawn = {}
        for width in (1500, 767):
            self.open_at(INDEX_TABS["charts"].url, width)
            drawn[width] = self.browser.execute_script(
                f"{LOOK}"
                " const box = '#chart-balance-container ';"
                " return {columns: look(box + '.highcharts-point', 'fill', 'stroke'),"
                " figures: [...document.querySelectorAll("
                "  box + '.highcharts-data-label text')]"
                "  .map(f => [f.textContent, getComputedStyle(f).fill]),"
                " zero: look(box + '.highcharts-plot-line', 'stroke'),"
                " series: document.querySelectorAll("
                "  box + '.highcharts-series:not(.highcharts-markers)').length,"
                " legend: document.querySelectorAll(box + '.highcharts-legend-item')"
                "  .length};"
            )
            drawn[width]["zero_at"] = self.read_chart(
                "chart-balance-container",
                "return c.yAxis[0].plotLinesAndBands.map(rule => rule.options.value);",
            )

        # one column a month, a month at nought in the tint; a figure is muted, off a
        # month at nought, and below 768px left to the tooltip
        at_1500 = {
            "columns": [[TINT, YEAR_0], [HARM_SOFT, HARM]] + [[TINT, YEAR_0]] * 10,
            "figures": [["0,3k", INK_MUTED], ["-1,5k", INK_MUTED]],
            "zero": [[INK]],
            "zero_at": [0],
            "series": 1,
            "legend": 0,
        }
        assert drawn == {1500: at_1500, 767: at_1500 | {"figures": []}}

    def test_the_charts_stand_side_by_side_from_1200_and_stack_below(self):
        placed = {}
        for width in (1200, 1199):
            self.open_at(INDEX_TABS["charts"].url, width)
            a, b, c = self._boxes("#tab_content .panel")
            x, y, _lines = self._boxes("#tab_content .highcharts-plot-background")
            placed[width] = {
                "beside": a["top"] == b["top"] and a["right"] < b["left"],
                "stacked": b["top"] > a["bottom"],
                "same_width": a["width"] == b["width"],
                "plots_end_on_one_line": x["bottom"] == y["bottom"],
                "lines_below_full_width": c["top"] > max(a["bottom"], b["bottom"])
                and c["left"] == a["left"]
                and c["right"] == b["right"],
            }

        assert placed == {
            1200: {
                "beside": True,
                "stacked": False,
                "same_width": True,
                "plots_end_on_one_line": True,
                "lines_below_full_width": True,
            },
            1199: {
                "beside": False,
                "stacked": True,
                "same_width": True,
                "plots_end_on_one_line": False,
                "lines_below_full_width": True,
            },
        }

    def test_a_year_with_no_expenses_draws_one_bar_and_no_figure(self):
        self.open_at(INDEX_TABS["charts"].url, 1500)

        drawn = self.browser.execute_script(
            "return getComputedStyle(document.querySelector("
            "  '#chart-expenses-container .highcharts-point')).fill;"
        )

        assert (drawn, self._texts(EXPENSE_PARTS)) == (TINT, [])

    def test_each_expense_bar_ends_in_its_whole_sum_and_share_in_the_muted_figure(
        self,
    ):
        for title, price in (("Big", 12345000), ("Small", 4115000)):
            ExpenseFactory(expense_type=ExpenseTypeFactory(title=title), price=price)
        drawn = {}
        for width in (1500, 360):
            self.open_at(INDEX_TABS["charts"].url, width)
            drawn[width] = self.browser.execute_script(
                f"const look = getComputedStyle(document.querySelector('{EXPENSE_PARTS}'));"
                " const chart = document.querySelector('#chart-expenses-container svg')"
                "  .getBoundingClientRect();"
                f" return {{look: [look.fill, look.fontSize, look.fontWeight],"
                f" inside: [...document.querySelectorAll('{EXPENSE_PARTS}')]"
                "  .every(f => f.getBoundingClientRect().right <= chart.right)};"
            )

        # the factory's own type, spent nothing, gets the last bar and no figure
        assert (self._texts(EXPENSE_PARTS), drawn) == (
            ["123.450€ · 75,0%", "41.150€ · 25,0%"],
            dict.fromkeys(
                (1500, 360), {"look": [INK_MUTED, "12px", "400"], "inside": True}
            ),
        )

    def test_the_money_axes_read_from_100_in_thousands_either_way(self):
        self._open_charts_with_two_types(1500)

        axes = [
            self._texts(f"#{chart} .highcharts-yaxis-labels text")
            for chart in (
                "chart-expenses-container",
                "chart-balance-container",
                "chart-incomes-expenses-container",
            )
        ]

        assert axes == [
            ["0", "0,1k", "0,2k", "0,3k", "0,4k"],
            ["-0,6k", "-0,4k", "-0,2k", "0"],
            ["0", "0,2k", "0,4k", "0,6k"],
        ]

    @time_machine.travel("1999-03-15")
    def test_the_current_month_draws_paler_and_the_months_after_it_gap(self):
        IncomeFactory(date=date(1999, 3, 1), price=50000)
        ExpenseFactory(date=date(1999, 12, 1), price=10000)
        self.open_at(INDEX_TABS["charts"].url, 1500)

        drawn = {
            chart: self.read_chart(
                chart,
                tooltip_at(2) + " return {y: c.series[0].points.map(p => p.y),"
                "  fills: c.series.map(s => [0, 2].map(x =>"
                "   getComputedStyle(s.points[x].graphic.element).fill)),"
                "  tip: tip[0]};",
            )
            for chart in ("chart-balance-container", "chart-incomes-expenses-container")
        }

        # December already holds an expense, so it draws
        assert drawn == {
            "chart-balance-container": {
                "y": [0, 0, 500, *[None] * 8, -100],
                "fills": [[TINT, TINT_FADED]],
                "tip": "Kovas (iki šiol)",
            },
            "chart-incomes-expenses-container": {
                "y": [0, 0, 500, *[None] * 8, 0],
                "fills": [[DATA_RGB, DATA_FADED], [HARM, HARM_FADED]],
                "tip": "Kovas (iki šiol)",
            },
        }

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

        tips = {
            chart: self.read_chart(
                chart,
                tooltip_at(0)
                + " return [getComputedStyle(c.tooltip.label.text.element).color,"
                "  ...tip];",
            )
            for chart in (
                "chart-expenses-container",
                "chart-balance-container",
                "chart-incomes-expenses-container",
            )
        }

        # in ink; the lines chart's tooltip gives the month's balance too
        assert tips == {
            "chart-expenses-container": [INK, "Big", "300€ · 75,0%"],
            "chart-balance-container": [INK, "Sausis", "Balansas: -400€"],
            "chart-incomes-expenses-container": [
                INK,
                "Sausis",
                "Pajamos: 0€",
                "Išlaidos: 400€",
                "Balansas: -400€",
            ],
        }

    def test_the_overview_panels_stand_in_three_columns_from_992_and_one_below(self):
        placed = {}
        for width in (992, 991):
            self.open_at(INDEX_TABS["overview"].url, width)
            a, b, c = self._boxes(".overview-grid__column")
            placed[width] = {
                "beside": a["top"] == b["top"] == c["top"]
                and a["right"] < b["left"]
                and b["right"] < c["left"],
                "stacked": a["bottom"] <= b["top"] and b["bottom"] <= c["top"],
                "middle_widest": b["width"] > a["width"]
                and round(a["width"]) == round(c["width"]),
            }

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
        # reads in the body face (sass.md *Type*); the groups centre over their columns
        looks = self.browser.execute_script(
            "const groups = document.querySelector('#table-balance thead tr').cells;"
            " const toggle = getComputedStyle(arguments[0]);"
            " return [toggle.borderTopStyle, toggle.borderTopColor,"
            " toggle.fontFamily.split(',')[0],"
            " ...[groups[1], groups[2]].map(c => getComputedStyle(c).textAlign)];",
            toggle,
        )

        assert looks == [
            "solid",
            HAIR,
            '"Segoe UI Variable Text"',
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
        # a funds table and the accounts table run wider than a phone's column; the
        # dev DB's longest fund and pension names
        IncomeFactory()
        SavingFactory(saving_type=SavingTypeFactory(title=LONGEST_FUND))
        PensionFactory(
            pension_type=PensionTypeFactory(title="Artea Ambicingas Index 16+")
        )
        overflow = {}
        for tab in INDEX_TABS:
            self.open_at(tab.url, 360)
            overflow[tab.name] = page_overflow(self.browser)
            if tab.name == "funds":
                scrolls = self.browser.execute_script(
                    "return [...document.querySelectorAll('.panel .table-responsive')]"
                    "  .map(box => box.scrollWidth > box.clientWidth);"
                )

        assert (overflow, scrolls) == (
            dict.fromkeys((tab.name for tab in INDEX_TABS), 0),
            [True, True],
        )

    def test_the_unnecessary_expenses_tip_opens_whole_under_its_header(self):
        # six types and Taupymas: a list taller than its table
        journal = JournalFactory()
        types = [ExpenseTypeFactory(title=f"Type {n}") for n in range(6)]
        journal.unnecessary_savings = True
        journal.unnecessary_expenses = json.dumps([t.pk for t in types])
        journal.save()
        read = {}
        for width in (1500, 360):
            self.open_at(INDEX_TABS["overview"].url, width)
            self.browser.execute_script(
                FIND_TIP + " tip.scrollIntoView({block: 'center'});", NO_INCOMES_TIP
            )
            hidden = self.browser.execute_script(TIP_BUBBLE, NO_INCOMES_TIP)
            self.browser.execute_script(FIND_TIP + " tip.focus();", NO_INCOMES_TIP)
            read[width] = (
                [hidden["box_scrolls"], hidden["page_overflow"]],
                self._tip_opens(NO_INCOMES_TIP),
                self.browser.execute_script(TIP_BUBBLE, NO_INCOMES_TIP),
            )

        whole = {
            "lines": 8,
            "whole": True,
            "below_its_header": True,
            "gap_is_8px": True,
            "in_the_window": True,
            "leaves_its_box": True,
            "box_scrolls": False,
            "page_overflow": 0,
        }
        assert read == dict.fromkeys((1500, 360), ([False, 0], True, whole))

    def test_a_tip_at_the_edge_of_a_scrolled_table_opens_whole_past_it(self):
        long = "Type 6, the long one of eight"
        for n in range(1, 9):
            ExpenseTypeFactory(title=long if n == 6 else f"Type {n}")
        tip = f".tip[data-tip='{long}']"
        self.open_at(INDEX_TABS["balance"].url, 360)
        scrolled = self.browser.execute_script(
            FIND_TIP + " tip.scrollIntoView({block: 'center', inline: 'end'});"
            " tip.focus({preventScroll: true});"
            " const box = tip.closest('.table-responsive');"
            " return [box.scrollLeft > 0,"
            "  box.scrollLeft + box.clientWidth < box.scrollWidth];",
            tip,
        )
        read = self.browser.execute_script(TIP_BUBBLE, tip)

        # scrolled, and not to its end, where a box fades its edge: that mask would
        # cut the bubble where it leaves the box
        assert (scrolled, read) == (
            [True, True],
            {
                "lines": 1,
                "whole": True,
                "below_its_header": True,
                "gap_is_8px": True,
                "in_the_window": True,
                "leaves_its_box": True,
                "box_scrolls": True,
                "page_overflow": 0,
            },
        )

    def test_a_tip_with_no_room_under_its_header_opens_over_it_and_the_dock(self):
        self.open_at(INDEX_TABS["overview"].url, 1500)
        find_header = (
            FIND_TIP + " const header = tip.closest('th').getBoundingClientRect();"
        )
        header_bottom = self.browser.execute_script(
            find_header + " return header.bottom;", NO_INCOMES_TIP
        )
        # the window ends 2px under the header, so the dock lies over it
        self.browser.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1500,
                "height": round(header_bottom) + 2,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        placed = self.browser.execute_script(
            find_header + " tip.focus({preventScroll: true});"
            " const middle = (header.left + header.right) / 2;"
            " const dock = document.querySelector('.quick-add').getBoundingClientRect();"
            " const at = y => document.elementsFromPoint(middle, y);"
            " return [innerHeight - header.bottom < 3,"
            "  at(dock.top + 3).some(e => e.matches('.quick-add')),"
            "  at(dock.top + 3)[0] === tip, at(header.top - 20)[0] === tip];",
            NO_INCOMES_TIP,
        )

        # no room under the header; 3px into the dock the bubble lies over it, and
        # 20px over the header it is drawn too
        assert placed == [True, True, True, True]

    def test_a_browser_without_anchoring_opens_a_tip_against_its_trigger(self):
        journal = JournalFactory()
        journal.unnecessary_savings = True
        journal.save()
        AccountWorthFactory()
        self.open_at(INDEX_TABS["overview"].url, 1500)
        queries = self.browser.execute_script(NO_ANCHORING)
        read = {}
        for name, tip in (("check", "#accounts td .tip"), ("list", NO_INCOMES_TIP)):
            self.browser.execute_script(
                FIND_TIP + " tip.scrollIntoView({block: 'center'});"
                " tip.focus({preventScroll: true});",
                tip,
            )
            read[name] = self.browser.execute_script(TIP_AGAINST_ITS_TRIGGER, tip)

        # one anchored query and two without; a Check on one line beside its
        # account, the list's two lines under its header
        against = {"position": "absolute", "gap_is_8px": True}
        against |= {"middle_on_its_trigger": True}
        assert (queries, read) == (
            3,
            {
                "check": against | {"side": "beside", "lines": 1},
                "list": against | {"side": "under", "lines": 2},
            },
        )

    def test_every_tip_opens_on_focus_in_the_paper_look(self):
        journal = JournalFactory()
        journal.unnecessary_savings = True
        journal.save()
        AccountWorthFactory()
        self.open_at(INDEX_TABS["overview"].url, 1500)
        # a header's icon (its link takes the focus), a body cell's name, a header's
        # list
        tips = {
            "refresh": ("#accounts th .tip", "#accounts th .tip a"),
            "check": ("#accounts td .tip", "#accounts td .tip"),
            "unnecessary": (NO_INCOMES_TIP, NO_INCOMES_TIP),
        }
        looks = {}
        for name, (tip, focused) in tips.items():
            self.browser.execute_script(
                "document.querySelector(arguments[0]).focus();", focused
            )
            looks[name] = [
                self._tip_opens(tip),
                *self.browser.execute_script(
                    FIND_TIP + " const b = getComputedStyle(tip, '::before');"
                    " return [b.backgroundColor, b.color, b.fontFamily, b.textShadow,"
                    "  b.boxShadow, getComputedStyle(tip, '::after').content];",
                    tip,
                ),
            ]

        # ink on paper in the body face, no shadow, and no arrow after it
        assert looks == dict.fromkeys(
            tips, [True, INK, PAPER, BODY_FACE, "none", "none", "none"]
        )

    def test_the_funds_tables_start_their_figures_at_one_x(self):
        # the longest fund name, beside a short pension name
        SavingFactory(saving_type=SavingTypeFactory(title=LONGEST_FUND))
        PensionFactory(pension_type=PensionTypeFactory(title="P"))
        columns = {}
        for width in (1500, 1280):
            self.open_at(INDEX_TABS["funds"].url, width)
            # per table: the name column's width, the second column's left x
            columns[width] = self.browser.execute_script(
                "return [...document.querySelectorAll('.panel table.main')].map(t => {"
                " const name = t.querySelector('tbody td');"
                " return [name.getBoundingClientRect().width,"
                " name.nextElementSibling.getBoundingClientRect().left]; });"
            )
            if width == 1500:
                lines = self.browser.execute_script(
                    "const range = document.createRange();"
                    " range.selectNodeContents("
                    "document.querySelector('#savings tbody td'));"
                    " return range.getClientRects().length;"
                )

        assert {w: c[0] for w, c in columns.items()} == {
            w: c[1] for w, c in columns.items()
        }
        assert lines == 1

    def test_funds_tables_rule_where_each_column_group_starts(self):
        SavingFactory()
        PensionFactory()
        self.open_at(INDEX_TABS["funds"].url, 1500)

        # per table and row, each cell with a left rule, by position from 1, and its
        # colour; no width: a scaled display snaps 1px to a device pixel
        ruled = self.browser.execute_script(
            "return [...document.querySelectorAll('.panel table.main')].map(t =>"
            " [...t.querySelectorAll('tr')].map(tr =>"
            " [...tr.children].flatMap((c, i) => {"
            " const s = getComputedStyle(c);"
            " return s.borderLeftStyle === 'solid' ? [[i + 1, s.borderLeftColor]] : [];"
            " })));"
        )
        # the band: five group heads, both Pervesta (not Parduota), row three's
        # columns 2, 4, 6, 10, 12; the foot's market value spans two cells
        band = [
            [[i, HAIR] for i in (2, 3, 4, 5, 6)],
            [[1, HAIR], [2, HAIR]],
            [[i, HAIR] for i in (2, 4, 6, 10, 12)],
        ]
        row = [[i, HAIR_SOFT] for i in (2, 4, 6, 10, 12)]
        foot = [[i, HAIR_SOFT] for i in (2, 4, 6, 10, 11)]
        assert ruled == [[*band, row, foot]] * 2

    def _tip_opens(self, selector: str) -> bool:
        # its box, not its opacity: a minimized Chrome draws no frame, so the fade
        # never runs
        return self.browser.execute_script(
            "return getComputedStyle("
            "  document.querySelector(arguments[0]), '::before').display === 'block';",
            selector,
        )

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

    def _boxes(self, selector: str) -> list[dict]:
        return self.browser.execute_script(
            "return [...document.querySelectorAll(arguments[0])].map(e => {"
            " const r = e.getBoundingClientRect();"
            " return {top: r.top, bottom: r.bottom, left: r.left, right: r.right,"
            "  width: r.width}; });",
            selector,
        )

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
