import json
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import views
from ..factories import IncomeFactory, IncomeTypeFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


def test_incomes_index_func():
    view = resolve('/incomes/')

    assert views.Index == view.func.view_class


def test_incomes_lists_func():
    view = resolve('/incomes/lists/')

    assert views.Lists == view.func.view_class


def test_incomes_new_func():
    view = resolve('/incomes/new/')

    assert views.New == view.func.view_class


def test_incomes_update_func():
    view = resolve('/incomes/update/1/')

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve('/incomes/type/')

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve('/incomes/type/new/')

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve('/incomes/type/update/1/')

    assert views.TypeUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_income_load_form(admin_client):
    url = reverse('incomes:incomes_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '2000-01-01' in actual['html_form']


@pytest.mark.django_db()
def test_income_save(client, login):
    a = AccountFactory()
    i = IncomeTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'account': a.pk,
        'income_type': i.pk
    }

    url = reverse('incomes:incomes_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Income Type' in actual['html_list']


@pytest.mark.django_db()
def test_income_save_invalid_data(client, login):
    data = {
        'date': 'x',
        'price': 'x',
        'account': 'x',
        'income_type': 'x'
    }

    url = reverse('incomes:incomes_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_income_update_to_another_year(client, login):
    income = IncomeFactory()

    data = {'price': '150',
            'date': '2010-12-31',
            'remark': 'Pastaba',
            'account': 1,
            'income_type': 1
    }
    url = reverse('incomes:incomes_update', kwargs={'pk': income.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


@pytest.mark.django_db()
def test_income_update(client, login):
    income = IncomeFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'income_type': 1
    }
    url = reverse('incomes:incomes_update', kwargs={'pk': income.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert '150' in actual['html_list']
    assert 'Pastaba' in actual['html_list']


#
# IncomeType
#

@freeze_time('2000-01-01')
def test_type_load_form(admin_client):
    url = reverse('incomes:incomes_type_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code


@pytest.mark.django_db()
def test_type_save(client, login):
    data = {
        'title': 'TTT',
    }

    url = reverse('incomes:incomes_type_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_save_invalid_data(client, login):
    data = {'title': ''}

    url = reverse('incomes:incomes_type_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_type_update(client, login):
    income = IncomeTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('incomes:incomes_type_update', kwargs={'pk': income.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']
