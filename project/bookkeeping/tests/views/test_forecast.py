import re
from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....core.tests.utils import tab_fragment, view_for
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...views import Forecast

pytestmark = pytest.mark.django_db


def test_empty_forecast_totals_row_reads_dashes(client_logged):
    url = reverse("bookkeeping:forecast")
    content = client_logged.get(url).content.decode("utf-8")

    assert '<tfoot x-show="open">' in content
    assert content.count('<td class="main__figure">-</td>') == 3
    assert "data-sign" not in content


def test_forecast_sends_the_anonymous_to_the_login(client):
    url = reverse("bookkeeping:forecast")
    response = client.get(url)

    assert response.url == f"{reverse('users:login')}?next={url}"


def test_year_strip_expander_draws_a_chevron_that_turns_with_the_forecast(
    client_logged,
):
    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))

    # the chevron reads the strip table's own `open`
    assert re.findall(
        r'<table class="main striped hover" x-data="\{ open:false \}">.*?'
        r'<a\b[^>]*class="button-expand"[^>]*>\s*<i ([^>]*)></i>',
        content,
        re.S,
    ) == ["class=\"bi\" :class=\"open ? 'bi-chevron-up' : 'bi-chevron-down'\""]


@time_machine.travel("1999-02-10")
def test_forecast_reads_the_month_of_the_views_today(rf, main_user):
    IncomeFactory(price=1000, date=date(1999, 1, 5))
    ExpenseFactory(price=200, date=date(1999, 1, 6))
    ExpenseFactory(price=300, date=date(1999, 2, 6))
    view = view_for(rf, main_user, Forecast)

    assert view.get_context_data()["data"] == [0, -1500, -1500]
