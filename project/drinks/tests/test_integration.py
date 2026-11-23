from datetime import date

import pytest
from parameterized import parameterized
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from ...core.tests.test_integration_browser import HARM, INK_MUTED, Browser
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db

OVERVIEW_CHART = "#chart-overview-container"
HEAVY_DAY = "Rizikingo vartojimo diena: > 6 Std Av"


def _rule_labels(browser, scope, read):
    """`read`, a JS function of a label's span, for each chart rule label in scope."""
    return browser.execute_script(
        "return [...document.querySelectorAll("
        f"  arguments[0] + ' .highcharts-plot-line-label span')].map({read});",
        scope,
    )


@pytest.mark.webtest
class DrinksQuickAdd(Browser):
    def test_more_button_opens_the_modal_without_replacing_it(self):
        # htmx.ajax() has no source element, so it reads its swap off the target:
        # an "outer" swap replaces #mainModal and the Alpine scope every modal reads
        self.open("/drinks/")

        self.browser.find_element(By.CSS_SELECTOR, ".quick-add__pill").click()
        more = WebDriverWait(self.browser, 10).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, ".quick-add__sheet form > button[type=button]")
            )
        )
        more.click()
        self.wait_until_idle()

        assert self.browser.find_elements(By.ID, "mainModal")
        assert self.browser.find_elements(By.CSS_SELECTOR, "#mainModal .modal-form")


@pytest.mark.webtest
class DrinksChartAxisTitle(Browser):
    @parameterized.expand([(1280,), (360,)])
    def test_axis_title_is_written_as_in_a_sentence_inside_the_chart(self, width):
        chart = f"{OVERVIEW_CHART} .highcharts-root"
        title = f"{OVERVIEW_CHART} .highcharts-yaxis .highcharts-axis-title"
        self.open_at("/drinks/", width)

        face = self.browser.execute_script(
            "const t = document.querySelector(arguments[0]);"
            "const s = getComputedStyle(t);"
            "const r = t.getBoundingClientRect();"
            "const c = document.querySelector(arguments[1])"
            "  .getBoundingClientRect();"
            "return [s.fontSize, s.letterSpacing, s.textTransform,"
            "  r.top >= c.top && r.right <= c.right];",
            title,
            chart,
        )
        assert face == ["12px", "normal", "none", True]


@pytest.mark.webtest
class DrinksChartRuleLabel(Browser):
    @parameterized.expand(
        [
            ("habits", "#tab_content", 1280, [HEAVY_DAY, HEAVY_DAY]),
            ("habits", "#tab_content", 360, ["> 6 Std Av", "> 6 Std Av"]),
            ("risk", "#chart-heavy-container", 1280, ["Mažos rizikos riba: 3"]),
            ("risk", "#chart-heavy-container", 360, ["3"]),
        ]
    )
    def test_heavy_day_label_fits_inside_its_chart_at_each_width(
        self, tab, scope, width, texts
    ):
        # three heavy days in a month, or the Risk chart's axis stops below its rule
        for day in (1, 2, 3):
            DrinkFactory(date=date(1999, 1, day), stdav=8)
        self.open_at("/drinks/", width)
        self.click_tab(tab)

        labels = _rule_labels(
            self.browser,
            scope,
            "s => {"
            "  const r = s.getBoundingClientRect();"
            "  const c = s.closest('.highcharts-container').getBoundingClientRect();"
            "  return [s.textContent, r.left >= c.left && r.right <= c.right];"
            "}",
        )
        assert labels == [[text, True] for text in texts]

    def test_rule_label_wears_its_rule_state(self):
        # a week past the high-risk threshold, or Highcharts drops both rules off the axis
        DrinkFactory(stdav=30)
        self.open("/drinks/")
        self.click_tab("risk")

        labels = _rule_labels(
            self.browser,
            "#chart-weekly-container",
            "s => [s.textContent.split(':')[0], getComputedStyle(s).color]",
        )

        assert labels == [
            ["Mažos rizikos riba", INK_MUTED],
            ["Aukštos rizikos riba", HARM],
        ]


