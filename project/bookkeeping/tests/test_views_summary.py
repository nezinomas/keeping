import pytest
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve('/summary/')

    assert views.Summary == view.func.view_class


def test_200(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert 'chart_balance' in actual
    assert 'chart_incomes' in actual


def test_no_data(client_logged):
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
