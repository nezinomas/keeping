import json
from datetime import date

import pytest
from django.urls import resolve, reverse

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


def test_load_to_account_func():
    view = resolve('/ajax/load_to_account/')

    assert load_to_account == view.func


def test_load_account_form(admin_client):
    url = reverse('accounts:accounts_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code


@pytest.mark.django_db()
def test_save_account(client, login):
    data = {'title': 'Title', 'order': '111'}

    url = reverse('accounts:accounts_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'Title' in actual['html_list']


@pytest.mark.django_db()
def test_accounts_save_invalid_data(client, login):
    data = {'title': '', 'order': 'x'}

    url = reverse('accounts:accounts_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_account_update(client, login):
    account = AccountFactory()

    data = {'title': 'Title', 'order': '111'}
    url = reverse('accounts:accounts_update', kwargs={'pk': account.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'Title' in actual['html_list']


@pytest.mark.django_db
def test_load_to_account(login, client):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    url = reverse('accounts:load_to_account')

    response = client.get(url, {'id': a1.pk})

    assert 200 == response.status_code
    assert 1 == len(response.context['objects'])
