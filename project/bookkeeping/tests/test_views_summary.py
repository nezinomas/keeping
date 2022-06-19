from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve('/summary/')

    assert views.Summary == view.func.view_class


def test_200(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_salary_avg(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_data_avg'] == [1.0, 10.0]


@freeze_time('1999-01-01')
def test_salary_years(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_balance_years(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_incomes_avg(client_logged):
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


def test_no_data(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.context['records'] == 0
    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


def test_one_year_data(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.context['records'] == 1
    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


def test_view_context(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert 'records' in actual
    assert 'balance_categories' in actual
    assert 'balance_income_data' in actual
    assert 'balance_income_avg' in actual
    assert 'balance_expense_data' in actual
    assert 'salary_categories' in actual
    assert 'salary_data_avg' in actual


@freeze_time('1999-1-1')
def test_view_only_incomes(client_logged):
    IncomeFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_view_only_expenses(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_view_incomes_and_expenses(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_chart_categories_years(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]
    assert actual['salary_categories'] == [1999]


@freeze_time('1999-1-1')
def test_chart_balance_categories_only_incomes(client_logged):
    IncomeFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]\


@freeze_time('1999-1-1')
def test_chart_balance_categories_only_expenses(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]
