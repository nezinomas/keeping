import json

import pytest
from django.urls import resolve, reverse

from ...auths.factories import UserFactory
from ..factories import AccountFactory
from ..views import Lists, New, Update, load_to_account

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}



def test_view_lists_func():
    view = resolve('/accounts/')

    assert Lists == view.func.view_class


def test_view_new_func():
    view = resolve('/accounts/new/')

    assert New == view.func.view_class


def test_view_update_func():
    view = resolve('/accounts/update/1/')

    assert Update == view.func.view_class


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



# ----------------------------------------------------------------------------
#                                                                 load_account
# ----------------------------------------------------------------------------
def test_load_to_account_func():
    view = resolve('/ajax/load_to_account/')

    assert load_to_account == view.func


def test_load_t_account_form(admin_client):
    url = reverse('accounts:accounts_new')

    response = admin_client.get(url, {}, **X_Req)

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
