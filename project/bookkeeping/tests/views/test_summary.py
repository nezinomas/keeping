from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ..helper import script_json

pytestmark = pytest.mark.django_db


@time_machine.travel("2000-1-1")
@pytest.mark.parametrize(
    "script_id, expected",
    [
        pytest.param(
            "chart-balance-data",
            {"categories": [1999, 2000], "incomes": [1, 2], "expenses": [3, 4]},
            id="balance",
        ),
        pytest.param(
            "chart-incomes-data",
            {"categories": [1999, 2000], "incomes": [1 / 12, 2], "salary": [1 / 12, 2]},
            id="incomes",
        ),
    ],
)
def test_view_renders_the_data_of_its_charts(client_logged, script_id, expected):
    for year, income, expense in ((1999, 1, 3), (2000, 2, 4)):
        IncomeFactory(date=date(year, 1, 1), price=income)
        ExpenseFactory(date=date(year, 1, 1), price=expense)

    content = client_logged.get(reverse("bookkeeping:summary")).content.decode()
    data = script_json(content, script_id)

    assert {key: data[key] for key in expected} == expected


def test_no_data(client_logged):
    url = reverse("bookkeeping:summary")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Trūksta duomenų. Reikia bent dviejų metų duomenų." in actual


def test_view_summary_one_year_data(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse("bookkeeping:summary")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Trūksta duomenų. Reikia bent dviejų metų duomenų." in actual
