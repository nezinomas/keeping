import re
from datetime import date

import pytest
from django.urls import reverse

from ....core.tests.utils import tab_fragment, view_for
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...views import Forecast

pytestmark = pytest.mark.django_db


def test_empty_forecast_reads_dashes_under_the_year_strips_titles(client_logged):
    url = reverse("bookkeeping:forecast")
    content = client_logged.get(url).content.decode("utf-8")

    # in its scroll box; the Panel's body carries the toggle, not the table
    assert re.findall(
        r'<div class="table-responsive">\s*<table\b([^>]*)>', content
    ) == [' class="main striped hover"']
    assert re.findall(r"<th>([^<]*)</th>", content) == [
        "1999 pradžioje",
        "1999 pabaigoje",
        "Balansas",
    ]
    assert content.count('<td class="main__figure">-</td>') == 3
    assert "data-sign" not in content


def test_forecast_panel_title_is_one_control_whose_chevron_turns_with_the_forecast(
    client_logged,
):
    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))

    # the title's word and its chevron are one control; the Panel holds the `open`
    # both it and the body read
    panels = [
        (re.findall(r'(@click|hx-[\w-]+)="([^"]*)"', control), icon, body)
        for control, icon, body in re.findall(
            r'<section class="panel panel--table" x-data="\{ open:false \}">\s*'
            r'<h2 class="panel__title"><a role="button" class="panel__toggle"'
            r"([^>]*)>Prognozė <i ([^>]*)></i></a></h2>\s*(.*?)\s*</section>",
            content,
            re.S,
        )
    ]

    assert panels == [
        (
            [
                ("@click", "open = ! open"),
                ("hx-get", reverse("bookkeeping:forecast")),
                ("hx-target", "#forecast"),
                ("hx-trigger", "click once"),
                ("hx-indicator", "#indicator"),
            ],
            "class=\"bi\" :class=\"open ? 'bi-chevron-up' : 'bi-chevron-down'\"",
            '<div id="forecast" x-show="open"></div>',
        )
    ]


def test_forecast_reads_the_month_of_the_views_today(rf, main_user):
    IncomeFactory(price=1000, date=date(1999, 1, 5))
    ExpenseFactory(price=200, date=date(1999, 1, 6))
    ExpenseFactory(price=300, date=date(1999, 2, 6))
    view = view_for(rf, main_user, Forecast)
    # apart from the clock, so a read of the clock shows
    view.today = date(1999, 2, 10)

    assert view.get_context_data()["data"] == [0, -1500, -1500]
