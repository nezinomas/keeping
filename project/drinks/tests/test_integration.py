import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from ...core.tests.test_integration_browser import Browser
from .factories import DrinkFactory

pytestmark = pytest.mark.django_db

OVERVIEW_CHART = "#chart-overview-container"
INK_MUTED = "rgb(90, 106, 117)"  # --skin-ink-muted


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
    def test_axis_title_takes_its_face_by_width_inside_the_chart(self):
        chart = f"{OVERVIEW_CHART} .highcharts-root"
        title = f"{OVERVIEW_CHART} .highcharts-yaxis .highcharts-axis-title"
        self.addCleanup(
            self.browser.execute_cdp_cmd, "Emulation.clearDeviceMetricsOverride", {}
        )
        for width, size, spacing, transform in (
            (1280, "12px", "1.44px", "uppercase"),
            (360, "10.88px", "0.6528px", "none"),
        ):
            with self.subTest(width=width):
                self.browser.execute_cdp_cmd(
                    "Emulation.setDeviceMetricsOverride",
                    {
                        "width": width,
                        "height": 900,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    },
                )
                self.browser.get(f"{self.live_server_url}/drinks/")
                self.wait_until_idle()
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

                assert face == [size, spacing, transform, True]


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
