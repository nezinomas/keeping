from datetime import date, datetime

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch
from project.accounts.models import Account
from project.journals.factories import JournalFactory

from ...accounts.factories import AccountBalance, AccountFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import (PensionBalance, PensionFactory,
                                   PensionTypeFactory)
from ...savings.factories import (SavingBalance, SavingFactory,
                                  SavingTypeFactory)
from .. import views
from .utils import setup_view

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'year, expect',
    [
        (2010, 2010),
        (1000, 1999),
        (3000, 1999),
    ])
@freeze_time('2020-01-01')
def test_set_year(year, expect, get_user, client_logged):
    get_user.journal.first_record = date(1974, 1, 1)
    url = reverse(
        'core:set_year',
        kwargs={'year': year}
    )
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.year == expect


@pytest.mark.parametrize(
    'month, expect',
    [
        (1, 1),
        (12, 12),
        (13, 12),
    ])
def test_set_month(month, expect, client_logged):
    url = reverse(
        'core:set_month',
        kwargs={'month': month}
    )

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.month == expect


# ---------------------------------------------------------------------------------------
#                                                                     Regenerate Balances
# ---------------------------------------------------------------------------------------
def test_view_regenerate_balances_func():
    view = resolve('/set/balances/')

    assert views.RegenerateBalances == view.func.view_class


def test_view_regenerate_balances_current_year_func():
    view = resolve('/set/balances/1999/')

    assert views.RegenerateBalancesCurrentYear == view.func.view_class


def test_view_regenerate_balances_status_200(client_logged):
    url = reverse('core:regenerate_balances')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


def test_view_regenerate_balances_current_year_status_200(client_logged):
    url = reverse(
        'core:regenerate_balances_current_year',
        kwargs={'year': 1999}
    )
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_view_regenerate_balances_current_year(client_logged):
    ExpenseFactory()
    IncomeFactory()
    SavingFactory()
    PensionFactory()

    AccountBalance.objects.all().delete()
    SavingBalance.objects.all().delete()
    PensionBalance.objects.all().delete()

    assert AccountBalance.objects.all().count() == 0
    assert SavingBalance.objects.all().count() == 0
    assert PensionBalance.objects.all().count() == 0

    url = reverse(
        'core:regenerate_balances_current_year',
        kwargs={'year': 1999}
    )

    client_logged.get(url, {'ajax_trigger': 1}, follow=True, **X_Req)

    assert AccountBalance.objects.all().count() == 1
    assert SavingBalance.objects.all().count() == 1
    assert PensionBalance.objects.all().count() == 1


@freeze_time('1999-01-01')
def test_view_regenerate_balances_all_year(client_logged, get_user):
    ExpenseFactory()
    ExpenseFactory(date=date(1998, 1, 1))

    IncomeFactory()
    IncomeFactory(date=date(1998, 1, 1))

    SavingFactory()
    PensionFactory()

    get_user.journal.first_record = date(1998, 1, 1)
    get_user.journal.save()

    AccountBalance.objects.all().delete()
    SavingBalance.objects.all().delete()
    PensionBalance.objects.all().delete()

    assert AccountBalance.objects.all().count() == 0
    assert SavingBalance.objects.all().count() == 0
    assert PensionBalance.objects.all().count() == 0

    url = reverse('core:regenerate_balances')

    client_logged.get(url, {'ajax_trigger': 1}, follow=True, **X_Req)

    assert AccountBalance.objects.all().count() == 2
    assert SavingBalance.objects.all().count() == 2
    assert PensionBalance.objects.all().count() == 2


@freeze_time('2007-01-01')
@patch('project.core.views.accounts')
@patch('project.core.views.savings')
@patch('project.core.views.pensions')
@patch.object(views.SignalBase, 'accounts')
@patch.object(views.SignalBase, 'savings')
@patch.object(views.SignalBase, 'pensions')
def test_view_regenerate_balances_func_called(mck_pension,
                                              mck_saving,
                                              mck_account,
                                              mp, ms, ma,
                                              get_user,
                                              fake_request):

    fake_request.user = get_user
    fake_request.user.journal.first_record = date(2006, 1, 1)

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), fake_request)
    view.get(fake_request)

    assert mck_account.call_count == 2
    assert mck_saving.call_count == 2
    assert mck_pension.call_count == 2


@patch('project.core.views.accounts')
@patch('project.core.views.savings')
@patch('project.core.views.pensions')
@patch.object(views.SignalBase, 'accounts')
@patch.object(views.SignalBase, 'savings')
@patch.object(views.SignalBase, 'pensions')
def test_view_regenerate_balances_current_year_func_called(mck_pension,
                                                           mck_saving,
                                                           mck_account,
                                                           mp, ms, ma,
                                                           fake_request):
    fake_request.user.journal = JournalFactory()

    class Dummy(views.RegenerateBalancesCurrentYear):
        pass

    view = setup_view(Dummy(), fake_request)
    view.get(fake_request)

    assert mck_account.call_count == 1
    assert mck_saving.call_count == 1
    assert mck_pension.call_count == 1
