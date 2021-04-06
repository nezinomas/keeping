import json

import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import setup_view
from ...users.factories import UserFactory
from .. import views
from ..factories import AccountFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}



def test_view_lists_func():
    view = resolve('/accounts/')

    assert views.Lists is view.func.view_class


def test_view_new_func():
    view = resolve('/accounts/new/')

    assert views.New is view.func.view_class


def test_view_update_func():
    view = resolve('/accounts/update/1/')

    assert views.Update is view.func.view_class


@pytest.mark.django_db()
def test_save_account(client_logged):
    data = {'title': 'Title', 'order': '111'}

    url = reverse('accounts:accounts_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'Title' in actual['html_list']


@pytest.mark.django_db()
def test_accounts_save_invalid_data(client_logged):
    data = {'title': '', 'order': 'x'}

    url = reverse('accounts:accounts_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_account_update(client_logged):
    account = AccountFactory()

    data = {'title': 'Title', 'order': '111'}
    url = reverse('accounts:accounts_update', kwargs={'pk': account.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'Title' in actual['html_list']


@pytest.mark.django_db()
def test_account_list_view_has_all(fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1974)

    view = setup_view(views.Lists(), fake_request)

    ctx = view.get_context_data()
    actual = [str(x) for x in ctx['items']]

    assert len(actual) == 2
    assert 'S1' in actual
    assert 'S2' in actual


# ----------------------------------------------------------------------------
#                                                                 load_account
# ----------------------------------------------------------------------------
def test_load_to_account_func():
    view = resolve('/ajax/load_to_account/')

    assert views.load_to_account is view.func


@pytest.mark.django_db
def test_load_to_account_form(client_logged):
    url = reverse('accounts:accounts_new')

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 200


@pytest.mark.django_db
def test_load_to_account(client_logged):
    a1 = AccountFactory(title='A1')
    AccountFactory(title='A2')
    AccountFactory(title='A3', user=UserFactory(username='XXX'))

    url = reverse('accounts:load_to_account')

    response = client_logged.get(url, {'id': a1.pk})

    assert response.status_code == 200
    assert len(response.context['objects']) == 1
