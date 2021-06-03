import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import change_profile_year
from ...users.factories import UserFactory
from .. import models
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..views import expenses, expenses_name, expenses_type

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db

@pytest.fixture()
def _db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title='F')
    ExpenseNameFactory(title='S', valid_for=1999)


# ---------------------------------------------------------------------------------------
#                                                                                 Expense
# ---------------------------------------------------------------------------------------
def test_expenses_index_func():
    view = resolve('/expenses/')

    assert expenses.Index == view.func.view_class


def test_expenses_lists_func():
    view = resolve('/expenses/lists/')

    assert expenses.Lists == view.func.view_class


def test_expenses_lists_200(client_logged):
    url = reverse('expenses:expenses_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_expenses_lists_302(client):
    url = reverse('expenses:expenses_list')
    response = client.get(url)

    assert response.status_code == 302


def test_expenses_lists_month_func():
    view = resolve('/expenses/lists/1/')

    assert expenses.MonthLists == view.func.view_class


def test_expenses_lists_month_search_form(client_logged):
    url = reverse('expenses:expenses_month_list', kwargs={'month': 1})
    response = client_logged.get(url).content.decode('utf-8')

    assert '<input type="text" name="search"' in response
    assert reverse('expenses:expenses_search') in response


def test_expenses_new_func():
    view = resolve('/expenses/new/')

    assert expenses.New == view.func.view_class


def test_expenses_update_func():
    view = resolve('/expenses/update/1/')

    assert expenses.Update == view.func.view_class


@freeze_time('1974-08-08')
def test_expenses_load_new_form(get_user, client_logged):
    get_user.year = 3000
    url = reverse('expenses:expenses_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '3000-08-08' in actual['html_form']


def test_expenses_save(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'quantity': 33,
        'account': a.pk,
        'expense_type': t.pk,
        'expense_name': n.pk,
    }

    url = reverse('expenses:expenses_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Expense.objects.get(pk=1)
    assert actual.date == date(1999, 1, 1)
    assert pytest.approx(float(actual.price), rel=1e-2) == 1.05
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'


def test_expenses_save_insert_button(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'quantity': 33,
        'account': a.pk,
        'expense_type': t.pk,
        'expense_name': n.pk,
    }

    url = reverse('expenses:expenses_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')
    assert 'id="submit">Insert</button>' in actual['html_form']
    assert 'data-action="insert"' in actual['html_form']
    assert 'data-chained-dropdown="/ajax/load_expense_name/' in actual['html_form']


def test_expenses_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'quantity': 0,
        'account': 'x',
        'expense_type': 'x',
    }

    url = reverse('expenses:expenses_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_expenses_load_update_form(client_logged):
    e = ExpenseFactory()
    url = reverse('expenses:expenses_update', kwargs={'pk': e.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '1999-01-01' in form
    assert '1.12' in form
    assert '13' in form
    assert 'Expense Type' in form
    assert 'Expense Name' in form
    assert 'Remark' in form


def test_expenses_update_to_another_year(client_logged):
    e = ExpenseFactory()

    data = {
        'price': '150',
        'quantity': 13,
        'date': '2010-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'expense_type': 1,
        'expense_name': 1,
    }
    url = reverse('expenses:expenses_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    assert actual['form_is_valid']

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(2010, 12, 31)
    assert actual.quantity == 13


def test_expenses_update(client_logged):
    e = ExpenseFactory()

    data = {
        'price': '150',
        'quantity': 33,
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'expense_type': 1,
        'expense_name': 1,
    }
    url = reverse('expenses:expenses_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1999, 12, 31)
    assert float(150) == 150
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'
    assert actual.remark == 'Pastaba'


@freeze_time('2000-03-03')
def test_expenses_update_past_record(get_user, client_logged):
    get_user.year = 2000
    e = ExpenseFactory(date=date(1974, 12, 12))

    data = {
        'price': '150',
        'quantity': 33,
        'date': '1974-12-12',
        'remark': 'Pastaba',
        'account': 1,
        'expense_type': 1,
        'expense_name': 1,
    }
    url = reverse('expenses:expenses_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1974, 12, 12)
    assert float(150) == 150
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'
    assert actual.remark == 'Pastaba'


def test_expenses_index_200(client_logged):
    response = client_logged.get('/expenses/')

    assert response.status_code == 200

    assert 'expenses_list' in response.context
    assert 'categories' in response.context


def test_expenses_month_list_200(client_logged):
    response = client_logged.get('/expenses/lists/1/')

    assert response.status_code == 200


def test_expenses_index_search_form(client_logged):
    url = reverse('expenses:expenses_index')
    response = client_logged.get(url).content.decode('utf-8')

    assert '<input type="text" name="search"' in response
    assert reverse('expenses:expenses_search') in response


# ---------------------------------------------------------------------------------------
#                                                                          Expense Delete
# ---------------------------------------------------------------------------------------
def test_view_expenses_delete_func():
    view = resolve('/expenses/delete/1/')

    assert expenses.Delete is view.func.view_class


def test_view_expenses_delete_200(client_logged):
    p = ExpenseFactory()

    url = reverse('expenses:expenses_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_expenses_delete_load_form(client_logged):
    p = ExpenseFactory()

    url = reverse('expenses:expenses_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="expenses_list">' in actual
    assert 'Ar tikrai nori išrinti: <strong>1999-01-01/Expense Type/Expense Name</strong>?' in actual


def test_view_expenses_delete(client_logged):
    p = ExpenseFactory()

    assert models.Expense.objects.all().count() == 1
    url = reverse('expenses:expenses_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Expense.objects.all().count() == 0


# ---------------------------------------------------------------------------------------
#                                                                             ExpenseType
# ---------------------------------------------------------------------------------------
def test_expenses_type_new_func():
    view = resolve('/expenses/type/new/')

    assert expenses_type.New == view.func.view_class


def test_expenses_type_update_func():
    view = resolve('/expenses/type/update/1/')

    assert expenses_type.Update == view.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                             ExpenseName
# ---------------------------------------------------------------------------------------
def test_expenses_name_new_func():
    view = resolve('/expenses/name/new/')

    assert expenses_name.New == view.func.view_class


def test_expenses_name_update_func():
    view = resolve('/expenses/name/update/1/')

    assert expenses_name.Update == view.func.view_class


def test_expense_name_save_data(client_logged):
    url = reverse('expenses:expenses_name_new')
    p = ExpenseTypeFactory()

    data = {
        'title': 'TTT', 'parent': p.pk
    }

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    templates = [t.name for t in response.templates]
    template = 'expenses/includes/expenses_type_list.html'

    # expense_name template is same as expense_type
    assert template in templates


def test_expense_name_save_invalid_data(client_logged):
    data = {
        'title': 'x',
        'parent': 0
    }

    url = reverse('expenses:expenses_name_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_expense_name_update(client_logged):
    e = ExpenseNameFactory()

    data = {
        'title': 'TTT',
        'valid_for': 2000,
        'parent': e.parent.pk
    }
    url = reverse('expenses:expenses_name_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


# ---------------------------------------------------------------------------------------
#                                                                       LoadExpenseName
# ---------------------------------------------------------------------------------------
def test_load_expenses_name_new_func():
    actual = resolve('/ajax/load_expense_name/')

    assert expenses.LoadExpenseName is actual.func.view_class


def test_load_expense_name_status_code(client_logged):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client_logged, _db_data):
    change_profile_year(client_logged)

    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.context['objects'].count() == 1


def test_load_expense_name_all(client_logged, _db_data):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.context['objects'].count() == 2


def test_load_expense_name_select_empty_parent(client_logged, _db_data):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': ''})

    assert response.context['objects'] == []


# ---------------------------------------------------------------------------------------
#                                                                         realod expenses
# ---------------------------------------------------------------------------------------
def test_view_reload_expenses_func():
    view = resolve('/expenses/reload/')

    assert expenses.ReloadExpenses is view.func.view_class


def test_view_reload_expenses_render(rf):
    request = rf.get('/expenses/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = expenses.ReloadExpenses.as_view()(request)

    assert response.status_code == 200


def test_view_reload_expenses_render_ajax_trigger_not_set(client_logged):
    url = reverse('expenses:reload_expenses')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert expenses.Index == response.resolver_match.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                         Expenses Search
# ---------------------------------------------------------------------------------------
@pytest.fixture()
def _search_form_data():
    return ([
        {"name":"csrfmiddlewaretoken", "value":"xxx"},
        {"name":"search", "value":"1999 type"},
    ])


def test_search_func():
    view = resolve('/expenses/search/')

    assert expenses.Search == view.func.view_class


def test_search_get_200(client_logged):
    url = reverse('expenses:expenses_search')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_get_302(client):
    url = reverse('expenses:expenses_search')
    response = client.get(url)

    assert response.status_code == 302


def test_search_post_200(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)
    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 200


def test_search_post_404(client_logged):
    url = reverse('expenses:expenses_search')
    response = client_logged.post(url)

    assert response.status_code == 404


def test_search_post_500(client_logged):
    form_data = json.dumps([{'x': 'y'}])
    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_bad_json_data(client_logged):
    form_data = "{'x': 'y'}"
    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_form_is_not_valid(client_logged, _search_form_data):
    _search_form_data[1]['value'] = '@#$%^&*xxxx'  # search
    form_data = json.dumps(_search_form_data)

    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert not actual['form_is_valid']


def test_search_form_is_valid(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)

    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert actual['form_is_valid']


def test_search_not_found(client_logged, _search_form_data):
    ExpenseFactory()

    _search_form_data[1]['value'] = 'xxxx'
    form_data = json.dumps(_search_form_data)

    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert 'Nieko neradau' in actual['html']


def test_search_found(client_logged, _search_form_data):
    ExpenseFactory()

    form_data = json.dumps(_search_form_data)

    url = reverse('expenses:expenses_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert '1999-01-01' in actual['html']
    assert 'Remark' in actual['html']
