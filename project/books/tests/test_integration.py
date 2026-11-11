from datetime import date

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from ...core.tests.test_integration_browser import Browser
from .factories import BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Books(Browser):
    def test_overview_chart_draws_on_load_and_after_a_tab_swap(self):
        self.assert_overview_chart_redraws(
            reverse("books:index"), "chart-finished-container"
        )

    def test_goal_figure_is_printed_only_on_a_wide_chart(self):
        BookFactory(ended=date(1999, 1, 31))
        BookTargetFactory(quantity=1)
        # the Goal's rule is the bullet's own, drawn at every width
        for width, figure in ((1280, True), (360, False)):
            with self.subTest(width=width):
                self.open_at(reverse("books:index"), width)
                drawn = self.read_chart(
                    "chart-finished-container",
                    "return [c.series[1].visible,"
                    "  !!c.series[0].points[0].targetGraphic];",
                )

                assert drawn == [figure, True]

    def test_tooltip_names_the_goal_only_on_a_phone(self):
        BookFactory(ended=date(1998, 1, 31))
        BookFactory(ended=date(1999, 1, 31))
        BookTargetFactory(quantity=5)
        # a year with no Goal names none
        for width, year, expected in (
            (1280, 1999, ""),
            (360, 1998, "1998Perskaitytos: 1"),
            (360, 1999, "1999Perskaitytos: 1Tikslas: 5"),
        ):
            with self.subTest(width=width, year=year):
                self.open_at(reverse("books:index"), width)
                bar = self.browser.find_elements(
                    By.CSS_SELECTOR,
                    "#chart-finished-container .highcharts-bullet-series"
                    " .highcharts-point",
                )[year - 1998]
                tip = self.read_chart(
                    "chart-finished-container",
                    "const r = arguments[1].getBoundingClientRect();"
                    "const at = {bubbles: true, clientX: r.x + r.width / 2,"
                    "  clientY: r.y + r.height / 2};"
                    "arguments[1].dispatchEvent(new MouseEvent('mouseover', at));"
                    "arguments[1].dispatchEvent(new MouseEvent('mousemove', at));"
                    "return c.tooltip.isHidden === false"
                    "  ? c.tooltip.container.querySelector('.highcharts-tooltip span')"
                    "    .textContent : '';",
                    bar,
                )

                assert tip == expected
