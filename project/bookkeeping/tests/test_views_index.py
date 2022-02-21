from datetime import date, datetime

import pytest
import pytz
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountBalanceFactory
from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ...pensions.factories import PensionFactory
from ...savings.factories import SavingFactory
from .. import views
from ..factories import (AccountWorthFactory, PensionWorthFactory,
                         SavingWorthFactory)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                   Index
# ---------------------------------------------------------------------------------------
def test_view_index_func():
    view = resolve('/')

    assert views.Index == view.func.view_class


def test_view_index_200(client_logged):
    response = client_logged.get('/')

    assert response.status_code == 200


def test_view_index_context(client_logged):
    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert 'year' in response.context
    assert 'accounts' in response.context
    assert 'savings' in response.context
    assert 'pensions' in response.context
    assert 'year_balance' in response.context
    assert 'year_balance_short' in response.context
    assert 'year_expenses' in response.context
    assert 'no_incomes' in response.context
    assert 'averages' in response.context
    assert 'wealth' in response.context
    assert 'borrow' in response.context
    assert 'lend' in response.context
    assert 'chart_expenses' in response.context
    assert 'chart_balance' in response.context


@freeze_time('1999-07-01')
def test_no_incomes(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=1.0, expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(date=date(1999, 1, 1), price=2.0, expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(date=date(1999, 6, 1), price=4.0, expense_type=ExpenseTypeFactory(title='y'))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 1.17
    assert round(response.context['save_sum'], 2) == 0.0


@freeze_time('1999-07-01')
def test_no_incomes_no_data(client_logged):
    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 0
    assert round(response.context['save_sum'], 2) == 0


def test_index_account_worth(client_logged):
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=pytz.utc), price=555)

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    actual = response.context['accounts']
    assert 'title="1999 m. vasario 2 d., 00:00"' in actual
    assert '555,0' in actual


def test_index_account_worth_then_last_check_empty(client_logged):
    AccountBalanceFactory()

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    actual = response.context['accounts']

    assert 'data-bs-title="Nenurodyta"' in actual
    assert '0,2' in actual


def test_index_savings_worth(client_logged):
    SavingFactory()
    SavingWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    SavingWorthFactory(date=datetime(1998, 2, 2, tzinfo=pytz.utc))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = [x['items'] for x in response.context if x.get('title') == 'Fondai'][0][0]

    assert exp['latest_check'] == datetime(1998, 2, 2, tzinfo=pytz.utc)


def test_index_pension_worth(client_logged):
    PensionFactory()
    PensionWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    PensionWorthFactory(date=datetime(1998, 2, 2, tzinfo=pytz.utc))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = [x['items'] for x in response.context if x.get('title') == 'Pensijos'][0][0]

    assert exp['latest_check'] == datetime(1998, 2, 2, tzinfo=pytz.utc)
