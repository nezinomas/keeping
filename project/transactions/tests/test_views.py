import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...journals.factories import JournalFactory
from ...savings.factories import SavingTypeFactory
from ...users.factories import UserFactory
from .. import models, views
from ..factories import (SavingChangeFactory, SavingCloseFactory,
                         TransactionFactory)

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_view_index_200(client_logged):
    response = client_logged.get('/transactions/')

    assert response.status_code == 200

    assert 'categories' in response.context
    assert 'transactions' in response.context
    assert 'savings_close' in response.context
    assert 'savings_change' in response.context


def test_transactions_index_func():
    view = resolve('/transactions/')

    assert views.Index is view.func.view_class


def test_transactions_lists_func():
    view = resolve('/transactions/lists/')

    assert views.Lists is view.func.view_class


def test_transactions_new_func():
    view = resolve('/transactions/new/')

    assert views.New is view.func.view_class


def test_transactions_update_func():
    view = resolve('/transactions/update/1/')

    assert views.Update is view.func.view_class


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


# ---------------------------------------------------------------------------------------
#                                                                           Transaction Delete
# ---------------------------------------------------------------------------------------
def test_view_transactions_delete_func():
    view = resolve('/transactions/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_transactions_delete_200(client_logged):
    p = TransactionFactory()

    url = reverse('transactions:transactions_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_transactions_delete_load_form(client_logged):
    p = TransactionFactory()

    url = reverse('transactions:transactions_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai nori išrinti: <strong>1999-01-01 Account1-&gt;Account2: 200.00</strong>?' in actual


def test_view_transactions_delete(client_logged):
    p = TransactionFactory()

    assert models.Transaction.objects.all().count() == 1
    url = reverse('transactions:transactions_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Transaction.objects.all().count() == 0


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


# ---------------------------------------------------------------------------------------
#                                                                      SavingClose Delete
# ---------------------------------------------------------------------------------------
def test_view_savings_close_delete_func():
    view = resolve('/savings_close/delete/1/')

    assert views.SavingsCloseDelete is view.func.view_class


def test_view_savings_close_delete_200(client_logged):
    p = SavingCloseFactory()

    url = reverse('transactions:savings_close_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_savings_close_delete_load_form(client_logged):
    p = SavingCloseFactory()

    url = reverse('transactions:savings_close_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai nori išrinti: <strong>1999-01-01 Savings From-&gt;Account To: 10.00</strong>?' in actual


def test_view_savings_close_delete(client_logged):
    p = SavingCloseFactory()

    assert models.SavingClose.objects.all().count() == 1
    url = reverse('transactions:savings_close_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.SavingClose.objects.all().count() == 0


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
def test_load_saving_type_func():
    view = resolve('/ajax/load_saving_type/')

    assert views.LoadSavingType is view.func.view_class


def test_load_saving_type_status_code(client_logged):
    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': 1})

    assert response.status_code == 200


def test_load_saving_type_closed_in_past(client_logged):
    s1 = SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': s1.pk})

    assert 'S1' not in str(response.content)
    assert 'S2' not in str(response.content)


def test_load_saving_type_for_current_user(client_logged):
    s1 = SavingTypeFactory(title='S1')
    j2 = JournalFactory(user=UserFactory(username='X'))
    SavingTypeFactory(title='S2', journal=j2)

    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': s1.pk})

    assert 'S1' not in str(response.content)
    assert 'S2' not in str(response.content)


def test_load_saving_type_empty_parent_pk(client_logged):
    url = reverse('transactions:load_saving_type')
    response = client_logged.get(url, {'id': ''})

    assert response.status_code == 200
    assert response.context['objects'] == []


# ---------------------------------------------------------------------------------------
#                                                                      SavingChange Delete
# ---------------------------------------------------------------------------------------
def test_view_savings_change_delete_func():
    view = resolve('/savings_change/delete/1/')

    assert views.SavingsChangeDelete is view.func.view_class


def test_view_savings_change_delete_200(client_logged):
    p = SavingChangeFactory()

    url = reverse('transactions:savings_change_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_savings_change_delete_load_form(client_logged):
    p = SavingChangeFactory()

    url = reverse('transactions:savings_change_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai nori išrinti: <strong>1999-01-01 Savings From-&gt;Savings To: 10.00</strong>?' in actual


def test_view_savings_change_delete(client_logged):
    p = SavingChangeFactory()

    assert models.SavingChange.objects.all().count() == 1
    url = reverse('transactions:savings_change_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.SavingChange.objects.all().count() == 0