@pytest.mark.webtest
class DrinksHistoryDataLabels(Browser):
    # the forecast's hollow bar prints no figure at any width
    @parameterized.expand(
        [(1280, [True, True, False], True), (360, [False] * 3, False)]
    )
    def test_data_labels_drop_where_a_year_is_too_narrow_for_them(
        self, width, enabled, drawn
    ):
        # ten years: about 23 px a year at 360, five times that at 1280
        for year in range(1990, 2000):
            DrinkFactory(date=date(year, 1, 1))
        self.open_at("/drinks/", width)
        self.click_tab("history")

        shown = self.read_chart(
            "chart-summary-container",
            "return [c.series.map(s => s.options.dataLabels.enabled),"
            "  !!c.container.querySelector('.highcharts-data-label')];",
        )
        assert shown == [enabled, drawn]


@pytest.mark.webtest
class DrinksTrendLimitRule(Browser):
    @parameterized.expand([(lambda: None, []), (DrinkTargetFactory, ["Riba: 100"])])
    def test_limit_rule_is_drawn_only_with_a_drink_target(self, target, expected):
        DrinkFactory()
        target()
        self.open("/drinks/")
        self.click_tab("trends")

        labels = _rule_labels(
            self.browser, "#chart-trend-container", "s => s.textContent"
        )
        assert labels == expected


@pytest.mark.webtest
class DrinksChartTooltip(Browser):
    def test_profile_tooltip_heads_with_the_day_at_the_tooltip_size(self):
        DrinkFactory()
        self.open("/drinks/")
        self.click_tab("habits")

        head = self.read_chart(
            "chart-weekday-container",
            "c.tooltip.refresh(c.series.map(s => s.points[0]));"
            "const t = c.tooltip.container.querySelector('.highcharts-tooltip span');"
            "return [t.innerHTML.split('<br>')[0], getComputedStyle(t).fontSize];",
        )

        assert head == ["Pirmadienis", "12px"]


@pytest.mark.webtest
class DrinksChartBarFigures(Browser):
    def test_bar_figure_is_muted(self):
        DrinkFactory()
        self.open("/drinks/")

        fill = self.browser.execute_script(
            "const t = document.querySelector(arguments[0]);"
            "return getComputedStyle(t).fill;",
            f"{OVERVIEW_CHART} .highcharts-data-labels.highcharts-column-series text",
        )

        assert fill == INK_MUTED


@pytest.mark.webtest
class DrinksCalendarTooltip(Browser):
    @parameterized.expand(
        [
            ("focus", "day.focus();", "day.blur();"),
            # off every day: the month label has no data-label, so a mouseover hides
            # the tooltip and a move over the label keeps it hidden
            (
                "hover",
                "day.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));",
                "label.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));"
                " label.dispatchEvent(new MouseEvent('mousemove', {bubbles: true}));",
            ),
        ]
    )
    def test_tooltip_reads_its_day_only_while_the_day_holds_it(self, _, show, hide):
        DrinkFactory()
        self.open("/drinks/")
        day = self.browser.find_element(By.CSS_SELECTOR, ".mini i[data-label]:not(.l0)")

        seen = self.browser.execute_script(
            """
            const day = arguments[0];
            const tooltip = document.getElementById('heat-tooltip');
            const label = document.querySelector('.heat-card .mlabel');
            const read = () => [
                tooltip.checkVisibility(),
                [...tooltip.children].map(line => line.textContent),
            ];
            // a handler that throws reports to window, not to dispatchEvent
            const errors = [];
            window.addEventListener('error', e => errors.push(e.message));
            const before = tooltip.checkVisibility();
            """
            + show
            + """
            const over = read();
            """
            + hide
            + """
            return [
                day.dataset.label.split('\\n'), before, over,
                tooltip.checkVisibility(), errors,
            ];
            """,
            day,
        )

        lines, before, (shown, text), after, errors = seen
        assert len(lines) == 3
        assert (before, shown, text, after, errors) == (False, True, lines, False, [])

    def test_tooltip_shows_a_label_as_text_not_markup(self):
        DrinkFactory()
        self.open("/drinks/")
        day = self.browser.find_element(By.CSS_SELECTOR, ".mini i[data-label]")

        lines, tags = self.browser.execute_script(
            """
            const day = arguments[0];
            const tooltip = document.getElementById('heat-tooltip');
            day.dataset.label = '<b>1999-01-05</b>\\n<img src=x>';
            day.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
            return [
                [...tooltip.children].map(line => line.textContent),
                tooltip.querySelectorAll('b, img').length,
            ];
            """,
            day,
        )

        assert (lines, tags) == (["<b>1999-01-05</b>", "<img src=x>"], 0)

    def test_tooltip_wears_the_calendars_face(self):
        DrinkFactory()
        self.open("/drinks/")
        day = self.browser.find_element(By.CSS_SELECTOR, ".mini i[data-label]")

        shown, face, calendar_face = self.browser.execute_script(
            """
            const tooltip = document.getElementById('heat-tooltip');
            const face = el => getComputedStyle(el).fontFamily;
            arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
            return [!tooltip.hidden, face(tooltip), face(document.querySelector('.mlabel'))];
            """,
            day,
        )

        assert (shown, face) == (True, calendar_face)

    def test_tooltip_follows_its_day_when_the_calendar_scrolls_under_the_mouse(self):
        DrinkFactory()
        # a phone width, so the heat body scrolls sideways; the events are
        # dispatched, since a minimized window takes no Selenium hover
        self.open_at("/drinks/", 360)
        day = self.browser.find_element(By.CSS_SELECTOR, ".mini i[data-label]")

        placed = self.browser.execute_script(
            """
            const day = arguments[0];
            const body = document.querySelector('.heat-body');
            const tooltip = document.getElementById('heat-tooltip');
            const centre = el => {
                const rect = el.getBoundingClientRect();
                return rect.left + rect.width / 2;
            };
            day.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
            body.scrollLeft = 60;
            day.dispatchEvent(new MouseEvent('mousemove', {bubbles: true}));
            return {
                scrolled: body.scrollLeft,
                off_centre: Math.round(centre(tooltip) - centre(day)),
                gap_above: Math.round(
                    day.getBoundingClientRect().top
                    - tooltip.getBoundingClientRect().bottom
                ),
            };
            """,
            day,
        )

        # the skin lifts the tooltip 8px off its day
        assert placed == {"scrolled": 60, "off_centre": 0, "gap_above": 8}


