from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from .. import views

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                 Summary
# ---------------------------------------------------------------------------------------
def test_view_summary_func():
    view = resolve('/summary/')

    assert views.Summary == view.func.view_class


def test_view_summary_200(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_view_summary_salary_avg(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_data_avg'] == [1.0, 10.0]


@freeze_time('1999-01-01')
def test_view_summary_salary_years(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_categories'] == [1998, 1999]


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

