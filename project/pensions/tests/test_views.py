import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from .. import views
from ..factories import PensionFactory, PensionTypeFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


def test_pensions_index_func():
    view = resolve('/pensions/')

    assert views.Index == view.func.view_class


def test_pensions_lists_func():
    view = resolve('/pensions/lists/')

    assert views.Lists == view.func.view_class


def test_pensions_new_func():
    view = resolve('/pensions/new/')

    assert views.New == view.func.view_class


def test_pensions_update_func():
    view = resolve('/pensions/update/1/')

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve('/pensions/type/')

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve('/pensions/type/new/')

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve('/pensions/type/update/1/')

    assert views.TypeUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_pensions_load_form(admin_client):
    url = reverse('pensions:pensions_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '2000-01-01' in actual['html_form']


@pytest.mark.django_db()
def test_pensions_save(client_logged):
    i = PensionTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'pension_type': i.pk
    }

    url = reverse('pensions:pensions_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'PensionType' in actual['html_list']


@pytest.mark.django_db()
def test_pensions_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'pension_type': 'x'
    }

    url = reverse('pensions:pensions_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_pensions_update_to_another_year(client_logged):
    income = PensionFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'pension_type': 1,
    }
    url = reverse('pensions:pensions_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


@pytest.mark.django_db()
def test_pensions_update(client_logged):
    income = PensionFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'pension_type': 1
    }
    url = reverse('pensions:pensions_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert '150' in actual['html_list']
    assert 'Pastaba' in actual['html_list']


#
# PensionType
#

@freeze_time('2000-01-01')
def test_type_load_form(admin_client):
    url = reverse('pensions:pensions_type_new')

    response = admin_client.get(url, {}, **X_Req)

    assert response.status_code == 200


@pytest.mark.django_db()
def test_type_save(client_logged):
    data = {
        'title': 'TTT',
    }

    url = reverse('pensions:pensions_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('pensions:pensions_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_type_update(client_logged):
    income = PensionTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('pensions:pensions_type_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get('/pensions/')

    assert response.status_code == 200

    assert 'data' in response.context
    assert 'categories' in response.context
