from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from ...savings.factories import SavingFactory
from .. import views
from ..services.detailed import DetailedService

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                Detailed
# ---------------------------------------------------------------------------------------
def test_view_detailed_func():
    view = resolve('/detailed/')

    assert views.Detailed == view.func.view_class


def test_view_detailed_200(client_logged):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_detailed_302(client):
    url = reverse('bookkeeping:detailed')
    response = client.get(url)

    assert response.status_code == 302


def test_view_detailed_rendered_expenses(client_logged, expenses):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Expense Name" in content
    assert "Išlaidos / Expense Type" in content


def test_view_detailed_no_expenses(client_logged):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / " not in content


def test_view_detailed_no_expenses_with_types(client_logged):
    ExpenseTypeFactory()

    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / Expense Type" not in content


def test_view_detailed_with_incomes(client_logged):
    IncomeFactory()

    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Pajamos</th>" in content
    assert "Income Type" in content


def test_view_detailed_no_incomes(client_logged):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "<th>Pajamos</th>" not in content
    assert "Income Type</td>" not in content


def test_view_detailed_no_savings(client_logged):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "<th>Taupymas</th>" not in content


def test_view_detailed_with_savings(client_logged):
    SavingFactory()

    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Taupymas</th>" in content
    assert "Savings</td>" in content


@freeze_time('1999-01-01')
def test_view_summary_balance_years(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_view_summary_incomes_avg(client_logged):
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Kita')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=10.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=2.0,
        income_type=IncomeTypeFactory(title='Kt')
    )

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_income_avg'] == [2.0, 12.0]


def test_view_summary_no_data(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


def test_view_summary_one_year_data(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


# ---------------------------------------------------------------------------------------
#                                                                         Detailed Helper
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _income():
    return [
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(1)},
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(4)},
        {'date': date(1999, 6, 1), 'title': 'B', 'sum': Decimal(2)},
    ]


def test_sum_detailed_rows(_income):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5)},
        {'date': date(1999, 6, 1), 'sum': Decimal(2)},
    ]
    actual = DetailedService(1999)._sum_detailed(_income, 'date', ['sum'])

    assert expect == actual


def test_sum_detailed_columns(_income):
    expect = [
        {'title': 'A', 'sum': Decimal(5)},
        {'title': 'B', 'sum': Decimal(2)},
    ]

    actual = DetailedService(1999)._sum_detailed(_income, 'title', ['sum'])

    assert expect == actual
