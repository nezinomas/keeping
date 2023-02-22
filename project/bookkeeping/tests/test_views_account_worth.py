from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...core.tests.utils import setup_view
from .. import views
from ..factories import AccountWorthFactory
from ..models import AccountWorth

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve('/bookkeeping/accounts_worth/new/')

    assert views.AccountsWorthNew == view.func.view_class


def test_200(client_logged):
    url = reverse('bookkeeping:accounts_worth_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_formset(client_logged):
    AccountFactory()

    url = reverse('bookkeeping:accounts_worth_new')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'Sąskaitų vertė' in actual
    assert '<option value="1" selected>Account1</option>' in actual


def test_formset_new(client_logged):
    i = AccountFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-date': '1999-9-9',
        'form-0-price': '999',
        'form-0-account': i.pk
    }

    url = reverse('bookkeeping:accounts_worth_new')
    client_logged.post(url, data, follow=True)

    actual = AccountWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 9
    assert actual.date.day == 9
    assert actual.price == 999


def test_formset_dublicated(client_logged):
    i = AccountFactory()
    data = {
        'form-TOTAL_FORMS': 2,
        'form-INITIAL_FORMS': 0,
        'form-0-date': '1999-9-9',
        'form-0-price': '999',
        'form-0-account': i.pk,
        'form-1-price': '666',
        'form-1-account': i.pk
    }

    url = reverse('bookkeeping:accounts_worth_new')
    response = client_logged.post(url, data)
    actual = response.context['formset']

    assert not actual.is_valid()


def test_formset_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-date': 'x',
        'form-0-price': 'x',
        'form-0-account': 0
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client_logged.post(url, data)
    actual = response.context['formset']

    assert not actual.is_valid()
    assert 'date' in actual.errors[0]
    assert 'price' in actual.errors[0]
    assert 'account' in actual.errors[0]


def test_formset_closed_in_past(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 2000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view.get_formset())  # pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' not in actual


def test_formset_closed_in_current(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view.get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


def test_formset_closed_in_future(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view.get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


def test_view(client_logged):
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=pytz.utc), price=555)

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    actual = response.context['accounts']
    assert 'title="1999 m. vasario 2 d., 00:00"' in actual
    assert '555,0' in actual


def test_view_last_check_empty(client_logged):
    AccountBalanceFactory()

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    actual = response.context['accounts']

    assert 'data-bs-title="Nenurodyta"' in actual
    assert '20' in actual
