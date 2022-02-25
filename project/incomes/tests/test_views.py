import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import models, views
from ..factories import Income, IncomeFactory, IncomeTypeFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

pytestmark = pytest.mark.django_db


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
def test_income_load_form(client_logged):
    url = reverse('incomes:incomes_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html_form']


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


def test_incomes_load_update_form(client_logged):
    i = IncomeFactory()
    url = reverse('incomes:incomes_update', kwargs={'pk': i.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '1999-01-01' in form
    assert '1000.62' in form
    assert 'Income Type' in form
    assert 'remark' in form


def test_incomes_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    a = AccountFactory(journal = j, title='a')
    it = IncomeTypeFactory(title='yyy', journal=j)
    obj = IncomeFactory(income_type=it, price=666, account=a)

    url = reverse('incomes:incomes_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert it.title not in form
    assert str(obj.price) not in form


def test_income_update_to_another_year(client_logged):
    income = IncomeFactory()

    data = {
        'price': '150',
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


@freeze_time('2000-03-03')
def test_incomes_update_past_record(get_user, client_logged):
    get_user.year = 2000
    i = IncomeFactory(date=date(1974, 12, 12))

    data = {
        'price': '150',
        'date': '1997-12-12',
        'remark': 'Pastaba',
        'account': 1,
        'income_type': 1,
    }
    url = reverse('incomes:incomes_update', kwargs={'pk': i.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Income.objects.get(pk=i.pk)
    assert actual.date == date(1997, 12, 12)
    assert float(150) == 150
    assert actual.account.title == 'Account1'
    assert actual.income_type.title == 'Income Type'
    assert actual.remark == 'Pastaba'


def test_incomes_index_search_form(client_logged):
    url = reverse('incomes:incomes_index')
    response = client_logged.get(url).content.decode('utf-8')

    assert '<input type="text" name="search"' in response
    assert reverse('incomes:incomes_search') in response


# ---------------------------------------------------------------------------------------
#                                                                           Income Delete
# ---------------------------------------------------------------------------------------
def test_view_incomes_delete_func():
    view = resolve('/incomes/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_incomes_delete_200(client_logged):
    p = IncomeFactory()

    url = reverse('incomes:incomes_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_incomes_delete_load_form(client_logged):
    p = IncomeFactory()

    url = reverse('incomes:incomes_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{p}</strong>?' in actual


def test_view_incomes_delete(client_logged):
    p = IncomeFactory()

    assert models.Income.objects.all().count() == 1
    url = reverse('incomes:incomes_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Income.objects.all().count() == 0


def test_incomes_delete_other_journal_get_form(client_logged, second_user):
    it2 = IncomeTypeFactory(title='yyy', journal=second_user.journal)
    i2 = IncomeFactory(income_type=it2, price=666)

    url = reverse('incomes:incomes_delete', kwargs={'pk': i2.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


def test_incomes_delete_other_journal_post_form(client_logged, second_user):
    it2 = IncomeTypeFactory(title='yyy', journal=second_user.journal)
    i2 = IncomeFactory(income_type=it2, price=666)

    url = reverse('incomes:incomes_delete', kwargs={'pk': i2.pk})
    client_logged.post(url, **X_Req)

    assert Income.objects.all().count() == 1


# ----------------------------------------------------------------------------
#                                                                 Income Type
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_type_load_form(client_logged):
    url = reverse('incomes:incomes_type_new')

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 200


def test_type_save(client_logged):
    data = {
        'title': 'TTT',
        'type': 'salary',
    }

    url = reverse('incomes:incomes_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('incomes:incomes_type_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_type_update(client_logged):
    income = IncomeTypeFactory()

    data = {'title': 'TTT', 'type': 'other'}
    url = reverse('incomes:incomes_type_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert 'TTT' in actual['html_list']


def test_income_type_not_load_other_journal(client_logged, main_user, second_user):
    IncomeTypeFactory(title='xxx', journal=main_user.journal)
    obj = IncomeTypeFactory(title='yyy', journal=second_user.journal)

    url = reverse('incomes:incomes_type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert obj.title not in form


def test_view_index_200(client_logged):
    response = client_logged.get('/incomes/')

    assert response.status_code == 200

    assert 'incomes' in response.context
    assert 'categories' in response.context


# ---------------------------------------------------------------------------------------
#                                                                          Incomes Search
# ---------------------------------------------------------------------------------------
@pytest.fixture()
def _search_form_data():
    return ([
        {"name":"csrfmiddlewaretoken", "value":"xxx"},
        {"name":"search", "value":"1999 type"},
    ])


def test_search_func():
    view = resolve('/incomes/search/')

    assert views.Search == view.func.view_class


def test_search_get_200(client_logged):
    url = reverse('incomes:incomes_search')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_get_302(client):
    url = reverse('incomes:incomes_search')
    response = client.get(url)

    assert response.status_code == 302


def test_search_post_200(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)
    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 200


def test_search_post_404(client_logged):
    url = reverse('incomes:incomes_search')
    response = client_logged.post(url)

    assert response.status_code == 404


def test_search_post_500(client_logged):
    form_data = json.dumps([{'x': 'y'}])
    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_bad_json_data(client_logged):
    form_data = "{'x': 'y'}"
    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_form_is_not_valid(client_logged, _search_form_data):
    _search_form_data[1]['value'] = '@#$%^&*xxxx'  # search
    form_data = json.dumps(_search_form_data)

    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert not actual['form_is_valid']


def test_search_form_is_valid(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)

    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert actual['form_is_valid']


def test_search_not_found(client_logged, _search_form_data):
    IncomeFactory()

    _search_form_data[1]['value'] = 'xxxx'
    form_data = json.dumps(_search_form_data)

    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert 'Nieko nerasta' in actual['html']


def test_search_found(client_logged, _search_form_data):
    IncomeFactory()

    form_data = json.dumps(_search_form_data)

    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert '1999-01-01' in actual['html']
    assert 'remark' in actual['html']


def test_search_pagination_first_page(client_logged, _search_form_data):
    a = AccountFactory()
    t = IncomeTypeFactory()
    i = IncomeFactory.build_batch(51, account=a, income_type=t)
    Income.objects.bulk_create(i)

    form_data = json.dumps(_search_form_data)

    url = reverse('incomes:incomes_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert 'html' in actual

    actual = actual['html']

    assert actual.count('Income Type') == 50


def test_search_pagination_second_page(client_logged):
    a = AccountFactory()
    t = IncomeTypeFactory()
    i = IncomeFactory.build_batch(51, account=a, income_type=t)
    Income.objects.bulk_create(i)

    url = reverse('incomes:incomes_search')

    response = client_logged.get(url, {'page': 2, 'search': 'type'})
    actual = json.loads(response.content)

    assert 'ajax-content' in actual

    actual = actual['ajax-content']

    assert actual.count('Income Type') == 1