@pytest.mark.webtest
class DrinksOverviewOnAPhone(Browser):
    # the scrolling box around a table or the calendar's day columns
    BOX = "document.querySelector(arguments[0]).parentElement"

    def test_breakdown_scrolls_inside_its_panel_not_the_page(self):
        # five-figure totals make the breakdown wider than a 360 panel
        DrinkFactory(stdav=50_000)
        self.open_at("/drinks/", 360)

        overflow = self.browser.execute_script(
            f"const box = {self.BOX};"
            " const page = document.documentElement;"
            " return {page_overflow: page.scrollWidth - page.clientWidth,"
            "  box_scrolls: getComputedStyle(box).overflowX,"
            "  table_wider: box.scrollWidth > box.clientWidth};",
            "#breakdown table",
        )

        assert overflow == {
            "page_overflow": 0,
            "box_scrolls": "auto",
            "table_wider": True,
        }

    @parameterized.expand(
        [
            ("#breakdown table", 360, False, True),
            ("#breakdown table", 360, True, False),
            ("#breakdown table", 1500, False, False),
            (".heat-daycol", 360, False, True),
        ]
    )
    def test_box_fades_its_edge_only_while_more_lies_past_it(
        self, inside, width, scroll_to_end, fade
    ):
        DrinkFactory(stdav=50_000)
        self.open_at("/drinks/", width)
        self.browser.execute_script(
            f"const box = {self.BOX};"
            " if (arguments[1]) box.scrollLeft = box.scrollWidth;",
            inside,
            scroll_to_end,
        )
        self.wait_two_frames()

        faded = self.browser.execute_script(
            f"return getComputedStyle({self.BOX}).maskImage !== 'none';",
            inside,
        )
        assert faded is fade


@pytest.mark.webtest
class DrinksDataOnAPhone(Browser):
    def test_quantity_keeps_its_unit_on_its_line(self):
        DrinkFactory()
        self.open_at("/drinks/", 360)
        self.click_tab("data")

        lines = self.browser.execute_script(
            "const range = document.createRange();"
            " range.selectNodeContents("
            "  document.querySelector('.main tbody tr').cells[2]);"
            " const tops = [...range.getClientRects()].map(r => Math.round(r.top));"
            " return [range.toString().trim(), new Set(tops).size];"
        )

        assert lines == ["0,4 vnt", 1]
