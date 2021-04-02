import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import setup_view
from .. import models, views
from ..factories import SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db
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
def test_saving_load_form(client_logged):
    url = reverse('savings:savings_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html_form']


def test_saving_save(client_logged):
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

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert '0,25' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Savings' in actual['html_list']


def test_saving_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'fee': 'x',
        'account': 'x',
        'saving_type': 'x'
    }

    url = reverse('savings:savings_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_saving_update_to_another_year(client_logged):
    saving = SavingFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'remark': 'Pastaba',
        'fee': '25',
        'account': 1,
        'saving_type': 1
    }
    url = reverse('savings:savings_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


def test_saving_update(client_logged):
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

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert '150' in actual['html_list']
    assert '25' in actual['html_list']
    assert 'Pastaba' in actual['html_list']


# ---------------------------------------------------------------------------------------
#                                                                           Saving Delete
# ---------------------------------------------------------------------------------------
def test_view_saving_delete_func():
    view = resolve('/savings/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_saving_delete_200(client_logged):
    p = SavingFactory()

    url = reverse('savings:savings_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_saving_delete_load_form(client_logged):
    p = SavingFactory()

    url = reverse('savings:savings_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/savings/delete/1/"' in actual['html_form']


def test_view_saving_delete(client_logged):
    p = SavingFactory()

    assert models.Saving.objects.all().count() == 1
    url = reverse('savings:savings_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Saving.objects.all().count() == 0


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_type_load_form(client_logged):
    url = reverse('savings:savings_type_new')

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 200


def test_type_save(client_logged):
    data = {
        'title': 'TTT',
    }

    url = reverse('savings:savings_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


def test_type_save_with_closed(client_logged):
    data = {
        'title': 'TTT', 'closed': '2000'
    }

    url = reverse('savings:savings_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('savings:savings_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_type_update(client_logged):
    saving = SavingTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('savings:savings_type_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


def test_type_update_with_closed(client_logged):
    saving = SavingTypeFactory()

    data = {'title': 'TTT', 'closed': '2000'}
    url = reverse('savings:savings_type_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get('/savings/')

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

    assert len(actual) == 2
    assert 'S1' in actual
    assert 'S2' in actual
