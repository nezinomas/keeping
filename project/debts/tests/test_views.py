import json
import re
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import factories, models, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                             Debts Index
# ---------------------------------------------------------------------------------------
def test_debts_index_func():
    view = resolve('/debts/')

    assert views.Index == view.func.view_class


def test_debts_index_200(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_debts_index_not_logged(client):
    url = reverse('debts:debts_index')
    response = client.get(url)

    assert response.status_code == 302


def test_debts_index_borrow_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'borrow' in response.context
    assert 'id="borrow_ajax"' in content


def test_debts_index_borrow_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'borrow_return' in response.context
    assert 'id="borrow_return_ajax"' in content


def test_debts_index_lent_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent' in response.context
    assert 'id="lent_ajax"' in content


def test_debts_index_lent_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent_return' in response.context
    assert 'id="lent_return_ajax"' in content


def test_debts_index_borrow_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:borrows_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_borrow_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:borrows_return_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


def test_debts_index_lent_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:lents_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_lent_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:lents_return_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


# ---------------------------------------------------------------------------------------
#                                                                                  Borrow
# ---------------------------------------------------------------------------------------
def test_borrow_list_func():
    view = resolve('/borrows/lists/')

    assert views.BorrowLists == view.func.view_class


def test_borrow_list_200(client_logged):
    url = reverse('debts:borrows_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_list_empty(client_logged):
    url = reverse('debts:borrows_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_list_with_data(client_logged):
    f = factories.BorrowFactory()

    url = reverse('debts:borrows_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolininkas' in content
    assert 'Paskolinta' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-01' in content
    assert f.name in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Borrow Remark' in content


def test_borrow_new_func():
    view = resolve('/borrows/new/')

    assert views.BorrowNew == view.func.view_class


def test_borrow_new_200(client_logged):
    url = reverse('debts:borrows_new')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('2000-01-01')
def test_borrow_load_form(client_logged):
    url = reverse('debts:borrows_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


def test_borrow_save(client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert '1,1' in actual['html_list']


def test_borrow_save_invalid_data(client_logged):
    data = {'date': 'x', 'name': 'A', 'price': '0'}

    url = reverse('debts:borrows_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_borrow_update_func():
    view = resolve('/borrows/update/1/')

    assert views.BorrowUpdate == view.func.view_class


def test_borrow_update_200(client_logged):
    f = factories.BorrowFactory()

    url = reverse('debts:borrows_update', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                           Borrow Return
# ---------------------------------------------------------------------------------------
def test_borrow_return_list_func():
    view = resolve('/borrows/return/lists/')

    assert views.BorrowReturnLists == view.func.view_class


def test_borrow_return_list_200(client_logged):
    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_list_empty(client_logged):
    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_return_list_with_data(client_logged):
    factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Kiek' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Borrow Return Remark' in content


def test_borrow_return_new_func():
    view = resolve('/borrows/return/new/')

    assert views.BorrowReturnNew == view.func.view_class


def test_borrow_return_new_200(client_logged):
    url = reverse('debts:borrows_return_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_form(client_logged):
    url = reverse('debts:borrows_return_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200


@freeze_time('1999-1-3')
def test_borrow_return_save(client_logged):
    a = AccountFactory()
    b = factories.BorrowFactory()

    data = {'borrow': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-03' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert '1,1' in actual['html_list']


def test_borrow_return_save_invalid_data(client_logged):
    data = {'borrow': 'A', 'price': '0'}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_borrow_return_update_func():
    view = resolve('/borrows/return/update/1/')

    assert views.BorrowReturnUpdate == view.func.view_class


def test_borrow_return_update_200(client_logged):
    f = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_update', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                                    Lent
# ---------------------------------------------------------------------------------------
def test_lent_list_func():
    view = resolve('/lents/lists/')

    assert views.LentLists == view.func.view_class


def test_lent_list_200(client_logged):
    url = reverse('debts:lents_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_list_empty(client_logged):
    url = reverse('debts:lents_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lent_list_with_data(client_logged):
    obj = factories.LentFactory()

    url = reverse('debts:lents_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolintojas' in content
    assert 'Pasiskolinta' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-01' in content
    assert obj.name in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Lent Remark' in content


def test_lent_new_func():
    view = resolve('/lents/new/')

    assert views.LentNew == view.func.view_class


def test_lent_new_200(client_logged):
    url = reverse('debts:lents_new')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('2000-01-01')
def test_lent_load_form(client_logged):
    url = reverse('debts:lents_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


def test_lent_save(client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert '1,1' in actual['html_list']


def test_lent_save_invalid_data(client_logged):
    data = {'date': 'x', 'name': 'A', 'price': '0'}

    url = reverse('debts:lents_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_lent_update_func():
    view = resolve('/lents/update/1/')

    assert views.LentUpdate == view.func.view_class


def test_lent_update_200(client_logged):
    f = factories.LentFactory()

    url = reverse('debts:lents_update', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                             Lent Return
# ---------------------------------------------------------------------------------------
def test_lent_return_list_func():
    view = resolve('/lents/return/lists/')

    assert views.LentReturnLists == view.func.view_class


def test_lent_return_list_200(client_logged):
    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_list_empty(client_logged):
    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lent_return_list_with_data(client_logged):
    factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Kiek' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Lent Return Remark' in content


def test_lent_return_new_func():
    view = resolve('/lents/return/new/')

    assert views.LentReturnNew == view.func.view_class


def test_lent_return_new_200(client_logged):
    url = reverse('debts:lents_return_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_load_form(client_logged):
    url = reverse('debts:lents_return_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200


@freeze_time('1999-1-3')
def test_lent_return_save(client_logged):
    a = AccountFactory()
    b = factories.LentFactory()

    data = {'lent': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-03' in actual['html_list']
    assert 'Account1' in actual['html_list']
    assert '1,1' in actual['html_list']


def test_lent_return_save_invalid_data(client_logged):
    data = {'lent': 'A', 'price': '0'}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_lent_return_update_func():
    view = resolve('/lents/return/update/1/')

    assert views.LentReturnUpdate == view.func.view_class


def test_lent_return_update_200(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_update', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200
