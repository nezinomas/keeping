import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import views
from ..factories import IncomeFactory, IncomeTypeFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ----------------------------------------------------------------------------
#                                                                      Incomes
# ----------------------------------------------------------------------------
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
@pytest.mark.django_db()
def test_income_load_form(client_logged):
    url = reverse('incomes:incomes_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html_form']


@pytest.mark.django_db()
def test_income_save(client_logged):
    a = AccountFactory()
    i = IncomeTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'account': a.pk,
        'income_type': i.pk
    }

    url = reverse('incomes:incomes_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Income Type' in actual['html_list']


@pytest.mark.django_db()
def test_income_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'account': 'x',
        'income_type': 'x'
    }

    url = reverse('incomes:incomes_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_income_update_to_another_year(client_logged):
    income = IncomeFactory()

    data = {'price': '150',
            'date': '2010-12-31',
            'remark': 'Pastaba',
            'account': 1,
            'income_type': 1
    }
    url = reverse('incomes:incomes_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


@pytest.mark.django_db()
def test_income_update(client_logged):
    income = IncomeFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'income_type': 1
    }
    url = reverse('incomes:incomes_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert '150' in actual['html_list']
    assert 'Pastaba' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                                 Income Type
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
@pytest.mark.django_db()
def test_type_load_form(client_logged):
    url = reverse('incomes:incomes_type_new')

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 200


@pytest.mark.django_db()
def test_type_save(client_logged):
    data = {
        'title': 'TTT',
    }

    url = reverse('incomes:incomes_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('incomes:incomes_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_type_update(client_logged):
    income = IncomeTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('incomes:incomes_type_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get('/incomes/')

    assert response.status_code == 200

    assert 'incomes' in response.context
    assert 'categories' in response.context
