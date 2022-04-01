from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountBalance
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import PensionBalance, PensionFactory
from ...savings.factories import SavingBalance, SavingFactory
from ...users.factories import UserFactory
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


def test_view_regenerate_balances_status_200(client_logged):
    url = reverse('core:regenerate_balances')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


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
    assert SavingBalance.objects.all().count() == 1
    assert PensionBalance.objects.all().count() == 1


def test_view_regenerate_balances_func_called(mocker, fake_request):
    account = mocker.patch.object(views.SignalBase, 'accounts')
    saving = mocker.patch.object(views.SignalBase, 'savings')
    pension = mocker.patch.object(views.SignalBase, 'pensions')

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

    account = mocker.patch.object(views.SignalBase, 'accounts')
    saving = mocker.patch.object(views.SignalBase, 'savings')
    pension = mocker.patch.object(views.SignalBase, 'pensions')

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

    account = mocker.patch.object(views.SignalBase, 'accounts')
    saving = mocker.patch.object(views.SignalBase, 'savings')
    pension = mocker.patch.object(views.SignalBase, 'pensions')

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

    account = mocker.patch.object(views.SignalBase, 'accounts')
    saving = mocker.patch.object(views.SignalBase, 'savings')
    pension = mocker.patch.object(views.SignalBase, 'pensions')

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 0
    assert saving.call_count == 0
    assert pension.call_count == 1
