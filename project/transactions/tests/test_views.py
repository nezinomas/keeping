import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from .. import views
from ..factories import (SavingChangeFactory, SavingCloseFactory,
                         TransactionFactory)
from ...users.factories import UserFactory

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


def test_load_saving_type_func():
    view = resolve('/ajax/load_saving_type/')

    assert views.load_saving_type == view.func


@pytest.mark.django_db
def test_load_saving_type_200(client_logged):
    response = client_logged.get('/ajax/load_saving_type/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_load_saving_type_has_saving_type(client_logged):
    SavingTypeFactory()

    response = client_logged.get('/ajax/load_saving_type/')

    assert 'Savings' in str(response.content)


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get('/transactions/')

    assert response.status_code == 200

    assert 'categories' in response.context
    assert 'transactions' in response.context
    assert 'savings_close' in response.context
    assert 'savings_change' in response.context


def test_transactions_index_func():
    view = resolve('/transactions/')

    assert views.Index == view.func.view_class


def test_transactions_lists_func():
    view = resolve('/transactions/lists/')

    assert views.Lists == view.func.view_class


def test_transactions_new_func():
    view = resolve('/transactions/new/')

    assert views.New == view.func.view_class


def test_transactions_update_func():
    view = resolve('/transactions/update/1/')

    assert views.Update == view.func.view_class


@freeze_time('2000-01-01')
def test_transactions_load_form(client_logged):
    url = reverse('transactions:transactions_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html_form']


def test_transactions_save(client_logged):
    a1 = AccountFactory()
    a2 = AccountFactory(title='Account2')

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'from_account': a1.pk,
        'to_account': a2.pk
    }

    url = reverse('transactions:transactions_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Account2' in actual['html_list']


def test_transactions_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'from_account': 0,
        'to_account': 0,
    }

    url = reverse('transactions:transactions_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_transactions_update_to_another_year(client_logged):
    tr = TransactionFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'to_account': tr.to_account.pk,
        'from_account': tr.from_account.pk,
    }
    url = reverse('transactions:transactions_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


def test_transactions_update(client_logged):
    tr = TransactionFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'from_account': tr.from_account.pk,
        'to_account': tr.to_account.pk
    }
    url = reverse('transactions:transactions_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Account2' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_lists_func():
    view = resolve('/savings_close/lists/')

    assert views.SavingsCloseLists == view.func.view_class


def test_saving_close_new_func():
    view = resolve('/savings_close/new/')

    assert views.SavingsCloseNew == view.func.view_class


def test_saving_close_update_func():
    view = resolve('/savings_close/update/1/')

    assert views.SavingsCloseUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_savings_close_load_form(client_logged):
    url = reverse('transactions:savings_close_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert  response.status_code == 200
    assert '1999-01-01' in actual['html_form']


def test_savings_close_save(client_logged):
    a1 = SavingTypeFactory()
    a2 = AccountFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'from_account': a1.pk,
        'to_account': a2.pk
    }

    url = reverse('transactions:savings_close_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'Savings' in actual['html_list']


def test_savings_close_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'from_account': 0,
        'to_account': 0,
    }

    url = reverse('transactions:savings_close_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_savings_close_update_to_another_year(client_logged):
    tr = SavingCloseFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'fee': '99',
        'to_account': tr.to_account.pk,
        'from_account': tr.from_account.pk
    }
    url = reverse('transactions:savings_close_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


def test_savings_close_update(client_logged):
    tr = SavingCloseFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'fee': '99',
        'from_account': tr.from_account.pk,
        'to_account': tr.to_account.pk
    }
    url = reverse('transactions:savings_close_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert 'Account To' in actual['html_list']
    assert 'Savings From' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_lists_func():
    view = resolve('/savings_change/lists/')

    assert views.SavingsChangeLists == view.func.view_class


def test_saving_change_new_func():
    view = resolve('/savings_change/new/')

    assert views.SavingsChangeNew == view.func.view_class


def test_saving_change_update_func():
    view = resolve('/savings_change/update/1/')

    assert views.SavingsChangeUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_savings_change_load_form(client_logged):
    url = reverse('transactions:savings_change_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html_form']


def test_savings_change_save(client_logged):
    a1 = SavingTypeFactory()
    a2 = SavingTypeFactory(title='Savings2')

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'from_account': a1.pk,
        'to_account': a2.pk
    }

    url = reverse('transactions:savings_change_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1,05' in actual['html_list']
    assert 'Savings' in actual['html_list']
    assert 'Savings2' in actual['html_list']


def test_savings_change_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'from_account': 0,
        'to_account': 0,
    }

    url = reverse('transactions:savings_change_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_savings_change_update_to_another_year(client_logged):
    tr = SavingChangeFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'fee': '99',
        'to_account': tr.to_account.pk,
        'from_account': tr.from_account.pk
    }
    url = reverse('transactions:savings_change_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


def test_savings_change_update(client_logged):
    tr = SavingChangeFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'fee': '99',
        'from_account': tr.from_account.pk,
        'to_account': tr.to_account.pk
    }
    url = reverse('transactions:savings_change_update', kwargs={'pk': tr.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-12-31' in actual['html_list']
    assert 'Savings To' in actual['html_list']
    assert 'Savings From' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                             load_saving_type
# ----------------------------------------------------------------------------
def test_load_saving_type_new_func():
    view = resolve('/ajax/load_saving_type/')

    assert views.load_saving_type == view.func


@pytest.mark.django_db
def test_load_saving_type_status_code(client_logged):
    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': 1})

    assert response.status_code == 200


@pytest.mark.django_db
def test_load_saving_type_closed_in_past(client_logged):
    s1 = SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': s1.pk})

    assert 'S1' not in str(response.content)
    assert 'S2' not in str(response.content)


@pytest.mark.django_db
def test_load_saving_type_for_current_user(client_logged):
    s1 = SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', user=UserFactory(username='XXX'))

    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': s1.pk})

    assert 'S1' not in str(response.content)
    assert 'S2' not in str(response.content)
