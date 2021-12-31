from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from project.journals.factories import JournalFactory

from ...accounts.factories import AccountBalance, AccountFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import PensionBalance, PensionFactory
from ...savings.factories import SavingBalance, SavingFactory, SavingTypeFactory
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


# ---------------------------------------------------------------------------------------
#                                                                                 Methods
# ---------------------------------------------------------------------------------------
def test_accounts_method():
    obj = AccountFactory()

    actual = views.accounts()

    assert actual == {'closed': {}, 'Account1': obj.pk}


def test_accounts_method_with_closed():
    obj1 = AccountFactory()
    obj2 = AccountFactory(title='XXX', closed=66)

    actual = views.accounts()

    assert actual == {'closed': {'XXX': 66}, 'Account1': obj1.pk, 'XXX': obj2.pk}


def test_savings_method():
    obj = SavingTypeFactory()

    actual = views.savings()

    assert actual == {'closed': dict(), 'Savings': obj.pk}


def test_savings_method_with_closed():
    obj1 = SavingFactory()
    obj2 = SavingTypeFactory(title='x', closed=66)

    actual = views.savings()

    assert actual == {'closed': {'x': 66}, 'Savings': obj1.pk, 'x': obj2.pk}


def test_pensions_method():
    obj = PensionFactory()

    actual = views.pensions()

    assert actual == {'PensionType': obj.pk}


def test_filter_types_1():
    arr = {'x': 1, 'y': 2, 'closed': {'x': 66}}

    actual = views.filter_types(arr, 67)

    assert actual == {'y': 2}


def test_filter_types_when_update_year_in_past():
    arr = {'x': 1, 'y': 2, 'closed': {'x': 66}}

    actual = views.filter_types(arr, 65)

    assert actual == {'x': 1, 'y': 2}


def test_filter_types_when_update_year_equal_closed():
    arr = {'x': 1, 'y': 2, 'closed': {'x': 66}}

    actual = views.filter_types(arr, 66)

    assert actual == {'x': 1, 'y': 2}


def test_filter_types_2():
    arr = {'x': 1, 'y': 2, 'closed': {}}

    actual = views.filter_types(arr, 67)

    assert actual == {'x': 1, 'y': 2}


def test_filter_types_preserve_orginal_arr():
    arr = {'x': 1, 'y': 2, 'closed': {'x': 99}}

    views.filter_types(arr, 99)

    assert arr == {'x': 1, 'y': 2, 'closed': {'x': 99}}


def test_filter_real_values_1():
    arr = {
        'closed': {'SEB Gyvybės kaupiamasis': 2019},
        'SEB Asia ex. Japan Fund': 5,
        'SEB Concept Biotechnology': 4,
        'SEB Gyvybės kaupiamasis': 7,
        'SEB Nordic Equity Fund': 6,
        'SEB Strategy Growth': 3,
        'INVL Extremo': 2,
        'Apple': 10,
        'MicroSoft': 8,
        'Tesla': 9
    }

    actual = views.filter_types(arr, 2020)

    assert 'SEB Gyvybės kaupiamasis' not in actual


def test_filter_real_values_2():
    arr = {
        'closed': {'SEB Gyvybės kaupiamasis': 2019},
        'SEB Asia ex. Japan Fund': 5,
        'SEB Concept Biotechnology': 4,
        'SEB Gyvybės kaupiamasis': 7,
        'SEB Nordic Equity Fund': 6,
        'SEB Strategy Growth': 3,
        'INVL Extremo': 2,
        'Apple': 10,
        'MicroSoft': 8,
        'Tesla': 9
    }

    actual = views.filter_types(arr, 2019)

    assert 'SEB Gyvybės kaupiamasis' in actual


def test_make_arr_1():
    _arr = [
        {'id': 1, 'title': 'X', 'closed': None},
        {'id': 2, 'title': 'Y', 'closed': 2000},
        {'id': 3, 'title': 'Z', 'closed': 2001},
    ]

    actual = views._make_arr(_arr)

    expect = {
        'closed': {'Y': 2000, 'Z': 2001},
        'X': 1,
        'Y': 2,
        'Z': 3
    }

    assert actual == expect
