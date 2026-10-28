import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from ...core.tests.test_integration_browser import Browser
from .factories import DrinkFactory

pytestmark = pytest.mark.django_db

OVERVIEW_CHART = "#chart-overview-container"
INK_MUTED = "rgb(90, 106, 117)"  # --skin-ink-muted
HARM = "rgb(125, 39, 51)"  # --skin-harm


@pytest.mark.webtest
class DrinksQuickAdd(Browser):
    def test_more_button_opens_the_modal_without_replacing_it(self):
        # htmx.ajax() has no source element, so it reads its swap off the target:
        # an "outer" swap replaces #mainModal and the Alpine scope every modal reads
        self.browser.get(f"{self.live_server_url}/drinks/")
        self.wait_until_idle()

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
    def test_axis_title_is_written_as_in_a_sentence_inside_the_chart(self):
        chart = f"{OVERVIEW_CHART} .highcharts-root"
        title = f"{OVERVIEW_CHART} .highcharts-yaxis .highcharts-axis-title"
        for width in (1280, 360):
            with self.subTest(width=width):
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
    def test_heavy_day_label_fits_inside_its_chart_at_each_width(self):
        DrinkFactory(stdav=8)
        for width, text in (
            (1280, "Rizikingo vartojimo diena: > 6 Std Av"),
            (360, "> 6 Std Av"),
        ):
            with self.subTest(width=width):
                self.open_at("/drinks/", width)
                self.browser.find_element(By.ID, "tab-habits").click()
                self.wait_until_idle()
                labels = self.browser.execute_script(
                    "return [...document.querySelectorAll("
                    "  '.highcharts-plot-line-label span')].map(s => {"
                    "  const r = s.getBoundingClientRect();"
                    "  const c = s.closest('.highcharts-container')"
                    "    .getBoundingClientRect();"
                    "  return [s.textContent, r.left >= c.left && r.right <= c.right];"
                    "});"
                )

                assert labels == [[text, True], [text, True]]

    def test_rule_label_wears_its_rule_state(self):
        # a week past the high-risk threshold, or Highcharts drops both rules off the axis
        DrinkFactory(stdav=30)
        self.browser.get(f"{self.live_server_url}/drinks/")
        self.wait_until_idle()
        self.browser.find_element(By.ID, "tab-risk").click()
        self.wait_until_idle()

        labels = self.browser.execute_script(
            "return [...document.querySelectorAll("
            "  '#chart-weekly-container .highcharts-plot-line-label span')]"
            "  .map(s => [s.textContent.split(':')[0], getComputedStyle(s).color]);"
        )

        assert labels == [
            ["Mažos rizikos riba", INK_MUTED],
            ["Aukštos rizikos riba", HARM],
        ]


@pytest.mark.webtest
class DrinksChartTooltip(Browser):
    def test_profile_tooltip_heads_with_the_day_at_the_tooltip_size(self):
        DrinkFactory()
        self.browser.get(f"{self.live_server_url}/drinks/")
        self.wait_until_idle()
        self.browser.find_element(By.ID, "tab-habits").click()
        self.wait_until_idle()

        head = self.browser.execute_script(
            "const c = Highcharts.charts.find("
            "  c => c && c.renderTo.id === 'chart-weekday-container');"
            "c.tooltip.refresh(c.series.map(s => s.points[0]));"
            "const t = c.tooltip.container.querySelector('.highcharts-tooltip span');"
            "return [t.innerHTML.split('<br>')[0], getComputedStyle(t).fontSize];"
        )

        assert head == ["Pirmadienis", "12px"]


@pytest.mark.webtest
class DrinksChartBarFigures(Browser):
    def test_bar_figure_is_muted(self):
        DrinkFactory()
        self.browser.get(f"{self.live_server_url}/drinks/")
        self.wait_until_idle()

        fill = self.browser.execute_script(
            "const t = document.querySelector(arguments[0]);"
            "return getComputedStyle(t).fill;",
            f"{OVERVIEW_CHART} .highcharts-data-labels.highcharts-column-series text",
        )

        assert fill == INK_MUTED
