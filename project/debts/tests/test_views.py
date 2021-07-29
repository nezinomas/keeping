import json
import re
from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from .. import factories, models, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                  Reload
# ---------------------------------------------------------------------------------------
def test_borrow_reload_func():
    view = resolve('/borrows/reload/')

    assert views.BorrowReload is view.func.view_class


def test_borrow_reload_render(rf):
    request = rf.get('/borrows/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.BorrowReload.as_view()(request)

    assert response.status_code == 200
    assert 'borrow' in response.context_data
    assert 'borrow_return' in response.context_data


def test_borrow_reload_ender_ajax_trigger_not_set(client_logged):
    url = reverse('debts:borrows_reload')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_lent_reload_func():
    view = resolve('/lents/reload/')

    assert views.LentReload is view.func.view_class


def test_lent_reload_render(rf):
    request = rf.get('/lents/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.LentReload.as_view()(request)

    assert response.status_code == 200
    assert 'lent' in response.context_data
    assert 'lent_return' in response.context_data


def test_lent_reload_ender_ajax_trigger_not_set(client_logged):
    url = reverse('debts:lents_reload')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


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
    obj = factories.BorrowFactory(closed=True)

    url = reverse('debts:borrows_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolininkas' in content
    assert 'Suma' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content
    assert 'Uždaryta' in content

    assert '1999-01-01' in content
    assert obj.name in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Borrow Remark' in content
    assert '<i class="bi bi-check-circle-fill"></i>' in content

def test_borrow_list_edit_button(client_logged):
    obj = factories.BorrowFactory()

    url = reverse('debts:borrows_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_update', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content

def test_borrow_list_delete_button(client_logged):
    obj = factories.BorrowFactory()

    url = reverse('debts:borrows_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content


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
    assert not actual.get('html_list')

    actual = models.Borrow.objects.items()[0]
    assert actual.date == date(1999, 1, 1)
    assert actual.account.title == 'Account1'
    assert actual.name == 'AAA'
    assert actual.price == Decimal('1.1')


def test_borrow_save_not_render_html_list(client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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


def test_borrow_load_update_form(client_logged):
    f = factories.BorrowFactory()
    url = reverse('debts:borrows_update', kwargs={'pk': f.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '1999-01-01' in form
    assert '100' in form
    assert 'Account1' in form
    assert 'Borrow Remark' in form


def test_borrow_update(client_logged):
    e = factories.BorrowFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }
    url = reverse('debts:borrows_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Borrow.objects.items()
    assert actual.count() == 1

    actual = actual[0]
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert actual.closed


def test_borrow_update_not_closed(client_logged):
    e = factories.BorrowFactory(name='XXX')

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': False
    }
    url = reverse('debts:borrows_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Borrow.objects.items()
    assert actual.count() == 1

    actual = actual[0]
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert not actual.closed


def test_borrow_update_not_render_html_list(client_logged):
    e = factories.BorrowFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }

    url = reverse('debts:borrows_update', kwargs={'pk': e.pk})
    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_borrow_delete_func():
    view = resolve('/borrows/delete/1/')

    assert views.BorrowDelete == view.func.view_class


def test_borrow_delete_200(client_logged):
    f = factories.BorrowFactory()

    url = reverse('debts:borrows_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_delete_load_form(client_logged):
    obj = factories.BorrowFactory()

    url = reverse('debts:borrows_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="borrow_ajax">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_borrow_delete(client_logged):
    p = factories.BorrowFactory()

    assert models.Borrow.objects.all().count() == 1
    url = reverse('debts:borrows_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Borrow.objects.all().count() == 0


def test_borrow_delete_not_render_html_list(client_logged):
    p = factories.BorrowFactory()

    assert models.Borrow.objects.all().count() == 1
    url = reverse('debts:borrows_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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
    assert 'Suma' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Borrow Return Remark' in content


def test_borrow_return_list_edit_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content

def test_borrow_return_list_delete_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_return_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content


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

    actual = models.BorrowReturn.objects.items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == 'Account1'
    assert actual.price == Decimal('1.1')


@freeze_time('1999-1-3')
def test_borrow_return_save_not_render_html_list(client_logged):
    a = AccountFactory()
    b = factories.BorrowFactory()

    data = {'borrow': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_update_form(client_logged):
    obj = factories.BorrowReturnFactory()
    url = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '5' in form
    assert 'Account1' in form
    assert 'Borrow Return Remark' in form


def test_borrow_return_update(client_logged):
    e = factories.BorrowReturnFactory()
    l = factories.BorrowFactory()
    a = AccountFactory(title='AAA')

    data = {
        'price': '5',
        'remark': 'Pastaba',
        'account': a.pk,
        'borrow': l.pk
    }
    url = reverse('debts:borrows_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.BorrowReturn.objects.get(pk=e.pk)

    assert actual.borrow == l
    assert actual.date == date(1999, 1, 2)
    assert actual.price == Decimal('5')
    assert actual.account.title == 'AAA'
    assert actual.remark == 'Pastaba'


def test_borrow_return_update_not_render_html_list(client_logged):
    e = factories.BorrowReturnFactory()
    l = factories.BorrowFactory()
    a = AccountFactory(title='AAA')

    data = {
        'price': '150',
        'remark': 'Pastaba',
        'account': a.pk,
        'borrow': l.pk
    }
    url = reverse('debts:borrows_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_borrow_return_delete_func():
    view = resolve('/borrows/return/delete/1/')

    assert views.BorrowReturnDelete == view.func.view_class


def test_borrow_return_delete_200(client_logged):
    f = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_delete_load_form(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="borrow_return_ajax">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_borrow_return_delete(client_logged):
    p = factories.BorrowReturnFactory()

    assert models.BorrowReturn.objects.all().count() == 1
    url = reverse('debts:borrows_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.BorrowReturn.objects.all().count() == 0


def test_borrow_return_delete_not_render_html_list(client_logged):
    p = factories.BorrowReturnFactory()

    assert models.BorrowReturn.objects.all().count() == 1
    url = reverse('debts:borrows_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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
    obj = factories.LentFactory(closed=True)

    url = reverse('debts:lents_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolintojas' in content
    assert 'Suma' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content
    assert 'Uždaryta' in content

    assert '1999-01-01' in content
    assert obj.name in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Lent Remark' in content
    assert '<i class="bi bi-check-circle-fill"></i>' in content


def test_lent_list_edit_button(client_logged):
    obj = factories.LentFactory()

    url = reverse('debts:lents_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_update', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


def test_lent_list_delete_button(client_logged):
    obj = factories.LentFactory()

    url = reverse('debts:lents_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


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
    assert not actual.get('html_list')

    actual = models.Lent.objects.items()[0]
    assert actual.date == date(1999, 1, 1)
    assert actual.account.title == 'Account1'
    assert actual.name == 'AAA'
    assert actual.price == Decimal('1.1')


def test_lent_save_not_render_html_list(client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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


def test_lent_load_update_form(client_logged):
    f = factories.LentFactory()
    url = reverse('debts:lents_update', kwargs={'pk': f.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '1999-01-01' in form
    assert '100' in form
    assert 'Account1' in form
    assert 'Lent Remark' in form


def test_lent_update(client_logged):
    e = factories.LentFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }
    url = reverse('debts:lents_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Lent.objects.get(pk=e.pk)
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert actual.closed


def test_lent_update_not_closed(client_logged):
    e = factories.LentFactory(name='XXX')

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': False
    }
    url = reverse('debts:lents_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Lent.objects.get(pk=e.pk)
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert not actual.closed


def test_lent_update_not_render_html_list(client_logged):
    e = factories.LentFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }

    url = reverse('debts:lents_update', kwargs={'pk': e.pk})
    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lent_delete_func():
    view = resolve('/lents/delete/1/')

    assert views.LentDelete == view.func.view_class


def test_lent_delete_200(client_logged):
    f = factories.LentFactory()

    url = reverse('debts:lents_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_delete_load_form(client_logged):
    obj = factories.LentFactory()

    url = reverse('debts:lents_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="lent_ajax">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_lent_delete(client_logged):
    p = factories.LentFactory()

    assert models.Lent.objects.all().count() == 1
    url = reverse('debts:lents_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Lent.objects.all().count() == 0


def test_lent_delete_not_render_html_list(client_logged):
    p = factories.LentFactory()

    assert models.Lent.objects.all().count() == 1
    url = reverse('debts:lents_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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
    assert 'Suma' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Lent Return Remark' in content


def test_lent_return_list_edit_button(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_return_update', kwargs={'pk': f.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


def test_lent_return_list_delete_button(client_logged):
    obj = factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


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

    actual = models.LentReturn.objects.items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == 'Account1'
    assert actual.price == Decimal('1.1')


@freeze_time('1999-1-3')
def test_lent_return_save_not_render_html_list(client_logged):
    a = AccountFactory()
    b = factories.LentFactory()

    data = {'lent': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


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


def test_lent_return_load_update_form(client_logged):
    f = factories.LentReturnFactory()
    url = reverse('debts:lents_return_update', kwargs={'pk': f.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '5' in form
    assert 'Account1' in form
    assert 'Lent Return Remark' in form


def test_lent_return_update(client_logged):
    e = factories.LentReturnFactory()
    l = factories.LentFactory()
    a = AccountFactory(title='AAA')

    data = {
        'price': '5',
        'remark': 'Pastaba',
        'account': a.pk,
        'lent': l.pk
    }
    url = reverse('debts:lents_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.LentReturn.objects.get(pk=e.pk)

    assert actual.lent == l
    assert actual.date == date(1999, 1, 2)
    assert actual.price == Decimal('5')
    assert actual.account.title == 'AAA'
    assert actual.remark == 'Pastaba'


def test_lent_return_update_not_render_html_list(client_logged):
    e = factories.LentReturnFactory()
    l = factories.LentFactory()
    a = AccountFactory(title='AAA')

    data = {
        'price': '150',
        'remark': 'Pastaba',
        'account': a.pk,
        'lent': l.pk
    }
    url = reverse('debts:lents_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lent_return_delete_func():
    view = resolve('/lents/return/delete/1/')

    assert views.LentReturnDelete == view.func.view_class


def test_lent_return_delete_200(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_delete_load_form(client_logged):
    obj = factories.LentReturnFactory()

    url = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="lent_return_ajax">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_lent_return_delete(client_logged):
    p = factories.LentReturnFactory()

    assert models.LentReturn.objects.all().count() == 1
    url = reverse('debts:lents_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.LentReturn.objects.all().count() == 0


def test_lent_return_delete_not_render_html_list(client_logged):
    p = factories.LentReturnFactory()

    assert models.LentReturn.objects.all().count() == 1
    url = reverse('debts:lents_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')
