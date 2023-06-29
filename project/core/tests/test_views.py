from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse
from mock import patch

from ...accounts.factories import AccountBalance
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import PensionBalance, PensionFactory
from ...savings.factories import SavingBalance, SavingFactory
from ...users.factories import UserFactory
from .. import views
from .utils import setup_view

pytestmark = pytest.mark.django_db
from datetime import datetime


@pytest.mark.parametrize(
    'year, expect',
    [
        (2010, 2010),
        (1000, 1999),
        (3000, 1999),
    ])
@patch('project.bookkeeping.lib.year_balance.datetime')
def test_set_year(dt_mock, year, expect, main_user, client_logged):
    dt_mock.now.return_value = datetime(2020, 1, 1)

    main_user.journal.first_record = date(1974, 1, 1)
    url = reverse(
        'core:set_year',
        kwargs={'year': year}
    )
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.year == expect


# ---------------------------------------------------------------------------------------
#                                                                     Regenerate Balances
# ---------------------------------------------------------------------------------------
def test_view_regenerate_balances_func():
    view = resolve('/set/balances/')

    assert views.RegenerateBalances == view.func.view_class


def test_view_regenerate_balances_status_200(client_logged):
    url = reverse('core:regenerate_balances')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 204


@time_machine.travel('1999-01-01')
def test_view_regenerate_balances_all_year(client_logged, main_user):
    ExpenseFactory()
    ExpenseFactory(date=date(1998, 1, 1))

    IncomeFactory()
    IncomeFactory(date=date(1998, 1, 1))

    SavingFactory()
    PensionFactory()

    main_user.journal.first_record = date(1998, 1, 1)
    main_user.journal.save()

    AccountBalance.objects.all().delete()
    SavingBalance.objects.all().delete()
    PensionBalance.objects.all().delete()

    assert AccountBalance.objects.all().count() == 0
    assert SavingBalance.objects.all().count() == 0
    assert PensionBalance.objects.all().count() == 0

    url = reverse('core:regenerate_balances')

    client_logged.get(url, {'ajax_trigger': 1}, follow=True)

    assert AccountBalance.objects.all().count() == 3
    assert SavingBalance.objects.all().count() == 2
    assert PensionBalance.objects.all().count() == 2


def test_view_regenerate_balances_func_called(mocker, fake_request):
    account = mocker.patch('project.core.signals.accounts_signal')
    saving = mocker.patch('project.core.signals.savings_signal')
    pension = mocker.patch('project.core.signals.pensions_signal')

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), fake_request)
    view.get(fake_request)

    assert account.call_count == 1
    assert saving.call_count == 1
    assert pension.call_count == 1


def test_view_regenerate_account_balances(mocker, rf):
    request = rf.get('/fake/?type=accounts')
    request.user = UserFactory.build()

    account = mocker.patch('project.core.signals.accounts_signal')
    saving = mocker.patch('project.core.signals.savings_signal')
    pension = mocker.patch('project.core.signals.pensions_signal')

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 1
    assert saving.call_count == 0
    assert pension.call_count == 0


def test_view_regenerate_saving_balances(mocker, rf):
    request = rf.get('/fake/?type=savings')
    request.user = UserFactory.build()

    account = mocker.patch('project.core.signals.accounts_signal')
    saving = mocker.patch('project.core.signals.savings_signal')
    pension = mocker.patch('project.core.signals.pensions_signal')

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 0
    assert saving.call_count == 1
    assert pension.call_count == 0


def test_view_regenerate_pension_balances(mocker, rf):
    request = rf.get('/fake/?type=pensions')
    request.user = UserFactory.build()

    account = mocker.patch('project.core.signals.accounts_signal')
    saving = mocker.patch('project.core.signals.savings_signal')
    pension = mocker.patch('project.core.signals.pensions_signal')

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 0
    assert saving.call_count == 0
    assert pension.call_count == 1


def test_view_regenerate_no_errors(client_logged):
    url = reverse('core:regenerate_balances')
    response = client_logged.get(f'{url}?type=xxx&ajax_trigger=1', {})

    assert response.status_code == 204
