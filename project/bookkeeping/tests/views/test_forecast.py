from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....core.tests.utils import view_for
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...views import Forecast

pytestmark = pytest.mark.django_db


def test_empty_forecast_totals_row_reads_dashes(client_logged):
    url = reverse("bookkeeping:forecast")
    content = client_logged.get(url).content.decode("utf-8")

    assert '<tfoot x-show="open">' in content
    assert content.count("<th>-</th>") == 2
    assert '<th data-sign="gain">-</th>' in content


def test_302(client):
    url = reverse("bookkeeping:forecast")
    response = client.get(url)

    assert response.status_code == 302


@time_machine.travel("1999-02-10")
def test_forecast_reads_the_month_of_the_views_today(rf, main_user):
    IncomeFactory(price=1000, date=date(1999, 1, 5))
    ExpenseFactory(price=200, date=date(1999, 1, 6))
    ExpenseFactory(price=300, date=date(1999, 2, 6))
    view = view_for(rf, main_user, Forecast)

    assert view.get_context_data()["data"] == [0, -1500, -1500]
