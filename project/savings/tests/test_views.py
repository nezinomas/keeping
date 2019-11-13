import json
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import setup_view
from .. import views
from ..factories import SavingFactory, SavingTypeFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}



def test_savings_index_func():
    view = resolve('/savings/')

    assert views.Index == view.func.view_class


def test_savings_lists_func():
    view = resolve('/savings/lists/')

    assert views.Lists == view.func.view_class


def test_savings_new_func():
    view = resolve('/savings/new/')

    assert views.New == view.func.view_class


def test_savings_update_func():
    view = resolve('/savings/update/1/')

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve('/savings/type/')

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve('/savings/type/new/')

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve('/savings/type/update/1/')

    assert views.TypeUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_saving_load_form(admin_client):
    url = reverse('savings:savings_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '2000-01-01' in actual['html_form']


@pytest.mark.django_db()
def test_saving_save(client, login):
    a = AccountFactory()
    i = SavingTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'fee': '0.25',
        'account': a.pk,
        'saving_type': i.pk
    }

    url = reverse('savings:savings_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert '0,25' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Savings' in actual['html_list']


@pytest.mark.django_db()
def test_saving_save_invalid_data(client, login):
    data = {
        'date': 'x',
        'price': 'x',
        'fee': 'x',
        'account': 'x',
        'saving_type': 'x'
    }

    url = reverse('savings:savings_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_saving_update_to_another_year(client, login):
    saving = SavingFactory()

    data = {'price': '150',
            'date': '2010-12-31',
            'remark': 'Pastaba',
            'fee': '25',
            'account': 1,
            'saving_type': 1
    }
    url = reverse('savings:savings_update', kwargs={'pk': saving.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


@pytest.mark.django_db()
def test_saving_update(client, login):
    saving = SavingFactory()

    data = {
        'price': '150',
        'fee': '25',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'saving_type': 1
    }
    url = reverse('savings:savings_update', kwargs={'pk': saving.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert '150' in actual['html_list']
    assert '25' in actual['html_list']
    assert 'Pastaba' in actual['html_list']


#
# SavingType
#

@freeze_time('2000-01-01')
def test_type_load_form(admin_client):
    url = reverse('savings:savings_type_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code


@pytest.mark.django_db()
def test_type_save(client, login):
    data = {
        'title': 'TTT',
    }

    url = reverse('savings:savings_type_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_save_with_closed(client, login):
    data = {
        'title': 'TTT', 'closed': '2000'
    }

    url = reverse('savings:savings_type_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_save_invalid_data(client, login):
    data = {'title': ''}

    url = reverse('savings:savings_type_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_type_update(client, login):
    saving = SavingTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('savings:savings_type_update', kwargs={'pk': saving.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_update_with_closed(client, login):
    saving = SavingTypeFactory()

    data = {'title': 'TTT', 'closed': '2000'}
    url = reverse('savings:savings_type_update', kwargs={'pk': saving.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db
def test_view_index_200(login, client):
    response = client.get('/savings/')

    assert response.status_code == 200

    assert 'savings' in response.context
    assert 'categories' in response.context


@pytest.mark.django_db
def test_type_list_view_has_all(fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1974)

    view = setup_view(views.TypeLists(), fake_request)

    ctx = view.get_context_data()
    actual = [str(x) for x in ctx['items']]

    assert 2 == len(actual)
    assert 'S1' in actual
    assert 'S2' in actual
