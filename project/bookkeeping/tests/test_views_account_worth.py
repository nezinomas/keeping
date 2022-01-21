import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import setup_view
from .. import views

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ---------------------------------------------------------------------------------------
#                                                                           Account Worth
# ---------------------------------------------------------------------------------------
def test_accounts_worth_func():
    view = resolve('/bookkeeping/accounts_worth/new/')

    assert views.AccountsWorthNew == view.func.view_class


def test_account_worth_200(client_logged):
    response = client_logged.get('/bookkeeping/accounts_worth/new/')

    assert response.status_code == 200


def test_account_worth_formset(client_logged):
    AccountFactory()

    url = reverse('bookkeeping:accounts_worth_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert 'Sąskaitų vertė' in actual['html_form']
    assert '<option value="1" selected>Account1</option>' in actual['html_form']


@freeze_time('1999-9-9')
def test_account_worth_new(client_logged):
    i = AccountFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-account': i.pk
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']
    assert 'data-bs-title="1999 m. rugsėjo 9 d.' in actual['html_list']

def test_account_worth_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-account': 0
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_account_worth_formset_closed_in_past(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 2000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  # pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' not in actual


def test_account_worth_formset_closed_in_current(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


def test_account_worth_formset_closed_in_future(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual
