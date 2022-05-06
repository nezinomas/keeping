import json
from datetime import date
from decimal import Decimal

import pytest
from django.http.response import JsonResponse
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import change_profile_year
from ...users.factories import UserFactory
from .. import models
from ..factories import (Expense, ExpenseFactory, ExpenseNameFactory,
                         ExpenseTypeFactory)
from ..views import expenses, expenses_name, expenses_type

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
    view = resolve('/expenses/list/')

    assert expenses.Lists == view.func.view_class


def test_expenses_lists_200(client_logged):
    url = reverse('expenses:list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_expenses_lists_302(client):
    url = reverse('expenses:list')
    response = client.get(url)

    assert response.status_code == 302


def test_expenses_new_func():
    view = resolve('/expenses/new/')

    assert expenses.New == view.func.view_class


def test_expenses_update_func():
    view = resolve('/expenses/update/1/')

    assert expenses.Update == view.func.view_class


def test_expenses_context(client_logged):
    url = reverse('expenses:index')
    response = client_logged.get(url)
    context = response.context

    assert 'types' in context
    assert 'expenses' in context


@freeze_time('1974-08-08')
def test_expenses_load_new_form(get_user, client_logged):
    get_user.year = 3000
    url = reverse('expenses:new')

    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert '3000-08-08' in actual
    assert 'Įrašyti</button>' in actual
    assert 'Įrašyti ir uždaryti</button>' in actual


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

    url = reverse('expenses:new')
    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.last()
    assert actual.date == date(1999, 1, 1)
    assert actual.price == Decimal('1.05')
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'


def test_expenses_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'quantity': 0,
        'account': 'x',
        'expense_type': 'x',
    }

    url = reverse('expenses:new')
    response = client_logged.post(url, data)
    actual = response.context['form']

    assert not actual.is_valid()


def test_expenses_load_update_form(client_logged):
    e = ExpenseFactory()

    url = reverse('expenses:update', kwargs={'pk': e.pk})
    response = client_logged.get(url)
    form = response.content.decode('utf-8')

    assert 'Atnaujinti</button>' in form
    assert 'Atnaujinti ir uždaryti</button>' in form

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
    url = reverse('expenses:update', kwargs={'pk': e.pk})

    client_logged.post(url, data)

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
    url = reverse('expenses:update', kwargs={'pk': e.pk})

    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'
    assert actual.remark == 'Pastaba'


def test_expenses_not_load_other_journal(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(journal = j1, title='a1')
    a2 = AccountFactory(journal = j2, title='a2')
    et1 = ExpenseTypeFactory(title='xxx', journal=j1)
    et2 = ExpenseTypeFactory(title='yyy', journal=j2)

    ExpenseFactory(expense_type=et1, account=a1)
    e2 = ExpenseFactory(expense_type=et2, account=a2, price=666)

    url = reverse('expenses:update', kwargs={'pk': e2.pk})
    response = client_logged.get(url)

    form = response.content.decode('utf-8')

    assert et2.title not in form
    assert str(e2.price) not in form


@freeze_time('2000-03-03')
def test_expenses_update_past_record(get_user, client_logged):
    get_user.year = 2000
    e = ExpenseFactory(date=date(1974, 12, 12))

    data = {
        'price': '150',
        'quantity': 33,
        'date': '1998-12-12',
        'remark': 'Pastaba',
        'account': 1,
        'expense_type': 1,
        'expense_name': 1,
    }
    url = reverse('expenses:update', kwargs={'pk': e.pk})
    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1998, 12, 12)
    assert actual.price == Decimal('150')
    assert actual.quantity == 33
    assert actual.account.title == 'Account1'
    assert actual.expense_type.title == 'Expense Type'
    assert actual.expense_name.title == 'Expense Name'
    assert actual.remark == 'Pastaba'


def test_expenses_index_200(client_logged):
    url = reverse('expenses:index')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


def test_expenses_index_search_form(client_logged):
    url = reverse('expenses:index')
    response = client_logged.get(url, follow=True).content.decode('utf-8')

    assert '<input type="search" name="search"' in response
    assert reverse('expenses:search') in response


@freeze_time('1999-1-1')
def test_expenses_list_month_not_set(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse('expenses:list')
    actual = client_logged.get(url).context['object_list']

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)


@freeze_time('1999-1-1')
def test_expenses_list_month_stringt(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse('expenses:list')
    actual = client_logged.get(url, {'month': 'xxx'}).context['object_list']

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)


@freeze_time('1999-1-1')
def test_expenses_list_january(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))


    url = reverse('expenses:list')
    actual = client_logged.get(url, {'month': 1}).context['object_list']

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)


@freeze_time('1999-1-1')
def test_expenses_list_all(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse('expenses:list')
    actual = client_logged.get(url, {'month': 13}).context['object_list']

    assert len(actual) == 2


@freeze_time('1999-1-1')
def test_expenses_list_all_any_num(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse('expenses:list')
    actual = client_logged.get(url, {'month': 133}).context['object_list']

    assert len(actual) == 2


# ---------------------------------------------------------------------------------------
#                                                                          Expense Delete
# ---------------------------------------------------------------------------------------
def test_view_expenses_delete_func():
    view = resolve('/expenses/delete/1/')

    assert expenses.Delete is view.func.view_class


def test_view_expenses_delete_200(client_logged):
    p = ExpenseFactory()

    url = reverse('expenses:delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_expenses_delete_load_form(client_logged):
    p = ExpenseFactory()

    url = reverse('expenses:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)

    actual = response.content.decode('utf-8')

    assert response.status_code == 200
    assert '<form method="POST"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01/Expense Type/Expense Name</strong>?' in actual


def test_view_expenses_delete(client_logged):
    p = ExpenseFactory()

    assert models.Expense.objects.all().count() == 1
    url = reverse('expenses:delete', kwargs={'pk': p.pk})

    client_logged.post(url)

    assert models.Expense.objects.all().count() == 0


def test_expenses_delete_other_journal_get_form(client_logged, second_user):
    it2 = ExpenseTypeFactory(title='yyy', journal=second_user.journal)
    i2 = ExpenseFactory(expense_type=it2, price=666)

    url = reverse('expenses:delete', kwargs={'pk': i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expenses_delete_other_journal_post_form(client_logged, second_user):
    it2 = ExpenseTypeFactory(title='yyy', journal=second_user.journal)
    i2 = ExpenseFactory(expense_type=it2, price=666)

    url = reverse('expenses:delete', kwargs={'pk': i2.pk})
    client_logged.post(url)

    assert Expense.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                             ExpenseType
# ---------------------------------------------------------------------------------------
def test_expenses_type_new_func():
    view = resolve('/expenses/type/new/')

    assert expenses_type.New == view.func.view_class


def test_expenses_type_update_func():
    view = resolve('/expenses/type/update/1/')

    assert expenses_type.Update == view.func.view_class


def test_expense_type_not_load_other_journal(client_logged, main_user, second_user):
    ExpenseTypeFactory(title='xxx', journal=main_user.journal)
    obj = ExpenseTypeFactory(title='yyy', journal=second_user.journal)

    url = reverse('expenses:type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    form = response.content.decode('utf-8')

    assert obj.title not in form


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
    url = reverse('expenses:name_new')
    p = ExpenseTypeFactory()

    data = {
        'title': 'TTT', 'parent': p.pk
    }

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert 'TTT' in actual



def test_expense_name_save_invalid_data(client_logged):
    data = {
        'title': 'x',
        'parent': 0
    }

    url = reverse('expenses:name_new')

    response = client_logged.post(url, data)

    actual = response.context['form']

    assert not actual.is_valid()


def test_expense_name_update(client_logged):
    e = ExpenseNameFactory()

    data = {
        'title': 'TTT',
        'valid_for': 2000,
        'parent': e.parent.pk
    }
    url = reverse('expenses:name_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_expense_name_not_load_other_journal(client_logged, main_user, second_user):
    et1 = ExpenseTypeFactory(title='xxx', journal=main_user.journal)
    et2 = ExpenseTypeFactory(title='yyy', journal=second_user.journal)

    ExpenseNameFactory(parent=et1)
    obj = ExpenseNameFactory(parent=et2)

    url = reverse('expenses:name_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    actual = response.content.decode('utf-8')

    assert obj.title not in actual
    assert et2.title not in actual


# ---------------------------------------------------------------------------------------
#                                                                       LoadExpenseName
# ---------------------------------------------------------------------------------------
def test_load_expenses_name_new_func():
    actual = resolve('/expenses/load_expense_name/')

    assert expenses.LoadExpenseName is actual.func.view_class


def test_load_expense_name_status_code(client_logged):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client_logged, _db_data):
    change_profile_year(client_logged)

    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.context['object_list'].count() == 1


def test_load_expense_name_all(client_logged, _db_data):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': 1})

    assert response.context['object_list'].count() == 2


def test_load_expense_name_select_empty_parent(client_logged, _db_data):
    url = reverse('expenses:load_expense_name')
    response = client_logged.get(url, {'expense_type': ''})

    assert response.context['object_list'] == []


def test_load_expense_name_must_logged(client):
    url = reverse('expenses:load_expense_name')

    response = client.get(url, follow=True)

    assert response.status_code == 200

    from ...users.views import Login
    assert response.resolver_match.func.view_class is Login


# ---------------------------------------------------------------------------------------
#                                                                         Expenses Search
# ---------------------------------------------------------------------------------------
def test_search_func():
    view = resolve('/expenses/search/')

    assert expenses.Search == view.func.view_class


def test_search_get_200(client_logged):
    url = reverse('expenses:search')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_not_found(client_logged):
    ExpenseFactory()

    url = reverse('expenses:search')
    response = client_logged.get(url, {'search': 'xxx'})
    actual = response.content.decode('utf-8')

    assert 'Nieko nerasta' in actual


def test_search_found(client_logged):
    ExpenseFactory()

    url = reverse('expenses:search')
    response = client_logged.get(url, {'search': 'type'})
    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual
    assert 'Remark' in actual


def test_search_pagination_first_page(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    i = ExpenseFactory.build_batch(51, account=a, expense_type=t, expense_name=n)
    Expense.objects.bulk_create(i)

    url = reverse('expenses:search')
    response = client_logged.get(url, {'search': 'type'})
    actual = response.context['object_list']

    assert len(actual) == 50


def test_search_pagination_second_page(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    i = ExpenseFactory.build_batch(51, account=a, expense_type=t, expense_name=n)
    Expense.objects.bulk_create(i)

    url = reverse('expenses:search')
    response = client_logged.get(url, {'page': 2, 'search': 'type'})
    actual = response.context['object_list']

    assert len(actual) == 1
