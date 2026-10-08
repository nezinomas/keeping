from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....incomes.tests.factories import IncomeFactory
from ....savings.tests.factories import SavingFactory
from ..helper import script_json

pytestmark = pytest.mark.django_db


def test_view_no_logged_user(client):
    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client.get(url)

    assert response.status_code == 302


@time_machine.travel("2000-1-1")
@pytest.mark.parametrize(
    "incomes, savings, expected",
    [
        pytest.param(
            {2000: 1},
            {},
            {"categories": [1999, 2000]},
            id="categories",
        ),
        pytest.param(
            {1999: 1, 2000: 2},
            {},
            {"incomes": [1, 2]},
            id="incomes",
        ),
        pytest.param({1999: 1}, {}, {"incomes": [1, 0]}, id="incomes_one_empty_year"),
        pytest.param({}, {1999: 1, 2000: 2}, {"savings": [1, 2]}, id="savings"),
        pytest.param({}, {1999: 1}, {"savings": [1, 0]}, id="savings_one_empty_year"),
        pytest.param(
            {1999: 10},
            {1999: 1},
            {
                "categories": [1999, 2000],
                "incomes": [10, 0],
                "savings": [1, 0],
                "percents": [10, 0],
            },
            id="percents",
        ),
    ],
)
def test_view_renders_its_chart_data(client_logged, incomes, savings, expected):
    for year, price in incomes.items():
        IncomeFactory(date=date(year, 1, 1), price=price)
    for year, price in savings.items():
        SavingFactory(date=date(year, 1, 1), price=price, fee=0)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    content = client_logged.get(url).content.decode()
    data = script_json(content, "chart-data")

    assert {key: data[key] for key in expected} == expected
    assert "<th>1999</th>" in content
