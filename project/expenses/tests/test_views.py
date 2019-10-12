import json

import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import change_profile_year
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..models import ExpenseName
from ..views import expenses, expenses_name, expenses_type

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


@pytest.fixture()
def db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title='F')
    ExpenseNameFactory(title='S', valid_for=1999)


#
# =============================================================
#                                                      Expense
# =============================================================
#
def test_expenses_index_func():
    view = resolve('/expenses/')

    assert expenses.Index == view.func.view_class


def test_expenses_lists_func():
    view = resolve('/expenses/lists/')

    assert expenses.Lists == view.func.view_class


def test_expenses_new_func():
    view = resolve('/expenses/new/')

    assert expenses.New == view.func.view_class


def test_expenses_update_func():
    view = resolve('/expenses/update/1/')

    assert expenses.Update == view.func.view_class


@pytest.mark.django_db
def test_expenses_index_200(login, client):
    response = client.get('/expenses/')

    assert response.status_code == 200

    assert 'expenses' in response.context
    assert 'categories' in response.context


#
# =============================================================
#                                                   ExpenseType
# =============================================================
#
def test_expenses_type_new_func():
    view = resolve('/expenses/type/new/')

    assert expenses_type.New == view.func.view_class


def test_expenses_type_update_func():
    view = resolve('/expenses/type/update/1/')

    assert expenses_type.Update == view.func.view_class


#
# =============================================================
#                                                   ExpenseName
# =============================================================
#
def test_expenses_name_new_func():
    view = resolve('/expenses/name/new/')

    assert expenses_name.New == view.func.view_class


def test_expenses_name_update_func():
    view = resolve('/expenses/name/update/1/')

    assert expenses_name.Update == view.func.view_class


@pytest.mark.django_db
def test_expense_name_save_data(login, client):
    url = reverse('expenses:expenses_name_new')
    p = ExpenseTypeFactory()

    data = {
        'title': 'TTT', 'parent': p.pk
    }

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code

    templates = [t.name for t in response.templates]
    template = 'expenses/includes/expenses_type_list.html'

    # expense_name template is same as expense_type
    assert template in templates


@pytest.mark.django_db()
def test_expense_name_save_invalid_data(client, login):
    data = {
        'title': 'x',
        'parent': 0
    }

    url = reverse('expenses:expenses_name_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_expense_name_update(client, login):
    e = ExpenseNameFactory()

    data = {
        'title': 'TTT',
        'valid_for': 2000,
        'parent': e.parent.pk
    }
    url = reverse('expenses:expenses_name_update', kwargs={'pk': e.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


#
# =============================================================
#                                             load_expense_name
# =============================================================
#
def test_load_expenses_name_new_func():
    view = resolve('/ajax/load_expense_name/')

    assert expenses.load_expense_name == view.func


@pytest.mark.django_db
def test_load_expense_name_status_code(client, login):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert response.status_code == 200


@pytest.mark.django_db
def test_load_expense_name_isnull_count(client, login, db_data):
    change_profile_year(client)

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 1 == response.context['objects'].count()


@pytest.mark.django_db
def test_load_expense_name_all(client, login, db_data):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 2 == response.context['objects'].count()
